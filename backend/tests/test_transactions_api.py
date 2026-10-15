import hashlib
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from backend.app.database import (
    Base,
    ListingAuditEvent,
    MarketplaceListing,
    MarketplaceTransaction,
    MarketplaceTransactionEvent,
    get_db,
)
from backend.app.main import app

client = TestClient(app)
SELLER_TOKEN = "offers-seller-token"
BUYER_TOKEN = "offers-buyer-token"
SELLER_REF = hashlib.sha256(SELLER_TOKEN.encode()).hexdigest()[:32]
BUYER_REF = hashlib.sha256(BUYER_TOKEN.encode()).hexdigest()[:32]
SELLER_HEADERS = {"Authorization": f"Bearer {SELLER_TOKEN}"}
BUYER_HEADERS = {"Authorization": f"Bearer {BUYER_TOKEN}"}


def _setup(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setenv("DOMHOSTIFY_SELLER_API_TOKEN", SELLER_TOKEN)
    monkeypatch.setenv("DOMHOSTIFY_BUYER_API_TOKEN", BUYER_TOKEN)
    return engine, Session


def _cleanup(engine):
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _create_listing(published=True):
    response = client.post(
        "/api/v1/marketplace/seller/listings",
        headers=SELLER_HEADERS,
        json={"domain": "offer-target.com", "asking_price": 250},
    )
    assert response.status_code == 201
    listing_id = response.json()["id"]
    if published:
        from backend.app.database import MarketplaceListing as Listing
        # The fixture session is reached through the dependency override.
        session_gen = app.dependency_overrides[get_db]()
        db = next(session_gen)
        try:
            listing = db.get(Listing, listing_id)
            listing.ownership_status = "verified"
            listing.moderation_status = "approved"
            listing.listing_status = "active"
            listing.active = True
            db.commit()
        finally:
            try:
                next(session_gen)
            except StopIteration:
                pass
    return listing_id


def _enable_buy_now(Session, listing_id):
    with Session() as db:
        listing = db.get(MarketplaceListing, listing_id)
        listing.sale_type = "buy_now"
        db.commit()


def test_buy_now_reservation_blocks_second_checkout_and_cancel_releases(monkeypatch):
    engine, Session = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        _enable_buy_now(Session, listing_id)

        first = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/buy-now",
            headers={**BUYER_HEADERS, "Idempotency-Key": "buy-first"},
        )
        assert first.status_code == 201
        intent = first.json()
        assert intent["status"] == "buy_now_pending"
        assert intent["payment_status"] == "not_started"
        assert "No payment has been taken" in intent["message"]

        second = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/buy-now",
            headers={**BUYER_HEADERS, "Idempotency-Key": "buy-second"},
        )
        assert second.status_code == 409

        cancelled = client.post(
            f"/api/v1/marketplace/buyer/offers/{intent['id']}/cancel",
            headers=BUYER_HEADERS,
        )
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"

        retry = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/buy-now",
            headers={**BUYER_HEADERS, "Idempotency-Key": "buy-retry"},
        )
        assert retry.status_code == 201
        with Session() as db:
            listing = db.get(MarketplaceListing, listing_id)
            assert listing.reservation_transaction_id == retry.json()["id"]
            assert listing.reserved_until is not None
            events = db.scalars(select(MarketplaceTransactionEvent).where(
                MarketplaceTransactionEvent.transaction_id == retry.json()["id"]
            )).all()
            assert [event.to_status for event in events] == ["buy_now_pending"]
    finally:
        _cleanup(engine)


def test_buy_now_idempotency_returns_same_reservation_on_retry(monkeypatch):
    engine, Session = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        _enable_buy_now(Session, listing_id)
        headers = {**BUYER_HEADERS, "Idempotency-Key": "stable-checkout-request"}
        first = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/buy-now",
            headers=headers,
        )
        replay = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/buy-now",
            headers=headers,
        )
        assert first.status_code == 201
        assert replay.status_code == 201
        assert replay.json()["id"] == first.json()["id"]
        with Session() as db:
            rows = db.scalars(select(MarketplaceTransaction).where(
                MarketplaceTransaction.idempotency_key == "stable-checkout-request"
            )).all()
            assert len(rows) == 1
    finally:
        _cleanup(engine)


