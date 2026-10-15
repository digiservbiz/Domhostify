from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.database import Base, ListingAuditEvent, MarketplaceListing, get_db
from backend.app.main import app

client = TestClient(app)
TOKEN = "seller-management-test-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def _setup(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setenv("DOMHOSTIFY_SELLER_API_TOKEN", TOKEN)
    return engine, Session


def _cleanup(engine):
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _create_listing():
    response = client.post(
        "/api/v1/marketplace/seller/listings",
        headers=HEADERS,
        json={"domain": "manage-example.com", "asking_price": 150},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_seller_edit_requires_remoderation_and_preserves_ownership(monkeypatch):
    engine, Session = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        with Session() as db:
            listing = db.get(MarketplaceListing, listing_id)
            listing.ownership_status = "verified"
            listing.moderation_status = "approved"
            listing.listing_status = "active"
            listing.active = True
            db.commit()

        response = client.patch(
            f"/api/v1/marketplace/seller/listings/{listing_id}",
            headers=HEADERS,
            json={"asking_price": 225, "currency": "usd"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asking_price"] == 225
        assert data["currency"] == "USD"
        assert data["ownership_status"] == "verified"
        assert data["active"] if "active" in data else data["listing_status"] == "pending_review"
        assert data["listing_status"] == "pending_review"
        assert data["moderation_status"] == "pending"

        with Session() as db:
            listing = db.get(MarketplaceListing, listing_id)
            events = db.scalars(select(ListingAuditEvent).where(ListingAuditEvent.listing_id == listing_id)).all()
            assert listing.active is False
            assert any(event.event_type == "seller_listing_updated" for event in events)
    finally:
        _cleanup(engine)


def test_seller_withdrawal_is_soft_and_idempotent(monkeypatch):
    engine, Session = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        response = client.delete(f"/api/v1/marketplace/seller/listings/{listing_id}", headers=HEADERS)
        assert response.status_code == 200
        assert response.json()["listing_status"] == "withdrawn"
        second = client.delete(f"/api/v1/marketplace/seller/listings/{listing_id}", headers=HEADERS)
        assert second.status_code == 200
        with Session() as db:
            listing = db.get(MarketplaceListing, listing_id)
            events = db.scalars(select(ListingAuditEvent).where(ListingAuditEvent.listing_id == listing_id)).all()
            assert listing is not None
            assert listing.active is False
            assert any(event.event_type == "seller_listing_withdrawn" for event in events)
    finally:
        _cleanup(engine)


def test_seller_cannot_edit_another_sellers_listing(monkeypatch):
    engine, _ = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        monkeypatch.setenv("DOMHOSTIFY_SELLER_API_TOKEN", "other-seller-token")
        response = client.patch(
            f"/api/v1/marketplace/seller/listings/{listing_id}",
            headers={"Authorization": "Bearer other-seller-token"},
            json={"asking_price": 1},
        )
        assert response.status_code == 404
    finally:
        _cleanup(engine)
