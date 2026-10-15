from backend.app.database import Base


def test_catalog_models_define_expected_tables() -> None:
    assert "registrar_offers" in Base.metadata.tables
    assert "marketplace_listings" in Base.metadata.tables
    assert "hosting_plans" in Base.metadata.tables
    assert "listing_audit_events" in Base.metadata.tables
    assert "ownership_challenges" in Base.metadata.tables


def test_registrar_offer_availability_defaults_to_unknown() -> None:
    column = Base.metadata.tables["registrar_offers"].c.availability
    assert column.default.arg == "unknown"
    assert column.server_default.arg == "unknown"


def test_marketplace_listing_defaults_to_inactive_draft() -> None:
    table = Base.metadata.tables["marketplace_listings"]
    assert table.c.listing_status.default.arg == "draft"
    assert table.c.ownership_status.default.arg == "unverified"
    assert table.c.moderation_status.default.arg == "pending"
    assert table.c.active.default.arg is False
    assert table.c.created_at.server_default is not None


def test_catalog_price_fields_are_nullable_until_provider_data_exists() -> None:
    table = Base.metadata.tables["registrar_offers"]
    assert table.c.registration_price.nullable
    assert table.c.renewal_price.nullable


def test_hosting_plan_catalog_defaults_to_inactive_unverified() -> None:
    table = Base.metadata.tables["hosting_plans"]
    assert table.c.source_status.default.arg == "unverified"
    assert table.c.active.default.arg is False
    assert table.c.introductory_price.nullable
    assert table.c.renewal_price.nullable


def test_listing_audit_event_is_opaque_and_personal_data_free_by_design() -> None:
    table = Base.metadata.tables["listing_audit_events"]
    assert table.c.listing_id.nullable is False
    assert table.c.event_type.nullable is False
    assert table.c.actor_ref.type.length == 64
    assert table.c.event_note.type.length == 500
    assert "ip_address" not in table.c
    assert "user_agent" not in table.c


def test_ownership_challenge_stores_only_a_token_hash() -> None:
    table = Base.metadata.tables["ownership_challenges"]
    assert table.c.method.default.arg == "dns_txt"
    assert table.c.status.default.arg == "pending"
    assert table.c.token_hash.type.length == 128
    assert "token" not in table.c
    assert table.c.expires_at.nullable is False
