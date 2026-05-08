"""add charge plans and payment allocations

Revision ID: 20260508_0005
Revises: 20260507_0004
Create Date: 2026-05-08 00:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260508_0005"
down_revision: str | None = "20260507_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

charge_plan_frequency = sa.Enum("monthly", "quarterly", "yearly", name="charge_plan_frequency")


def upgrade() -> None:
    op.create_table(
        "charge_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("charge_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("frequency", charge_plan_frequency, nullable=False, server_default="monthly"),
        sa.Column("start_period", sa.String(length=7), nullable=False),
        sa.Column("end_period", sa.String(length=7), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "charge_plan_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("charge_plan_id", sa.String(length=36), nullable=False),
        sa.Column("flat_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["charge_plan_id"], ["charge_plans.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["flat_id"], ["flats.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_charge_plan_assignments_plan_flat_active",
        "charge_plan_assignments",
        ["charge_plan_id", "flat_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "payment_allocations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("payment_id", sa.String(length=36), nullable=False),
        sa.Column("charge_id", sa.String(length=36), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["charge_id"], ["charges.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_payment_allocations_payment_charge_active",
        "payment_allocations",
        ["payment_id", "charge_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_payment_allocations_payment_charge_active", table_name="payment_allocations")
    op.drop_table("payment_allocations")

    op.drop_index("uq_charge_plan_assignments_plan_flat_active", table_name="charge_plan_assignments")
    op.drop_table("charge_plan_assignments")

    op.drop_table("charge_plans")
