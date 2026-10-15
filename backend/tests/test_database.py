from backend.app.database import Base, MarketplaceListing, RegistrarOffer


def test_catalog_models_define_expected_tables() -> None:
    assert "registrar_offers" in Base.metadata.tables
    assert "marketplace_listings" in Base.metadata.tables


def test_registrar_offer_never_defaults_to_available() -> None:
    offer = RegistrarOffer(domain="example.com", registrar_key="demo")
    assert offer.availability == "unknown"
    assert offer.source_status == "unverified"


def test_marketplace_listing_defaults_to_inactive_draft() -> None:
    listing = MarketplaceListing(domain="example.com", asking_price=100.0)
    assert listing.listing_status == "draft"
    assert listing.active is False
