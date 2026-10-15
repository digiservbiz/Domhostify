"""Authenticated bootstrap API for Make Offer and temporary Buy Now intents.

Buy Now reservations only hold a listing briefly; they do not collect payments or
perform transfers. Buyer/seller tokens are single-identity bootstrap credentials.
"""
import hashlib
import hmac
import os
from datetime import timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from backend.app.database import (
    MarketplaceListing,
    MarketplaceTransaction,
    MarketplaceTransactionEvent,
    get_db,
    utc_now,
)
from backend.app.transactions import transition_transaction

router = APIRouter(tags=["transactions"])


def _is_future(value, now) -> bool:
    if value is None:
        return False
    # SQLite may return naive datetimes despite timezone=True; normalize as UTC.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value > now


def _token_ref(env_key: str, authorization: str | None, role: str) -> str:
    configured = os.getenv(env_key, "").strip()
    if not configured:
        raise HTTPException(status_code=503, detail=f"{role.capitalize()} authentication is not configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer authentication required.")
    supplied = authorization[7:].strip()
    if not supplied or not hmac.compare_digest(supplied, configured):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    return hashlib.sha256(supplied.encode("utf-8")).hexdigest()[:32]


def _require_buyer_auth(authorization: str | None = Header(default=None)) -> str:
    return _token_ref("DOMHOSTIFY_BUYER_API_TOKEN", authorization, "buyer")


def _require_seller_auth(authorization: str | None = Header(default=None)) -> str:
    return _token_ref("DOMHOSTIFY_SELLER_API_TOKEN", authorization, "seller")


def _require_admin_auth(authorization: str | None = Header(default=None)) -> str:
    return _token_ref("DOMHOSTIFY_ADMIN_API_TOKEN", authorization, "admin")


class OfferCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class OfferDecision(BaseModel):
    decision: str = Field(min_length=1, max_length=20)
    note: str | None = Field(default=None, max_length=500)


def _offer_payload(transaction: MarketplaceTransaction, domain: str) -> dict:
    return {
        "id": transaction.id,
        "listing_id": transaction.listing_id,
        "domain": domain,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "transaction_type": transaction.transaction_type,
        "status": transaction.status,
        "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
        "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None,
    }


@router.post("/api/v1/marketplace/listings/{listing_id}/offers", status_code=201)
def create_offer(
    listing_id: int,
    payload: OfferCreate,
    buyer_ref: str = Depends(_require_buyer_auth),
    db: Session = Depends(get_db),
) -> dict:
    """Create a make-offer request for a currently public listing."""
    try:
        listing = db.scalar(select(MarketplaceListing).where(
            MarketplaceListing.id == listing_id,
            MarketplaceListing.active.is_(True),
            MarketplaceListing.listing_status == "active",
            MarketplaceListing.ownership_status == "verified",
            MarketplaceListing.moderation_status == "approved",
        ))
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        if not listing.seller_ref:
            raise HTTPException(status_code=409, detail="Listing seller identity is unavailable.")
        if hmac.compare_digest(buyer_ref, listing.seller_ref):
            raise HTTPException(status_code=409, detail="Sellers cannot make offers on their own listings.")
        transaction = MarketplaceTransaction(
            listing_id=listing.id,
            buyer_ref=buyer_ref,
            seller_ref=listing.seller_ref,
            transaction_type="make_offer",
            amount=payload.amount,
            currency=listing.currency,
            status="offer_pending",
        )
        db.add(transaction)
        db.flush()
        db.add(MarketplaceTransactionEvent(
            transaction_id=transaction.id,
            event_type="transaction_offer_pending",
            from_status=None,
            to_status="offer_pending",
            actor_type="buyer",
            actor_ref=buyer_ref,
            event_note="Buyer submitted a make-offer request",
        ))
        db.commit()
        db.refresh(transaction)
        return _offer_payload(transaction, listing.domain)
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc


@router.post("/api/v1/admin/marketplace/reservations/expire")
def expire_buy_now_reservations(
    admin_ref: str = Depends(_require_admin_auth),
    db: Session = Depends(get_db),
) -> dict:
    """Expire stale reservations and append cancellation events; suitable for a scheduled job."""
    now = utc_now()
    listings = db.scalars(select(MarketplaceListing).where(
        MarketplaceListing.reservation_transaction_id.is_not(None),
        MarketplaceListing.reserved_until <= now,
    )).all()
    expired = 0
    for listing in listings:
        transaction_id = listing.reservation_transaction_id
        transaction = db.get(MarketplaceTransaction, transaction_id)
        if transaction is not None and transaction.transaction_type == "buy_now" and transaction.status == "buy_now_pending":
            transition_transaction(
                db,
                transaction=transaction,
                target_status="cancelled",
                actor_type="admin",
                actor_ref=admin_ref,
                note="Buy Now reservation expired before payment started",
            )
        db.execute(update(MarketplaceListing).where(
            MarketplaceListing.id == listing.id,
            MarketplaceListing.reservation_transaction_id == transaction_id,
        ).execution_options(synchronize_session=False).values(
            reservation_transaction_id=None,
            reserved_until=None,
            updated_at=now,
        ))
        expired += 1
    db.commit()
    return {"expired_reservations": expired}


