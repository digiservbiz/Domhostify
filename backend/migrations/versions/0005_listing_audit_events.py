"""Add marketplace listing audit events."""
from alembic import op
import sqlalchemy as sa

revision = "0005_listing_audit_events"
down_revision = "0004_marketplace_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listing_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("actor_type", sa.String(length=30), server_default="system", nullable=False),
        sa.Column("actor_ref", sa.String(length=64), nullable=True),
        sa.Column("event_note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_listing_audit_events_listing_id", "listing_audit_events", ["listing_id"])
    op.create_index("ix_listing_audit_events_event_type", "listing_audit_events", ["event_type"])
    op.create_index("ix_listing_audit_events_created_at", "listing_audit_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_listing_audit_events_created_at", table_name="listing_audit_events")
    op.drop_index("ix_listing_audit_events_event_type", table_name="listing_audit_events")
    op.drop_index("ix_listing_audit_events_listing_id", table_name="listing_audit_events")
    op.drop_table("listing_audit_events")
