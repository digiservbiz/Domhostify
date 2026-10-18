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
    monkeypatch.setenv("DOMHOSTIFY_SELLER_API_TOKEN", "test-seller-token")
    return engine, TestSession


def test_seller_listing_requires_authentication(monkeypatch) -> None:
    monkeypatch.delenv("DOMHOSTIFY_SELLER_API_TOKEN", raising=False)
    response = client.post("/api/v1/marketplace/seller/listings", json={"domain": "example.com", "asking_price": 100})
    assert response.status_code == 503


def test_seller_listing_rejects_missing_or_invalid_bearer_token(monkeypatch) -> None:
    engine, _ = _client_with_database(monkeypatch)
    try:
        missing = client.post("/api/v1/marketplace/seller/listings", json={"domain": "example.com", "asking_price": 100})
        invalid = client.post("/api/v1/marketplace/seller/listings", headers={"Authorization": "Bearer wrong"}, json={"domain": "example.com", "asking_price": 100})
        assert missing.status_code == 401
        assert invalid.status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_seller_listing_enters_review_and_is_not_public(monkeypatch) -> None:
    engine, TestSession = _client_with_database(monkeypatch)
    try:
        response = client.post(
            "/api/v1/marketplace/seller/listings",
            headers={"Authorization": "Bearer test-seller-token"},
            json={"domain": "MyBrand.com", "asking_price": 1250, "currency": "eur", "sale_type": "buy_now"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["domain"] == "mybrand.com"
        assert body["listing_status"] == "pending_review"
        assert body["ownership_status"] == "unverified"
        assert body["moderation_status"] == "pending"

        with TestSession() as session:
            listing = session.get(MarketplaceListing, body["id"])
            events = session.scalars(select(ListingAuditEvent)).all()
            assert listing is not None
            assert listing.active is False
            assert listing.seller_ref is not None
            assert len(listing.seller_ref) == 32
            assert len(events) == 1
            assert events[0].event_type == "seller_listing_submitted"
            assert events[0].actor_type == "seller"
            assert events[0].actor_ref == listing.seller_ref

        public = client.get("/api/v1/marketplace/persistent-listings")
        assert public.status_code == 200
        assert public.json() == []
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_seller_inventory_requires_auth_and_returns_only_owned_listings(monkeypatch) -> None:
    engine, TestSession = _client_with_database(monkeypatch)
    try:
        unauthenticated = client.get("/api/v1/marketplace/seller/listings")
        assert unauthenticated.status_code == 401

        created = client.post(
            "/api/v1/marketplace/seller/listings",
            headers={"Authorization": "Bearer test-seller-token"},
            json={"domain": "owned-example.com", "asking_price": 99},
        )
        assert created.status_code == 201

        with TestSession() as session:
            session.add(MarketplaceListing(
                domain="other-seller.com",
                asking_price=500,
                seller_ref="different-seller-reference",
                listing_status="pending_review",
                ownership_status="unverified",
                moderation_status="pending",
                active=False,
            ))
            session.commit()

        response = client.get(
            "/api/v1/marketplace/seller/listings",
            headers={"Authorization": "Bearer test-seller-token"},
        )
        assert response.status_code == 200
        body = response.json()
        assert [item["domain"] for item in body] == ["owned-example.com"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
