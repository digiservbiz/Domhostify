"""Authenticated seller and admin marketplace ownership endpoints.

The raw challenge token is returned only when a challenge is created. Verification
uses bounded DNS resolution and never logs TXT contents. Ownership verification
does not publish a listing; admin moderation remains a separate step.
"""
from datetime import timezone

import dns.exception
import dns.resolver
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.app.auth import require_admin_ref, require_seller_ref
from backend.app.database import ListingAuditEvent, MarketplaceListing, OwnershipChallenge, get_db, utc_now
from backend.app.marketplace import add_listing_audit_event, create_ownership_challenge
from backend.app.ownership import verify_listing_ownership

router = APIRouter(tags=["ownership"])


def _listing_payload(listing: MarketplaceListing) -> dict:
    return {
        "id": listing.id,
        "domain": listing.domain,
        "asking_price": listing.asking_price,
        "currency": listing.currency,
        "sale_type": listing.sale_type,
        "listing_status": listing.listing_status,
        "ownership_status": listing.ownership_status,
        "moderation_status": listing.moderation_status,
        "seller_ref": listing.seller_ref,
        "active": listing.active,
        "created_at": listing.created_at.isoformat() if listing.created_at else None,
        "updated_at": listing.updated_at.isoformat() if listing.updated_at else None,
    }


@router.post("/api/v1/marketplace/seller/listings/{listing_id}/ownership-challenge", status_code=201)
def create_listing_ownership_challenge(
    listing_id: int,
    seller_ref: str = Depends(require_seller_ref),
    db: Session = Depends(get_db),
) -> dict:
    """Create a short-lived DNS TXT challenge for the authenticated seller's listing."""
    try:
        listing = db.scalar(select(MarketplaceListing).where(MarketplaceListing.id == listing_id, MarketplaceListing.seller_ref == seller_ref))
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        if listing.ownership_status == "verified":
            raise HTTPException(status_code=409, detail="Listing ownership is already verified.")
        previous = db.scalars(select(OwnershipChallenge).where(OwnershipChallenge.listing_id == listing.id, OwnershipChallenge.status == "pending")).all()
        for challenge in previous:
            challenge.status = "superseded"
        challenge, token = create_ownership_challenge(db, listing_id=listing.id, domain=listing.domain, ttl_minutes=30)
        add_listing_audit_event(db, listing_id=listing.id, event_type="ownership_challenge_created", actor_type="seller", actor_ref=seller_ref, event_note="DNS TXT challenge issued; expires in 30 minutes")
        db.commit()
        db.refresh(challenge)
        return {
            "listing_id": listing.id,
            "domain": listing.domain,
            "method": "dns_txt",
            "record_name": challenge.challenge_label,
            "record_type": "TXT",
            "record_value": token,
            "expires_at": challenge.expires_at.isoformat(),
            "instructions": "Create this TXT record in the domain's authoritative DNS. Submit verification before it expires. The token is shown only once.",
            "listing_remains_unpublished": True,
        }
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc


@router.post("/api/v1/marketplace/seller/listings/{listing_id}/verify-ownership")
def verify_listing_ownership_dns(
    listing_id: int,
    seller_ref: str = Depends(require_seller_ref),
    db: Session = Depends(get_db),
) -> dict:
    """Resolve the expected TXT record and consume a matching, unexpired challenge."""
    try:
        listing = db.scalar(select(MarketplaceListing).where(MarketplaceListing.id == listing_id, MarketplaceListing.seller_ref == seller_ref))
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        if listing.ownership_status == "verified":
            return {"listing_id": listing.id, "ownership_status": "verified", "moderation_status": listing.moderation_status, "message": "Ownership is already verified; the listing still requires admin moderation."}
        challenge = db.scalar(select(OwnershipChallenge).where(OwnershipChallenge.listing_id == listing.id, OwnershipChallenge.method == "dns_txt", OwnershipChallenge.status == "pending").order_by(OwnershipChallenge.created_at.desc()))
        if challenge is None:
            raise HTTPException(status_code=409, detail="No pending ownership challenge. Create a new challenge first.")
        expires_at = challenge.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= utc_now():
            challenge.status = "expired"
            db.commit()
            raise HTTPException(status_code=410, detail="Ownership challenge expired. Create a new challenge.")
        try:
            answer = dns.resolver.resolve(challenge.challenge_label, "TXT", lifetime=4.0, raise_on_no_answer=False)
            txt_values = []
            if answer.rrset is not None:
                for record in answer:
                    txt_values.append(b"".join(record.strings).decode("utf-8", errors="replace"))
        except (dns.exception.DNSException, OSError):
            txt_values = []
        verified = verify_listing_ownership(db, listing=listing, challenge=challenge, txt_values=txt_values, actor_ref=seller_ref)
        if not verified:
            db.commit()
            raise HTTPException(status_code=422, detail="The expected TXT value was not found. Check DNS propagation and try again before expiry.")
        db.commit()
        return {"listing_id": listing.id, "ownership_status": "verified", "moderation_status": listing.moderation_status, "message": "Domain ownership verified. The listing remains unpublished until admin moderation."}
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc


@router.get("/api/v1/admin/marketplace/listings")
def list_admin_marketplace_listings(
    status: str | None = Query(default=None, max_length=30),
    admin_ref: str = Depends(require_admin_ref),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return the moderation queue to authenticated admins; never expose it publicly."""
    del admin_ref
    statement = select(MarketplaceListing).order_by(MarketplaceListing.created_at.desc()).limit(200)
    if status and status.strip():
        statement = statement.where(MarketplaceListing.listing_status == status.strip().lower())
    try:
        records = db.scalars(statement).all()
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
    return [_listing_payload(record) for record in records]


@router.get("/api/v1/admin/marketplace/listings/{listing_id}/audit")
def get_admin_listing_audit(
    listing_id: int,
    admin_ref: str = Depends(require_admin_ref),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return append-only moderation/ownership audit history for an admin."""
    del admin_ref
    try:
        listing = db.get(MarketplaceListing, listing_id)
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        events = db.scalars(select(ListingAuditEvent).where(ListingAuditEvent.listing_id == listing_id).order_by(ListingAuditEvent.created_at.asc()).limit(200)).all()
    except OperationalError as exc:
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
    return [
        {
            "id": event.id,
            "listing_id": event.listing_id,
            "event_type": event.event_type,
            "actor_type": event.actor_type,
            "actor_ref": event.actor_ref,
            "event_note": event.event_note,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        for event in events
    ]
