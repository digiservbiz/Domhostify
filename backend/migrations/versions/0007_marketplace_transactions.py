"""Add transaction state and append-only event records."""
from alembic import op
import sqlalchemy as sa

revision = "0007_marketplace_transactions"
down_revision = "0006_ownership_challenges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marketplace_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("buyer_ref", sa.String(length=64), nullable=False),
        sa.Column("seller_ref", sa.String(length=64), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), server_default="make_offer", nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("status", sa.String(length=30), server_default="offer_pending", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_marketplace_transactions_listing_id", "marketplace_transactions", ["listing_id"])
    op.create_index("ix_marketplace_transactions_buyer_ref", "marketplace_transactions", ["buyer_ref"])
    op.create_index("ix_marketplace_transactions_seller_ref", "marketplace_transactions", ["seller_ref"])
    op.create_index("ix_marketplace_transactions_status", "marketplace_transactions", ["status"])

    op.create_table(
        "marketplace_transaction_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("from_status", sa.String(length=30), nullable=True),
        sa.Column("to_status", sa.String(length=30), nullable=False),
        sa.Column("actor_type", sa.String(length=30), server_default="system", nullable=False),
        sa.Column("actor_ref", sa.String(length=64), nullable=True),
        sa.Column("event_note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_marketplace_transaction_events_transaction_id", "marketplace_transaction_events", ["transaction_id"])
    op.create_index("ix_marketplace_transaction_events_event_type", "marketplace_transaction_events", ["event_type"])
    op.create_index("ix_marketplace_transaction_events_created_at", "marketplace_transaction_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_marketplace_transaction_events_created_at", table_name="marketplace_transaction_events")
    op.drop_index("ix_marketplace_transaction_events_event_type", table_name="marketplace_transaction_events")
    op.drop_index("ix_marketplace_transaction_events_transaction_id", table_name="marketplace_transaction_events")
    op.drop_table("marketplace_transaction_events")
    op.drop_index("ix_marketplace_transactions_status", table_name="marketplace_transactions")
    op.drop_index("ix_marketplace_transactions_seller_ref", table_name="marketplace_transactions")
    op.drop_index("ix_marketplace_transactions_buyer_ref", table_name="marketplace_transactions")
    op.drop_index("ix_marketplace_transactions_listing_id", table_name="marketplace_transactions")
    op.drop_table("marketplace_transactions")
