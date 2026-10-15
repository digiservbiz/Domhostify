from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from backend.app.database import Base, ListingAuditEvent, MarketplaceListing, OwnershipChallenge, get_db, utc_now
from backend.app.main import app

client = TestClient(app)


def _setup(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setenv("DOMHOSTIFY_SELLER_API_TOKEN", "ownership-test-token")
    return engine, TestSession


def _create_listing():
    response = client.post(
        "/api/v1/marketplace/seller/listings",
        headers={"Authorization": "Bearer ownership-test-token"},
        json={"domain": "verify-example.com", "asking_price": 150},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _cleanup(engine):
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_dns_ownership_challenge_and_verification(monkeypatch):
    engine, TestSession = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        headers = {"Authorization": "Bearer ownership-test-token"}
        challenge_response = client.post(
            f"/api/v1/marketplace/seller/listings/{listing_id}/ownership-challenge",
            headers=headers,
        )
        assert challenge_response.status_code == 201
        challenge_data = challenge_response.json()
        assert challenge_data["record_type"] == "TXT"
        assert challenge_data["record_name"] == "_domhostify-verification.verify-example.com"
        assert challenge_data["record_value"]
        assert challenge_data["listing_remains_unpublished"] is True

        class FakeTXT:
            strings = (challenge_data["record_value"].encode("utf-8"),)

        class FakeAnswer:
            rrset = True

            def __iter__(self):
                return iter([FakeTXT()])

        monkeypatch.setattr(
            "backend.app.ownership_api.dns.resolver.resolve",
            lambda *args, **kwargs: FakeAnswer(),
        )
        verify_response = client.post(
            f"/api/v1/marketplace/seller/listings/{listing_id}/verify-ownership",
            headers=headers,
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["ownership_status"] == "verified"
        assert verify_response.json()["moderation_status"] == "pending"

        with TestSession() as session:
            listing = session.get(MarketplaceListing, listing_id)
            challenge = session.scalar(select(OwnershipChallenge).where(OwnershipChallenge.listing_id == listing_id))
            events = session.scalars(select(ListingAuditEvent).where(ListingAuditEvent.listing_id == listing_id)).all()
            assert listing is not None and listing.ownership_status == "verified"
            assert listing.active is False
            assert challenge is not None and challenge.status == "verified"
            assert any(event.event_type == "domain_ownership_verified" for event in events)

        replay = client.post(
            f"/api/v1/marketplace/seller/listings/{listing_id}/verify-ownership",
            headers=headers,
        )
        assert replay.status_code == 200
        assert replay.json()["ownership_status"] == "verified"
    finally:
        _cleanup(engine)


def test_ownership_challenge_isolated_to_authenticated_seller(monkeypatch):
    engine, _ = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        monkeypatch.setenv("DOMHOSTIFY_SELLER_API_TOKEN", "different-seller-token")
        response = client.post(
            f"/api/v1/marketplace/seller/listings/{listing_id}/ownership-challenge",
            headers={"Authorization": "Bearer different-seller-token"},
        )
        assert response.status_code == 404
    finally:
        _cleanup(engine)


def test_expired_ownership_challenge_is_rejected(monkeypatch):
    engine, TestSession = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        headers = {"Authorization": "Bearer ownership-test-token"}
        challenge_response = client.post(
            f"/api/v1/marketplace/seller/listings/{listing_id}/ownership-challenge",
            headers=headers,
        )
        assert challenge_response.status_code == 201
        with TestSession() as session:
            challenge = session.scalar(select(OwnershipChallenge).where(OwnershipChallenge.listing_id == listing_id))
            assert challenge is not None
            challenge.expires_at = utc_now() - timedelta(minutes=1)
            session.commit()
        response = client.post(
            f"/api/v1/marketplace/seller/listings/{listing_id}/verify-ownership",
            headers=headers,
        )
        assert response.status_code == 410
    finally:
        _cleanup(engine)
