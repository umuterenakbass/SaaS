"""add blocks flats and resident relations

Revision ID: 20260506_0002
Revises: 20260504_0001
Create Date: 2026-05-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260506_0002"
down_revision: str | None = "20260504_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

flat_status = sa.Enum("active", "inactive", name="flat_status")
resident_relation_type = sa.Enum("owner", "tenant", name="resident_relation_type")


def upgrade() -> None:
    op.create_table(
        "blocks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
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
        sa.UniqueConstraint("site_id", "code", name="uq_blocks_site_id_code"),
    )

    op.create_table(
        "flats",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("block_id", sa.String(length=36), nullable=False),
        sa.Column("unit_no", sa.String(length=50), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", flat_status, nullable=False, server_default="active"),
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
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("block_id", "unit_no", name="uq_flats_block_id_unit_no"),
    )

    op.create_table(
        "resident_flat_relations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("site_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("flat_id", sa.String(length=36), nullable=False),
        sa.Column("relation_type", resident_relation_type, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["flat_id"], ["flats.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_resident_flat_relations_user_id"),
        "resident_flat_relations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resident_flat_relations_flat_id"),
        "resident_flat_relations",
        ["flat_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_resident_flat_relations_flat_id"), table_name="resident_flat_relations")
    op.drop_index(op.f("ix_resident_flat_relations_user_id"), table_name="resident_flat_relations")
    op.drop_table("resident_flat_relations")
    op.drop_table("flats")
    op.drop_table("blocks")
