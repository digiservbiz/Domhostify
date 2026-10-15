from backend.app.database import Base


def test_catalog_models_define_expected_tables() -> None:
    assert "registrar_offers" in Base.metadata.tables
    assert "marketplace_listings" in Base.metadata.tables


def test_registrar_offer_availability_defaults_to_unknown() -> None:
    column = Base.metadata.tables["registrar_offers"].c.availability
    assert column.default.arg == "unknown"


def test_marketplace_listing_defaults_to_inactive_draft() -> None:
    table = Base.metadata.tables["marketplace_listings"]
    assert table.c.listing_status.default.arg == "draft"
    assert table.c.active.default.arg is False
