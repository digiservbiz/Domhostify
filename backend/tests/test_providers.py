from backend.app.providers import DemoRegistrarProvider


def test_demo_provider_never_claims_domain_availability() -> None:
    result = DemoRegistrarProvider().check_domain("available-looking.example")

    assert result.domain == "available-looking.example"
    assert result.availability == "unknown"
    assert result.source_status == "demo_only"
    assert result.provider_key == "demo"
    assert result.checked_at is None


def test_demo_provider_discloses_no_registrar_was_queried() -> None:
    result = DemoRegistrarProvider().check_domain("mybrand.com")

    assert "have not been checked" in result.note
