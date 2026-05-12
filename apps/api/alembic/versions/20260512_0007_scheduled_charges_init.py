"""add scheduled_charges table

Revision ID: 20260512_0007
Revises: 20260512_0006
Create Date: 2026-05-12 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260512_0007"
down_revision: str | None = "20260512_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scheduled_charges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("charge_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("day_of_month", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
    op.create_index(
        "ix_scheduled_charges_site_id", "scheduled_charges", ["site_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_scheduled_charges_site_id", table_name="scheduled_charges")
    op.drop_table("scheduled_charges")
