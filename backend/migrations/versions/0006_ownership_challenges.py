"""Add ownership verification challenge records."""
from alembic import op
import sqlalchemy as sa

revision = "0006_ownership_challenges"
down_revision = "0005_listing_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ownership_challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(length=30), server_default="dns_txt", nullable=False),
        sa.Column("challenge_label", sa.String(length=253), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ownership_challenges_listing_id", "ownership_challenges", ["listing_id"])
    op.create_index("ix_ownership_challenges_status", "ownership_challenges", ["status"])
    op.create_index("ix_ownership_challenges_expires_at", "ownership_challenges", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_ownership_challenges_expires_at", table_name="ownership_challenges")
    op.drop_index("ix_ownership_challenges_status", table_name="ownership_challenges")
    op.drop_index("ix_ownership_challenges_listing_id", table_name="ownership_challenges")
    op.drop_table("ownership_challenges")