@router.post("/api/v1/marketplace/listings/{listing_id}/buy-now", status_code=201)
def create_buy_now_intent(
    listing_id: int,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    buyer_ref: str = Depends(_require_buyer_auth),
    db: Session = Depends(get_db),
) -> dict:
    """Create a ten-minute reservation intent; no payment is collected."""
    now = utc_now()
    if not idempotency_key or not idempotency_key.strip() or len(idempotency_key) > 128:
        raise HTTPException(status_code=400, detail="A non-empty Idempotency-Key header (max 128 characters) is required.")

    existing = db.scalar(select(MarketplaceTransaction).where(
        MarketplaceTransaction.buyer_ref == buyer_ref,
        MarketplaceTransaction.idempotency_key == idempotency_key,
    ))
    if existing is not None:
        if existing.listing_id != listing_id or existing.transaction_type != "buy_now":
            raise HTTPException(status_code=409, detail="Idempotency key was already used for a different request.")
        listing = db.get(MarketplaceListing, listing_id)
        if (
            existing.status == "buy_now_pending"
            and existing.expires_at is not None
            and _is_future(existing.expires_at, now)
            and listing is not None
            and listing.reservation_transaction_id == existing.id
        ):
            return {
                **_offer_payload(existing, listing.domain),
                "reservation_expires_at": existing.expires_at.isoformat(),
                "payment_status": "not_started",
                "message": "Existing reservation returned. No payment has been taken.",
            }
        raise HTTPException(status_code=409, detail="This idempotency key belongs to an expired or closed reservation. Use a new key.")

    expires_at = now + timedelta(minutes=10)
    try:
        listing = db.scalar(select(MarketplaceListing).where(
            MarketplaceListing.id == listing_id,
            MarketplaceListing.active.is_(True),
            MarketplaceListing.listing_status == "active",
            MarketplaceListing.ownership_status == "verified",
            MarketplaceListing.moderation_status == "approved",
            MarketplaceListing.sale_type == "buy_now",
        ))
        if listing is None:
            raise HTTPException(status_code=404, detail="Buy Now listing not found.")
        if not listing.seller_ref:
            raise HTTPException(status_code=409, detail="Listing seller identity is unavailable.")
        if hmac.compare_digest(buyer_ref, listing.seller_ref):
            raise HTTPException(status_code=409, detail="Sellers cannot purchase their own listings.")

        transaction = MarketplaceTransaction(
            listing_id=listing.id,
            buyer_ref=buyer_ref,
            seller_ref=listing.seller_ref,
            transaction_type="buy_now",
            idempotency_key=idempotency_key,
            amount=Decimal(str(listing.asking_price)).quantize(Decimal("0.01")),
            currency=listing.currency,
            status="buy_now_pending",
            expires_at=expires_at,
        )
        db.add(transaction)
        db.flush()

        # Conditional UPDATE is the atomic gate: one buyer can reserve an
        # available listing, or replace a reservation that has expired.
        reserved = db.execute(update(MarketplaceListing).where(
            MarketplaceListing.id == listing.id,
            MarketplaceListing.active.is_(True),
            MarketplaceListing.listing_status == "active",
            MarketplaceListing.ownership_status == "verified",
            MarketplaceListing.moderation_status == "approved",
            MarketplaceListing.sale_type == "buy_now",
            or_(
                MarketplaceListing.reserved_until.is_(None),
                MarketplaceListing.reserved_until <= now,
            ),
        ).execution_options(synchronize_session=False).values(
            reservation_transaction_id=transaction.id,
            reserved_until=expires_at,
            updated_at=now,
        ))
        if reserved.rowcount != 1:
            db.rollback()
            raise HTTPException(status_code=409, detail="This domain is already reserved for checkout.")
        db.add(MarketplaceTransactionEvent(
            transaction_id=transaction.id,
            event_type="transaction_buy_now_pending",
            from_status=None,
            to_status="buy_now_pending",
            actor_type="buyer",
            actor_ref=buyer_ref,
            event_note="Temporary Buy Now reservation created; payment not collected",
        ))
        db.commit()
        db.refresh(transaction)
        return {
            **_offer_payload(transaction, listing.domain),
            "reservation_expires_at": expires_at.isoformat(),
            "payment_status": "not_started",
            "message": "Reservation created. No payment has been taken.",
        }
    except IntegrityError as exc:
        db.rollback()
        # A simultaneous retry with the same key may have committed first.
        existing = db.scalar(select(MarketplaceTransaction).where(
            MarketplaceTransaction.buyer_ref == buyer_ref,
            MarketplaceTransaction.idempotency_key == idempotency_key,
        ))
        if existing is not None and existing.listing_id == listing_id:
            listing = db.get(MarketplaceListing, listing_id)
            if listing is not None and listing.reservation_transaction_id == existing.id:
                return {
                    **_offer_payload(existing, listing.domain),
                    "reservation_expires_at": existing.expires_at.isoformat() if existing.expires_at else None,
                    "payment_status": "not_started",
                    "message": "Existing reservation returned. No payment has been taken.",
                }
        raise HTTPException(status_code=409, detail="Idempotency key conflict; retry with the original request or a new key.") from exc
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc


