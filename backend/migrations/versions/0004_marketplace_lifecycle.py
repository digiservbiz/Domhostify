"""Add marketplace ownership and moderation lifecycle fields."""
from alembic import op
import sqlalchemy as sa

revision = "0004_marketplace_lifecycle"
down_revision = "0003_affiliate_clicks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("marketplace_listings", sa.Column("ownership_status", sa.String(length=30), server_default="unverified", nullable=False))
    op.add_column("marketplace_listings", sa.Column("moderation_status", sa.String(length=30), server_default="pending", nullable=False))
    op.add_column("marketplace_listings", sa.Column("seller_ref", sa.String(length=64), nullable=True))
    op.add_column("marketplace_listings", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_marketplace_listings_ownership_status", "marketplace_listings", ["ownership_status"])
    op.create_index("ix_marketplace_listings_moderation_status", "marketplace_listings", ["moderation_status"])
    op.create_index("ix_marketplace_listings_seller_ref", "marketplace_listings", ["seller_ref"])


def downgrade() -> None:
    op.drop_index("ix_marketplace_listings_seller_ref", table_name="marketplace_listings")
    op.drop_index("ix_marketplace_listings_moderation_status", table_name="marketplace_listings")
    op.drop_index("ix_marketplace_listings_ownership_status", table_name="marketplace_listings")
    op.drop_column("marketplace_listings", "updated_at")
    op.drop_column("marketplace_listings", "seller_ref")
    op.drop_column("marketplace_listings", "moderation_status")
    op.drop_column("marketplace_listings", "ownership_status")
