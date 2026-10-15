"""Add persistent hosting plan catalog."""
from alembic import op
import sqlalchemy as sa

revision = "0002_hosting_plans"
down_revision = "0001_catalog_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hosting_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider_key", sa.String(length=80), nullable=False),
        sa.Column("plan_name", sa.String(length=120), nullable=False),
        sa.Column("site_type", sa.String(length=120), nullable=False),
        sa.Column("introductory_price", sa.Float(), nullable=True),
        sa.Column("renewal_price", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="EUR", nullable=False),
        sa.Column("billing_period", sa.String(length=20), server_default="month", nullable=False),
        sa.Column("storage", sa.String(length=120), nullable=False),
        sa.Column("support", sa.String(length=120), nullable=False),
        sa.Column("source_status", sa.String(length=30), server_default="unverified", nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_hosting_plans_provider_key", "hosting_plans", ["provider_key"])
    op.create_index("ix_hosting_plans_active", "hosting_plans", ["active"])


def downgrade() -> None:
    op.drop_index("ix_hosting_plans_active", table_name="hosting_plans")
    op.drop_index("ix_hosting_plans_provider_key", table_name="hosting_plans")
    op.drop_table("hosting_plans")