@router.get("/api/v1/marketplace/buyer/offers")
def list_buyer_offers(
    buyer_ref: str = Depends(_require_buyer_auth),
    db: Session = Depends(get_db),
) -> list[dict]:
    try:
        rows = db.execute(
            select(MarketplaceTransaction, MarketplaceListing.domain)
            .join(MarketplaceListing, MarketplaceListing.id == MarketplaceTransaction.listing_id)
            .where(MarketplaceTransaction.buyer_ref == buyer_ref)
            .order_by(MarketplaceTransaction.created_at.desc())
            .limit(100)
        ).all()
        return [_offer_payload(transaction, domain) for transaction, domain in rows]
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc


@router.get("/api/v1/marketplace/seller/listings/{listing_id}/offers")
def list_seller_offers(
    listing_id: int,
    seller_ref: str = Depends(_require_seller_auth),
    db: Session = Depends(get_db),
) -> list[dict]:
    try:
        listing = db.scalar(select(MarketplaceListing).where(
            MarketplaceListing.id == listing_id,
            MarketplaceListing.seller_ref == seller_ref,
        ))
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        rows = db.scalars(select(MarketplaceTransaction).where(
            MarketplaceTransaction.listing_id == listing_id,
            MarketplaceTransaction.seller_ref == seller_ref,
        ).order_by(MarketplaceTransaction.created_at.desc()).limit(100)).all()
        return [_offer_payload(row, listing.domain) for row in rows]
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc


@router.post("/api/v1/marketplace/seller/offers/{transaction_id}/decision")
def decide_offer(
    transaction_id: int,
    payload: OfferDecision,
    seller_ref: str = Depends(_require_seller_auth),
    db: Session = Depends(get_db),
) -> dict:
    decision = payload.decision.strip().lower()
    if decision not in {"accept", "reject"}:
        raise HTTPException(status_code=422, detail="Decision must be accept or reject.")
    target = "accepted" if decision == "accept" else "rejected"
    try:
        transaction = db.scalar(select(MarketplaceTransaction).where(
            MarketplaceTransaction.id == transaction_id,
            MarketplaceTransaction.seller_ref == seller_ref,
        ))
        if transaction is None:
            raise HTTPException(status_code=404, detail="Offer not found.")
        listing = db.get(MarketplaceListing, transaction.listing_id)
        if listing is None or listing.seller_ref != seller_ref:
            raise HTTPException(status_code=404, detail="Offer not found.")
        try:
            transition_transaction(
                db,
                transaction=transaction,
                target_status=target,
                actor_type="seller",
                actor_ref=seller_ref,
                note=payload.note.strip() if payload.note else None,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        db.commit()
        db.refresh(transaction)
        return _offer_payload(transaction, listing.domain)
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc


@router.post("/api/v1/marketplace/buyer/offers/{transaction_id}/cancel")
def cancel_buyer_offer(
    transaction_id: int,
    buyer_ref: str = Depends(_require_buyer_auth),
    db: Session = Depends(get_db),
) -> dict:
    try:
        transaction = db.scalar(select(MarketplaceTransaction).where(
            MarketplaceTransaction.id == transaction_id,
            MarketplaceTransaction.buyer_ref == buyer_ref,
        ))
        if transaction is None:
            raise HTTPException(status_code=404, detail="Offer not found.")
        listing = db.get(MarketplaceListing, transaction.listing_id)
        if listing is None:
            raise HTTPException(status_code=404, detail="Offer not found.")
        try:
            transition_transaction(
                db,
                transaction=transaction,
                target_status="cancelled",
                actor_type="buyer",
                actor_ref=buyer_ref,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if transaction.transaction_type == "buy_now":
            db.execute(update(MarketplaceListing).where(
                MarketplaceListing.id == transaction.listing_id,
                MarketplaceListing.reservation_transaction_id == transaction.id,
            ).execution_options(synchronize_session=False).values(
                reservation_transaction_id=None,
                reserved_until=None,
                updated_at=utc_now(),
            ))
        db.commit()
        db.refresh(transaction)
        return _offer_payload(transaction, listing.domain)
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
