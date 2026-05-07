"""add billing core tables charges and payments

Revision ID: 20260507_0004
Revises: 20260506_0003
Create Date: 2026-05-07 00:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260507_0004"
down_revision: str | None = "20260506_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

charge_status = sa.Enum("pending", "paid", "cancelled", name="charge_status")
payment_method = sa.Enum("cash", "bank_transfer", "credit_card", "other", name="payment_method")


def upgrade() -> None:
    op.create_table(
        "charges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("flat_id", sa.String(length=36), nullable=False),
        sa.Column("charge_type", sa.String(length=50), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", charge_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["flat_id"], ["flats.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_charges_flat_id"), "charges", ["flat_id"], unique=False)
    op.create_index(
        "uq_charges_flat_period_type_active",
        "charges",
        ["flat_id", "period", "charge_type"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("flat_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", payment_method, nullable=False, server_default="bank_transfer"),
        sa.Column("reference_no", sa.String(length=100), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["flat_id"], ["flats.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_flat_id"), "payments", ["flat_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_flat_id"), table_name="payments")
    op.drop_table("payments")

    op.drop_index("uq_charges_flat_period_type_active", table_name="charges")
    op.drop_index(op.f("ix_charges_flat_id"), table_name="charges")
    op.drop_table("charges")
