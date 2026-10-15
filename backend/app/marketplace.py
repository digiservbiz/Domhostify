"""Security-sensitive marketplace lifecycle helpers.

These helpers intentionally do not expose seller write endpoints yet. Authentication,
authorization, and registrar/DNS integrations must be added before public writes.
"""
import hashlib
import secrets
from datetime import timedelta

from sqlalchemy.orm import Session

from backend.app.database import ListingAuditEvent, OwnershipChallenge, utc_now


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_ownership_challenge(
    db: Session,
    *,
    listing_id: int,
    domain: str,
    ttl_minutes: int = 30,
) -> tuple[OwnershipChallenge, str]:
    """Create a DNS TXT challenge and return the one-time token to the caller.

    Only the SHA-256 hash is persisted. The raw token must never be logged or stored.
    This function is not exposed as an unauthenticated API route.
    """
    if not 5 <= ttl_minutes <= 1440:
        raise ValueError("Challenge TTL must be between 5 minutes and 24 hours.")
    token = secrets.token_urlsafe(32)
    challenge = OwnershipChallenge(
        listing_id=listing_id,
        method="dns_txt",
        challenge_label=f"_domhostify-verification.{domain.lower().rstrip('.')}",
        token_hash=_hash_token(token),
        status="pending",
        expires_at=utc_now() + timedelta(minutes=ttl_minutes),
    )
    db.add(challenge)
    return challenge, token


def add_listing_audit_event(
    db: Session,
    *,
    listing_id: int,
    event_type: str,
    actor_type: str = "system",
    actor_ref: str | None = None,
    event_note: str | None = None,
) -> ListingAuditEvent:
    """Append a bounded audit event without collecting request fingerprint data."""
    if not event_type or len(event_type) > 60:
        raise ValueError("Invalid audit event type.")
    if actor_type not in {"system", "seller", "admin", "provider"}:
        raise ValueError("Invalid audit actor type.")
    if event_note is not None and len(event_note) > 500:
        raise ValueError("Audit note is too long.")
    event = ListingAuditEvent(
        listing_id=listing_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_ref=actor_ref,
        event_note=event_note,
    )
    db.add(event)
    return event
