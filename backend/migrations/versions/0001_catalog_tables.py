"""Create initial registrar offer and marketplace listing tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001_catalog_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registrar_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("domain", sa.String(length=253), nullable=False),
        sa.Column("registrar_key", sa.String(length=80), nullable=False),
        sa.Column("availability", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("registration_price", sa.Float(), nullable=True),
        sa.Column("renewal_price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("source_status", sa.String(length=30), server_default="unverified", nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_registrar_offers_domain", "registrar_offers", ["domain"])
    op.create_index("ix_registrar_offers_registrar_key", "registrar_offers", ["registrar_key"])

    op.create_table(
        "marketplace_listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("domain", sa.String(length=253), nullable=False),
        sa.Column("asking_price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("sale_type", sa.String(length=30), server_default="make_offer", nullable=False),
        sa.Column("listing_status", sa.String(length=30), server_default="draft", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_marketplace_listings_domain", "marketplace_listings", ["domain"])
    op.create_index("ix_marketplace_listings_listing_status", "marketplace_listings", ["listing_status"])


def downgrade() -> None:
    op.drop_index("ix_marketplace_listings_listing_status", table_name="marketplace_listings")
    op.drop_index("ix_marketplace_listings_domain", table_name="marketplace_listings")
    op.drop_table("marketplace_listings")
    op.drop_index("ix_registrar_offers_registrar_key", table_name="registrar_offers")
    op.drop_index("ix_registrar_offers_domain", table_name="registrar_offers")
    op.drop_table("registrar_offers")
