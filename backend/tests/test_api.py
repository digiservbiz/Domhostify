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
    assert result["source_status"] == "demo"


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
            assert "/" not in clicks[0].click_id
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
        assert "tracking database" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_cors_does_not_allow_all_origins_by_default() -> None:
    cors = next(middleware for middleware in app.user_middleware if middleware.cls.__name__ == "CORSMiddleware")
    assert "*" not in cors.options["allow_origins"]
    assert "http://localhost:5173" in cors.options["allow_origins"]


def test_persistent_hosting_plans_returns_only_active_verified_priced_rows_sorted() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with TestSession() as session:
        session.add_all([
            DBHostingPlan(
                provider_key="provider-b", plan_name="Business", site_type="Business website",
                introductory_price=9.0, renewal_price=15.0, currency="EUR",
                billing_period="month", storage="50 GB", support="Priority",
                source_status="verified", active=True,
            ),
            DBHostingPlan(
                provider_key="provider-a", plan_name="Starter", site_type="Small business",
                introductory_price=4.0, renewal_price=8.0, currency="EUR",
                billing_period="month", storage="20 GB", support="Email",
                source_status="verified", active=True,
            ),
            DBHostingPlan(
                provider_key="unverified", plan_name="Unverified", site_type="Business website",
                introductory_price=1.0, currency="EUR", storage="1 GB", support="None",
                source_status="demo_only", active=True,
            ),
            DBHostingPlan(
                provider_key="inactive", plan_name="Inactive", site_type="Business website",
                introductory_price=2.0, currency="EUR", storage="1 GB", support="None",
                source_status="verified", active=False,
            ),
            DBHostingPlan(
                provider_key="missing-price", plan_name="No price", site_type="Business website",
                introductory_price=None, currency="EUR", storage="1 GB", support="None",
                source_status="verified", active=True,
            ),
        ])
        session.commit()

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/hosting/persistent-plans")
        assert response.status_code == 200
        results = response.json()
        assert [item["plan_name"] for item in results] == ["Starter", "Business"]
        assert all(item["data_status"] == "database" for item in results)
        filtered = client.get(
            "/api/v1/hosting/persistent-plans",
            params={"site_type": "small business", "max_price": 5},
        )
        assert filtered.status_code == 200
        assert [item["plan_name"] for item in filtered.json()] == ["Starter"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_persistent_hosting_plans_fails_closed_when_schema_is_missing() -> None:
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
        response = client.get("/api/v1/hosting/persistent-plans")
        assert response.status_code == 503
        assert "Apply database migrations first" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_persistent_hosting_plans_are_capped_at_100() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with TestSession() as session:
        session.add_all([
            DBHostingPlan(
                provider_key=f"provider-{index}", plan_name=f"Plan {index}", site_type="Business website",
                introductory_price=float(index + 1), currency="EUR", storage="10 GB", support="Email",
                source_status="verified", active=True,
            )
            for index in range(105)
        ])
        session.commit()

    def override_get_db():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/hosting/persistent-plans")
        assert response.status_code == 200
        assert len(response.json()) == 100
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
