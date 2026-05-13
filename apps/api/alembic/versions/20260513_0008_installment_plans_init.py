"""installment_plans_init

Revision ID: 20260513_0008
Revises: 20260512_0007
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa

revision = "20260513_0008"
down_revision = "20260512_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "installment_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), sa.ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("flat_id", sa.String(36), sa.ForeignKey("flats.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("charge_id", sa.String(36), sa.ForeignKey("charges.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("installment_count", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "installment_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), sa.ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("installment_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("installment_no", sa.Integer, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "paid", "overdue", "cancelled", name="installment_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("paid_at", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("installment_items")
    op.drop_table("installment_plans")
    op.execute("DROP TYPE IF EXISTS installment_status")
