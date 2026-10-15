from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, ListingAuditEvent, MarketplaceListing, get_db
from backend.app.main import app

client = TestClient(app)


def _client_with_database(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setenv("DOMHOSTIFY_ADMIN_API_TOKEN", "test-admin-token")
    return engine, TestSession


def _create_listing(session_factory, *, ownership_status="verified"):
    with session_factory() as session:
        listing = MarketplaceListing(
            domain="moderation-example.com",
            asking_price=500,
            currency="EUR",
            sale_type="buy_now",
            listing_status="pending_review",
            ownership_status=ownership_status,
            moderation_status="pending",
            seller_ref="seller-ref",
            active=False,
        )
        session.add(listing)
        session.commit()
        return listing.id


def test_admin_moderation_fails_closed_when_not_configured(monkeypatch):
    monkeypatch.delenv("DOMHOSTIFY_ADMIN_API_TOKEN", raising=False)
    response = client.post(
        "/api/v1/admin/marketplace/listings/1/review",
        json={"decision": "reject"},
    )
    assert response.status_code == 503


def test_admin_cannot_approve_unverified_ownership(monkeypatch):
    engine, TestSession = _client_with_database(monkeypatch)
    try:
        listing_id = _create_listing(TestSession, ownership_status="unverified")
        response = client.post(
            f"/api/v1/admin/marketplace/listings/{listing_id}/review",
            headers={"Authorization": "Bearer test-admin-token"},
            json={"decision": "approve"},
        )
        assert response.status_code == 409
        with TestSession() as session:
            listing = session.get(MarketplaceListing, listing_id)
            assert listing is not None
            assert listing.active is False
            assert listing.moderation_status == "pending"
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_admin_approval_publishes_verified_listing_and_audits(monkeypatch):
    engine, TestSession = _client_with_database(monkeypatch)
    try:
        listing_id = _create_listing(TestSession)
        response = client.post(
            f"/api/v1/admin/marketplace/listings/{listing_id}/review",
            headers={"Authorization": "Bearer test-admin-token"},
            json={"decision": "approve", "note": "Ownership independently checked"},
        )
        assert response.status_code == 200
        assert response.json()["listing_status"] == "active"
        assert response.json()["moderation_status"] == "approved"
        with TestSession() as session:
            listing = session.get(MarketplaceListing, listing_id)
            events = session.scalars(select(ListingAuditEvent)).all()
            assert listing is not None and listing.active is True
            assert [event.event_type for event in events] == ["admin_listing_approved"]
            assert events[0].actor_type == "admin"
        public = client.get("/api/v1/marketplace/persistent-listings")
        assert public.status_code == 200
        assert [item["id"] for item in public.json()] == [listing_id]
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_admin_rejection_keeps_listing_private_and_audits(monkeypatch):
    engine, TestSession = _client_with_database(monkeypatch)
    try:
        listing_id = _create_listing(TestSession)
        response = client.post(
            f"/api/v1/admin/marketplace/listings/{listing_id}/review",
            headers={"Authorization": "Bearer test-admin-token"},
            json={"decision": "reject", "note": "Insufficient evidence"},
        )
        assert response.status_code == 200
        assert response.json()["listing_status"] == "rejected"
        assert response.json()["moderation_status"] == "rejected"
        with TestSession() as session:
            listing = session.get(MarketplaceListing, listing_id)
            events = session.scalars(select(ListingAuditEvent)).all()
            assert listing is not None and listing.active is False
            assert [event.event_type for event in events] == ["admin_listing_rejected"]
        public = client.get("/api/v1/marketplace/persistent-listings")
        assert public.status_code == 200
        assert public.json() == []
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
