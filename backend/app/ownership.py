"""Domain ownership verification helpers."""
import hashlib
import hmac
from datetime import timezone

from sqlalchemy.orm import Session

from backend.app.database import ListingAuditEvent, MarketplaceListing, OwnershipChallenge, utc_now


def verify_listing_ownership(
    db: Session,
    *,
    listing: MarketplaceListing,
    challenge: OwnershipChallenge,
    txt_values: list[str],
    actor_ref: str,
) -> bool:
    """Consume one valid, unexpired DNS challenge and audit successful verification."""
    if challenge.listing_id != listing.id or challenge.method != "dns_txt" or challenge.status != "pending":
        return False
    now = utc_now()
    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        challenge.status = "expired"
        return False
    if not any(hmac.compare_digest(hashlib.sha256(value.encode("utf-8")).hexdigest(), challenge.token_hash) for value in txt_values):
        return False
    challenge.status = "verified"
    challenge.verified_at = now
    listing.ownership_status = "verified"
    db.add(ListingAuditEvent(
        listing_id=listing.id,
        event_type="domain_ownership_verified",
        actor_type="seller",
        actor_ref=actor_ref,
        event_note="DNS TXT challenge verified",
    ))
    return True
