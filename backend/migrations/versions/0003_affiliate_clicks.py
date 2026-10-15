"""Add privacy-conscious affiliate click tracking."""
from alembic import op
import sqlalchemy as sa

revision = "0003_affiliate_clicks"
down_revision = "0002_hosting_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "affiliate_clicks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("click_id", sa.String(length=36), nullable=False),
        sa.Column("provider_key", sa.String(length=80), nullable=False),
        sa.Column("clicked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("click_id", name="uq_affiliate_clicks_click_id"),
    )
    op.create_index("ix_affiliate_clicks_click_id", "affiliate_clicks", ["click_id"])
    op.create_index("ix_affiliate_clicks_provider_key", "affiliate_clicks", ["provider_key"])


def downgrade() -> None:
    op.drop_index("ix_affiliate_clicks_provider_key", table_name="affiliate_clicks")
    op.drop_index("ix_affiliate_clicks_click_id", table_name="affiliate_clicks")
    op.drop_table("affiliate_clicks")
