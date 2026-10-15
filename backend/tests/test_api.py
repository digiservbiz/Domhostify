from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, MarketplaceListing as DBMarketplaceListing, RegistrarOffer as DBRegistrarOffer, get_db
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
            pass
        else:
            raise AssertionError(f"Expected invalid domain to be rejected: {invalid}")


def test_domain_normalization_rejects_invalid_labels() -> None:
    for invalid in ("-badname.com", "bad_name.com", "two..dots.com", "bad-.com"):
        try:
            normalize_domain_query(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected invalid domain to be rejected: {invalid}")


def test_domain_search_is_explicitly_demo_and_unknown() -> None:
    response = client.get("/api/v1/domains/search", params={"q": "mygreatbrand"})
    assert response.status_code == 200
    result = response.json()[0]
    assert result["domain"] == "mygreatbrand.com"
    assert result["availability"] == "unknown"
    assert result["source_status"] == "demo_only"


def test_domain_search_rejects_malformed_input() -> None:
    for invalid in ("bad domain", "foo/bar", "-bad.com"):
        response = client.get("/api/v1/domains/search", params={"q": invalid})
        assert response.status_code == 422


def test_hosting_plans_are_marked_demo() -> None:
    response = client.get("/api/v1/hosting/plans")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert all(plan["data_status"] == "demo" for plan in response.json())


def test_hosting_plan_price_filter() -> None:
    response = client.get("/api/v1/hosting/plans", params={"max_price": 5})
    assert response.status_code == 200
    assert all(plan["introductory_price"] <= 5 for plan in response.json())


def test_hosting_plan_site_type_filter() -> None:
    response = client.get("/api/v1/hosting/plans", params={"site_type": "small business"})
    assert response.status_code == 200
    assert all("small business" in plan["site_type"].lower() for plan in response.json())


def test_marketplace_listings_are_marked_demo() -> None:
    response = client.get("/api/v1/marketplace/listings")
    assert response.status_code == 200
    assert all(item["data_status"] == "demo" for item in response.json())


def test_marketplace_search_filter() -> None:
    response = client.get("/api/v1/marketplace/listings", params={"q": "examplebrand"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["domain"] == "examplebrand.com"


def test_marketplace_price_filter() -> None:
    response = client.get("/api/v1/marketplace/listings", params={"max_price": 1000})
    assert response.status_code == 200
    assert all(item["asking_price"] <= 1000 for item in response.json())



def test_domain_suggestions_returns_requested_extensions_as_unknown() -> None:
    response = client.get(
        "/api/v1/domains/suggestions",
        params={"q": "mybrand", "extensions": "com,net,io"},
    )
    assert response.status_code == 200
    results = response.json()
    assert [item["domain"] for item in results] == [
        "mybrand.com", "mybrand.net", "mybrand.io"
    ]
    assert all(item["availability"] == "unknown" for item in results)
    assert all(item["source_status"] == "demo_only" for item in results)


def test_domain_suggestions_removes_duplicate_extensions() -> None:
    response = client.get(
        "/api/v1/domains/suggestions",
        params={"q": "mybrand", "extensions": "com,.com,net"},
    )
    assert response.status_code == 200
    assert [item["domain"] for item in response.json()] == [
        "mybrand.com", "mybrand.net"
    ]


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


def test_affiliate_redirect_uses_allowlisted_configured_destination(monkeypatch) -> None:
    monkeypatch.setenv("AFFILIATE_URL_EXAMPLEHOST", "https://partner.example/offer?ref=domhostify")
    response = client.get("/api/v1/affiliate/examplehost", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://partner.example/offer?ref=domhostify"


def test_cors_does_not_allow_all_origins_by_default() -> None:
    cors = next(middleware for middleware in app.user_middleware if middleware.cls.__name__ == "CORSMiddleware")
    assert "*" not in cors.options["allow_origins"]
    assert "http://localhost:5173" in cors.options["allow_origins"]


def test_persistent_marketplace_endpoint_returns_only_active_database_listings() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with TestSession() as session:
        session.add_all([
            DBMarketplaceListing(
                domain="activebrand.com", asking_price=500, currency="EUR",
                sale_type="buy_now", listing_status="active", active=True,
            ),
            DBMarketplaceListing(
                domain="draftbrand.com", asking_price=100, currency="EUR",
                sale_type="buy_now", listing_status="draft", active=False,
            ),
            DBMarketplaceListing(
                domain="inactiveflag.com", asking_price=200, currency="EUR",
                sale_type="make_offer", listing_status="active", active=False,
            ),
        ])
        session.commit()

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/marketplace/persistent-listings")
        assert response.status_code == 200
        results = response.json()
        assert [item["domain"] for item in results] == ["activebrand.com"]
        assert results[0]["data_status"] == "database"

        filtered = client.get(
            "/api/v1/marketplace/persistent-listings",
            params={"max_price": 100},
        )
        assert filtered.status_code == 200
        assert filtered.json() == []
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_persistent_marketplace_endpoint_fails_closed_when_schema_is_missing() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/marketplace/persistent-listings")
        assert response.status_code == 503
        assert "Apply database migrations first" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_registrar_offers_returns_only_verified_priced_rows_sorted_by_price() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with TestSession() as session:
        session.add_all([
            DBRegistrarOffer(
                domain="brandexample.com", registrar_key="registrar-b",
                availability="unknown", registration_price=12.0, renewal_price=18.0,
                currency="EUR", source_status="verified",
            ),
            DBRegistrarOffer(
                domain="brandexample.com", registrar_key="registrar-a",
                availability="available", registration_price=8.0, renewal_price=16.0,
                currency="EUR", source_status="verified",
            ),
            DBRegistrarOffer(
                domain="brandexample.com", registrar_key="unverified",
                availability="available", registration_price=1.0, currency="EUR",
                source_status="demo_only",
            ),
            DBRegistrarOffer(
                domain="brandexample.com", registrar_key="missing-price",
                availability="unknown", registration_price=None, currency="EUR",
                source_status="verified",
            ),
        ])
        session.commit()

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/domains/offers", params={"domain": "brandexample.com"})
        assert response.status_code == 200
        offers = response.json()
        assert [item["registrar_key"] for item in offers] == ["registrar-a", "registrar-b"]
        assert [item["registration_price"] for item in offers] == [8.0, 12.0]
        assert all(item["source_status"] == "verified" for item in offers)
        assert offers[0]["availability"] == "available"
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_registrar_offers_rejects_invalid_domain() -> None:
    response = client.get("/api/v1/domains/offers", params={"domain": "https://bad.example"})
    assert response.status_code == 422


def test_registrar_offers_fails_closed_when_schema_is_missing() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/domains/offers", params={"domain": "brandexample.com"})
        assert response.status_code == 503
        assert "Apply database migrations first" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()
