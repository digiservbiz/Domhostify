"""Authenticated seller endpoints for DNS TXT domain ownership verification.

The raw challenge token is returned only when a challenge is created. Verification
uses bounded DNS resolution and never logs TXT contents. Ownership verification
does not publish a listing; admin moderation remains a separate step.
"""
import hashlib
import hmac
import os
from datetime import timezone

import dns.exception
import dns.resolver
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.app.database import (
    ListingAuditEvent,
    MarketplaceListing,
    OwnershipChallenge,
    get_db,
    utc_now,
)
from backend.app.marketplace import add_listing_audit_event, create_ownership_challenge
from backend.app.ownership import verify_listing_ownership

router = APIRouter(tags=["ownership"])


def _seller_ref(authorization: str | None = Header(default=None)) -> str:
    """Use the same single-seller bootstrap token boundary as marketplace routes."""
    configured = os.getenv("DOMHOSTIFY_SELLER_API_TOKEN", "").strip()
    if not configured:
        raise HTTPException(status_code=503, detail="Seller authentication is not configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer authentication required.")
    supplied = authorization[7:].strip()
    if not supplied or not hmac.compare_digest(supplied, configured):
        raise HTTPException(status_code=401, detail="Invalid seller credentials.")
    return hashlib.sha256(supplied.encode("utf-8")).hexdigest()[:32]


@router.post("/api/v1/marketplace/seller/listings/{listing_id}/ownership-challenge", status_code=201)
def create_listing_ownership_challenge(
    listing_id: int,
    seller_ref: str = Depends(_seller_ref),
    db: Session = Depends(get_db),
) -> dict:
    """Create a short-lived DNS TXT challenge for the authenticated seller's listing."""
    try:
        listing = db.scalar(
            select(MarketplaceListing).where(
                MarketplaceListing.id == listing_id,
                MarketplaceListing.seller_ref == seller_ref,
            )
        )
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        if listing.ownership_status == "verified":
            raise HTTPException(status_code=409, detail="Listing ownership is already verified.")

        now = utc_now()
        previous = db.scalars(
            select(OwnershipChallenge).where(
                OwnershipChallenge.listing_id == listing.id,
                OwnershipChallenge.status == "pending",
            )
        ).all()
        for challenge in previous:
            challenge.status = "superseded"

        challenge, token = create_ownership_challenge(
            db, listing_id=listing.id, domain=listing.domain, ttl_minutes=30
        )
        add_listing_audit_event(
            db,
            listing_id=listing.id,
            event_type="ownership_challenge_created",
            actor_type="seller",
            actor_ref=seller_ref,
            event_note="DNS TXT challenge issued; expires in 30 minutes",
        )
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
    seller_ref: str = Depends(_seller_ref),
    db: Session = Depends(get_db),
) -> dict:
    """Resolve the expected TXT record and consume a matching, unexpired challenge."""
    try:
        listing = db.scalar(
            select(MarketplaceListing).where(
                MarketplaceListing.id == listing_id,
                MarketplaceListing.seller_ref == seller_ref,
            )
        )
        if listing is None:
            raise HTTPException(status_code=404, detail="Marketplace listing not found.")
        if listing.ownership_status == "verified":
            return {
                "listing_id": listing.id,
                "ownership_status": "verified",
                "moderation_status": listing.moderation_status,
                "message": "Ownership is already verified; the listing still requires admin moderation.",
            }

        challenge = db.scalar(
            select(OwnershipChallenge)
            .where(
                OwnershipChallenge.listing_id == listing.id,
                OwnershipChallenge.method == "dns_txt",
                OwnershipChallenge.status == "pending",
            )
            .order_by(OwnershipChallenge.created_at.desc())
        )
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
            answer = dns.resolver.resolve(
                challenge.challenge_label,
                "TXT",
                lifetime=4.0,
                raise_on_no_answer=False,
            )
            txt_values = []
            if answer.rrset is not None:
                for record in answer:
                    txt_values.append(b"".join(record.strings).decode("utf-8", errors="replace"))
        except (dns.exception.DNSException, OSError):
            txt_values = []

        verified = verify_listing_ownership(
            db,
            listing=listing,
            challenge=challenge,
            txt_values=txt_values,
            actor_ref=seller_ref,
        )
        if not verified:
            db.commit()
            raise HTTPException(status_code=422, detail="The expected TXT value was not found. Check DNS propagation and try again before expiry.")

        db.commit()
        return {
            "listing_id": listing.id,
            "ownership_status": "verified",
            "moderation_status": listing.moderation_status,
            "message": "Domain ownership verified. The listing remains unpublished until admin moderation.",
        }
    except OperationalError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Marketplace database is not initialized. Apply database migrations first.") from exc
