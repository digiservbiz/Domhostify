from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.app.auth as auth_module
from backend.app.auth import create_session, hash_password
from backend.app.database import Base, MarketplaceListing, UserAccount, get_db
from backend.app.main import app


def _client_and_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    auth_module.SessionLocal = Session
    return engine, Session, TestClient(app)


def _register(client: TestClient, email: str, role: str) -> dict:
    response = client.post(
        "/api/v1/account/register",
        json={"email": email, "password": "Correct-Horse-Battery-77", "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _admin_token(Session) -> str:
    with Session() as db:
        admin = UserAccount(
            public_ref="admin-integration-ref",
            email="admin-integration@example.com",
            password_hash=hash_password("Correct-Horse-Battery-88"),
            role="admin",
            active=True,
        )
        db.add(admin)
        db.flush()
        token, _ = create_session(db, admin)
        db.commit()
        return token


def test_seller_listing_lifecycle_and_admin_moderation_boundaries() -> None:
    engine, Session, client = _client_and_session()
    try:
        seller = _register(client, "seller-lifecycle@example.com", "seller")
        buyer = _register(client, "buyer-boundary@example.com", "buyer")
        admin_token = _admin_token(Session)
        seller_headers = {"Authorization": f"Bearer {seller['access_token']}"}
        buyer_headers = {"Authorization": f"Bearer {buyer['access_token']}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        created = client.post(
            "/api/v1/marketplace/seller/listings",
            headers=seller_headers,
            json={"domain": "integration-example.com", "asking_price": 1200, "currency": "EUR", "sale_type": "buy_now"},
        )
        assert created.status_code == 201, created.text
        listing_id = created.json()["id"]
        assert created.json()["listing_status"] == "pending_review"

        assert client.get("/api/v1/marketplace/seller/listings", headers=buyer_headers).status_code == 403
        assert client.post(
            f"/api/v1/admin/marketplace/listings/{listing_id}/review",
            headers=seller_headers,
            json={"decision": "reject"},
        ).status_code == 403

        update = client.patch(
            f"/api/v1/marketplace/seller/listings/{listing_id}",
            headers=seller_headers,
            json={"asking_price": 1500},
        )
        assert update.status_code == 200, update.text
        assert update.json()["asking_price"] == 1500

        challenge = client.post(
            f"/api/v1/marketplace/seller/listings/{listing_id}/ownership-challenge",
            headers=seller_headers,
        )
        assert challenge.status_code == 201, challenge.text
        assert challenge.json()["record_type"] == "TXT"

        not_verified = client.post(
            f"/api/v1/admin/marketplace/listings/{listing_id}/review",
            headers=admin_headers,
            json={"decision": "approve"},
        )
        assert not_verified.status_code == 409

        with Session() as db:
            listing = db.scalar(select(MarketplaceListing).where(MarketplaceListing.id == listing_id))
            assert listing is not None
            listing.ownership_status = "verified"
            db.commit()

        approved = client.post(
            f"/api/v1/admin/marketplace/listings/{listing_id}/review",
            headers=admin_headers,
            json={"decision": "approve", "note": "Ownership checked by integration test"},
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["listing_status"] == "active"
        assert approved.json()["moderation_status"] == "approved"

        public = client.get("/api/v1/marketplace/persistent-listings")
        assert public.status_code == 200
        assert any(item["id"] == listing_id for item in public.json())

        audit = client.get(f"/api/v1/admin/marketplace/listings/{listing_id}/audit", headers=admin_headers)
        assert audit.status_code == 200, audit.text
        event_types = [event["event_type"] for event in audit.json()]
        assert "seller_listing_submitted" in event_types
        assert "ownership_challenge_created" in event_types
        assert "admin_listing_approved" in event_types
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
