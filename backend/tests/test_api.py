from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import AffiliateClick as DBAffiliateClick, Base, HostingPlanRecord as DBHostingPlan, MarketplaceListing as DBMarketplaceListing, RegistrarOffer as DBRegistrarOffer, get_db
from backend.app.main import app, normalize_domain_query

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_domain_normalization_adds_com_for_bare_name() -> None:
    assert normalize_domain_query("  MyGreatBrand ") == "mygreatbrand.com"


def test_domain_normalization_lowercases_and_removes_trailing_dot() -> None:
    assert normalize_domain_query("Shop.Example.NET.") == "shop.example.net"


def test_domain_normalization_rejects_spaces_and_url_parts() -> None:
    for invalid in ("bad domain", "https://example.com", "foo/bar", "a@b.com"):
        try:
            normalize_domain_query(invalid)
        except ValueError:
            continue
        raise AssertionError(f"Expected invalid domain: {invalid}")


def test_domain_search_returns_unknown_availability() -> None:
    response = client.get("/api/v1/domains/search", params={"q": "example.com"})
    assert response.status_code == 200
    result = response.json()[0]
    assert result["availability"] == "unknown"
    assert result["source_status"] == "demo_only"


def test_domain_suggestions_rejects_invalid_brand_or_extensions() -> None:
    invalid_params = [
        {"q": "https://mybrand.com", "extensions": "com"},
        {"q": "brand_name", "extensions": "com"},
        {"q": "mybrand", "extensions": "com,../admin"},
        {"q": "mybrand", "extensions": ",".join(["com"] * 11)},
    ]
    for params in invalid_params:
        response = client.get("/api/v1/domains/suggestions", params=params)
        assert response.status_code == 422


def test_affiliate_redirect_rejects_unknown_provider() -> None:
    response = client.get("/api/v1/affiliate/unknown", follow_redirects=False)
    assert response.status_code == 404


def test_affiliate_redirect_requires_configured_destination(monkeypatch) -> None:
    monkeypatch.delenv("AFFILIATE_URL_EXAMPLEHOST", raising=False)
    response = client.get("/api/v1/affiliate/examplehost", follow_redirects=False)
    assert response.status_code == 503


def test_affiliate_redirect_only_accepts_https_destination(monkeypatch) -> None:
    monkeypatch.setenv("AFFILIATE_URL_EXAMPLEHOST", "http://unsafe.example/offer")
    response = client.get("/api/v1/affiliate/examplehost", follow_redirects=False)
    assert response.status_code == 503


def test_affiliate_redirect_uses_allowlisted_destination_and_persists_opaque_click(monkeypatch) -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    def override_get_db():
        with TestSession() as session:
            yield session
    monkeypatch.setenv("AFFILIATE_URL_EXAMPLEHOST", "https://partner.example/offer?ref=domhostify")
    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/affiliate/examplehost", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "https://partner.example/offer?ref=domhostify"
        with TestSession() as session:
            clicks = session.scalars(select(DBAffiliateClick)).all()
            assert len(clicks) == 1
            assert clicks[0].provider_key == "examplehost"
            assert len(clicks[0].click_id) == 36
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_affiliate_redirect_fails_closed_when_tracking_schema_is_missing(monkeypatch) -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    def override_get_db():
        with TestSession() as session:
            yield session
    monkeypatch.setenv("AFFILIATE_URL_EXAMPLEHOST", "https://partner.example/offer")
    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/affiliate/examplehost", follow_redirects=False)
        assert response.status_code == 503
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_cors_does_not_allow_all_origins_by_default() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def _marketplace_client_with_rows(rows):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with TestSession() as session:
        session.add_all(rows)
        session.commit()
    def override_get_db():
        with TestSession() as session:
            yield session
    app.dependency_overrides[get_db] = override_get_db
    return engine


def test_marketplace_public_reads_require_ownership_and_moderation_approval() -> None:
    engine = _marketplace_client_with_rows([
        DBMarketplaceListing(domain="approved.com", asking_price=100, sale_type="buy_now", listing_status="active", ownership_status="verified", moderation_status="approved", active=True),
        DBMarketplaceListing(domain="unverified.com", asking_price=90, sale_type="buy_now", listing_status="active", ownership_status="unverified", moderation_status="approved", active=True),
        DBMarketplaceListing(domain="pending.com", asking_price=80, sale_type="make_offer", listing_status="active", ownership_status="verified", moderation_status="pending", active=True),
        DBMarketplaceListing(domain="draft.com", asking_price=70, sale_type="make_offer", listing_status="draft", ownership_status="verified", moderation_status="approved", active=False),
    ])
    try:
        response = client.get("/api/v1/marketplace/persistent-listings")
        assert response.status_code == 200
        assert [row["domain"] for row in response.json()] == ["approved.com"]
        detail = client.get("/api/v1/marketplace/persistent-listings/1")
        assert detail.status_code == 200
        assert detail.json()["ownership_status"] == "verified"
        hidden = client.get("/api/v1/marketplace/persistent-listings/2")
        assert hidden.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
