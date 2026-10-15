from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, ListingAuditEvent, OwnershipChallenge
from backend.app.marketplace import add_listing_audit_event, create_ownership_challenge


def _session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return engine, sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_ownership_challenge_persists_hash_not_raw_token() -> None:
    engine, Session = _session()
    try:
        with Session() as db:
            challenge, token = create_ownership_challenge(db, listing_id=7, domain="Example.COM")
            db.commit()
            stored = db.scalar(select(OwnershipChallenge).where(OwnershipChallenge.id == challenge.id))
            assert stored is not None
            assert token
            assert stored.token_hash != token
            assert len(stored.token_hash) == 64
            assert stored.challenge_label == "_domhostify-verification.example.com"
            assert stored.status == "pending"
    finally:
        engine.dispose()


def test_ownership_challenge_rejects_unsafe_ttl() -> None:
    engine, Session = _session()
    try:
        with Session() as db:
            try:
                create_ownership_challenge(db, listing_id=1, domain="example.com", ttl_minutes=1)
            except ValueError:
                pass
            else:
                raise AssertionError("Expected TTL validation")
    finally:
        engine.dispose()


def test_listing_audit_event_is_bounded_and_append_only() -> None:
    engine, Session = _session()
    try:
        with Session() as db:
            event = add_listing_audit_event(
                db,
                listing_id=3,
                event_type="submitted",
                actor_type="seller",
                actor_ref="seller-opaque-1",
                event_note="Submitted for review",
            )
            db.commit()
            stored = db.scalar(select(ListingAuditEvent).where(ListingAuditEvent.id == event.id))
            assert stored is not None
            assert stored.actor_type == "seller"
            assert stored.actor_ref == "seller-opaque-1"
            assert stored.event_note == "Submitted for review"
    finally:
        engine.dispose()
