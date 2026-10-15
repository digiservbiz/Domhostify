from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_endpoint() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_domain_search_is_explicitly_demo_and_unknown() -> None:
    response = client.get("/api/v1/domains/search", params={"q": "mygreatbrand"})
    assert response.status_code == 200
    result = response.json()[0]
    assert result["domain"] == "mygreatbrand.com"
    assert result["availability"] == "unknown"
    assert result["source_status"] == "demo_only"


def test_domain_search_rejects_spaces() -> None:
    response = client.get("/api/v1/domains/search", params={"q": "bad domain"})
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


def test_marketplace_listings_are_marked_demo() -> None:
    response = client.get("/api/v1/marketplace/listings")
    assert response.status_code == 200
    assert all(item["data_status"] == "demo" for item in response.json())


def test_marketplace_search_filter() -> None:
    response = client.get("/api/v1/marketplace/listings", params={"q": "examplebrand"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["domain"] == "examplebrand.com"
