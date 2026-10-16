from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_FRONTEND = ROOT / "frontend" / "index.html"
SELLER_DASHBOARD = ROOT / "frontend" / "seller-dashboard.html"


def test_public_frontend_has_configurable_api_base_and_no_bootstrap_credentials() -> None:
    content = PUBLIC_FRONTEND.read_text(encoding="utf-8")
    assert "DOMHOSTIFY_API_BASE" in content
    assert "DOMHOSTIFY_SELLER_API_TOKEN" not in content
    assert "DOMHOSTIFY_BUYER_API_TOKEN" not in content
    assert "DOMHOSTIFY_ADMIN_API_TOKEN" not in content
    assert "Authorization: 'Bearer" not in content
    assert "localStorage" not in content
    assert "sessionStorage" not in content


def test_seller_dashboard_is_session_oriented_and_does_not_accept_tokens() -> None:
    content = SELLER_DASHBOARD.read_text(encoding="utf-8")
    assert "session-oriented" in content
    assert "DOMHOSTIFY_SELLER_API_TOKEN" not in content
    assert "DOMHOSTIFY_BUYER_API_TOKEN" not in content
    assert "DOMHOSTIFY_ADMIN_API_TOKEN" not in content
    assert "localStorage" not in content
    assert "sessionStorage" not in content
    assert "type=\"password\"" not in content
