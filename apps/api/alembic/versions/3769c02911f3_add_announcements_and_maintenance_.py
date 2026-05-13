"""add announcements and maintenance_requests tables

Revision ID: 3769c02911f3
Revises: 4da41bf2f29e
Create Date: 2026-05-13 17:43:07.755899
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3769c02911f3'
down_revision: Union[str, None] = '4da41bf2f29e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), sa.ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("block_id", sa.String(36), sa.ForeignKey("blocks.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "maintenance_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("site_id", sa.String(36), sa.ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("flat_id", sa.String(36), sa.ForeignKey("flats.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("reported_by", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "category",
            sa.Enum("electrical", "plumbing", "elevator", "common_area", "heating", "other", name="maintenance_category"),
            nullable=False,
            server_default="other",
        ),
        sa.Column(
            "status",
            sa.Enum("open", "in_progress", "resolved", "cancelled", name="maintenance_status"),
            nullable=False,
            server_default="open",
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("maintenance_requests")
    op.drop_table("announcements")
    op.execute("DROP TYPE IF EXISTS maintenance_status")
    op.execute("DROP TYPE IF EXISTS maintenance_category")
