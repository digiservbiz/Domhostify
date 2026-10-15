"""Add idempotency keys for retry-safe checkout intents."""
from alembic import op
import sqlalchemy as sa

revision = "0009_transaction_idempotency"
down_revision = "0008_listing_reservations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("marketplace_transactions", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.create_index(
        "uq_marketplace_transactions_buyer_idempotency",
        "marketplace_transactions",
        ["buyer_ref", "idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_marketplace_transactions_buyer_idempotency", table_name="marketplace_transactions")
    op.drop_column("marketplace_transactions", "idempotency_key")
