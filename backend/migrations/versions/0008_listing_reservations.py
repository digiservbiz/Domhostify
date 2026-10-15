"""Add expiring Buy Now reservation fields to listings."""
from alembic import op
import sqlalchemy as sa

revision = "0008_listing_reservations"
down_revision = "0007_marketplace_transactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("marketplace_listings", sa.Column("reservation_transaction_id", sa.Integer(), nullable=True))
    op.add_column("marketplace_listings", sa.Column("reserved_until", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_marketplace_listings_reservation_transaction_id", "marketplace_listings", ["reservation_transaction_id"])
    op.create_index("ix_marketplace_listings_reserved_until", "marketplace_listings", ["reserved_until"])


def downgrade() -> None:
    op.drop_index("ix_marketplace_listings_reserved_until", table_name="marketplace_listings")
    op.drop_index("ix_marketplace_listings_reservation_transaction_id", table_name="marketplace_listings")
    op.drop_column("marketplace_listings", "reserved_until")
    op.drop_column("marketplace_listings", "reservation_transaction_id")