def test_buy_now_requires_idempotency_key(monkeypatch):
    engine, Session = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        _enable_buy_now(Session, listing_id)
        response = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/buy-now",
            headers=BUYER_HEADERS,
        )
        assert response.status_code == 400
    finally:
        _cleanup(engine)


def test_buy_now_requires_sale_type_and_public_listing(monkeypatch):
    engine, _ = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        response = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/buy-now",
            headers=BUYER_HEADERS,
        )
        assert response.status_code == 404
    finally:
        _cleanup(engine)


def test_buyer_creates_offer_and_seller_accepts_with_audit(monkeypatch):
    engine, Session = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        created = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/offers",
            headers=BUYER_HEADERS,
            json={"amount": "175.50"},
        )
        assert created.status_code == 201
        offer = created.json()
        assert offer["domain"] == "offer-target.com"
        assert offer["status"] == "offer_pending"
        offer_id = offer["id"]

        seller_inventory = client.get(
            f"/api/v1/marketplace/seller/listings/{listing_id}/offers",
            headers=SELLER_HEADERS,
        )
        assert seller_inventory.status_code == 200
        assert len(seller_inventory.json()) == 1

        decision = client.post(
            f"/api/v1/marketplace/seller/offers/{offer_id}/decision",
            headers=SELLER_HEADERS,
            json={"decision": "accept", "note": "Offer accepted for review"},
        )
        assert decision.status_code == 200
        assert decision.json()["status"] == "accepted"

        with Session() as db:
            transaction = db.get(MarketplaceTransaction, offer_id)
            events = db.scalars(select(MarketplaceTransactionEvent).where(
                MarketplaceTransactionEvent.transaction_id == offer_id
            )).all()
            assert transaction is not None
            assert transaction.amount == Decimal("175.50")
            assert transaction.status == "accepted"
            assert [event.to_status for event in events] == ["offer_pending", "accepted"]
    finally:
        _cleanup(engine)


def test_buyer_can_cancel_pending_offer_once(monkeypatch):
    engine, _ = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        created = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/offers",
            headers=BUYER_HEADERS,
            json={"amount": "100.00"},
        )
        offer_id = created.json()["id"]
        cancelled = client.post(
            f"/api/v1/marketplace/buyer/offers/{offer_id}/cancel",
            headers=BUYER_HEADERS,
        )
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"
        replay = client.post(
            f"/api/v1/marketplace/buyer/offers/{offer_id}/cancel",
            headers=BUYER_HEADERS,
        )
        assert replay.status_code == 409
    finally:
        _cleanup(engine)


def test_offer_creation_requires_public_listing(monkeypatch):
    engine, _ = _setup(monkeypatch)
    try:
        listing_id = _create_listing(published=False)
        response = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/offers",
            headers=BUYER_HEADERS,
            json={"amount": "100.00"},
        )
        assert response.status_code == 404
    finally:
        _cleanup(engine)


def test_seller_cannot_decide_another_sellers_offer(monkeypatch):
    engine, _ = _setup(monkeypatch)
    try:
        listing_id = _create_listing()
        created = client.post(
            f"/api/v1/marketplace/listings/{listing_id}/offers",
            headers=BUYER_HEADERS,
            json={"amount": "100.00"},
        )
        offer_id = created.json()["id"]
        monkeypatch.setenv("DOMHOSTIFY_SELLER_API_TOKEN", "different-seller-token")
        response = client.post(
            f"/api/v1/marketplace/seller/offers/{offer_id}/decision",
            headers={"Authorization": "Bearer different-seller-token"},
            json={"decision": "accept"},
        )
        assert response.status_code == 404
    finally:
        _cleanup(engine)
