"""make flat unique constraint active-only for soft delete

Revision ID: 20260506_0003
Revises: 20260506_0002
Create Date: 2026-05-06 00:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260506_0003"
down_revision: str | None = "20260506_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # SQLite does not support DROP CONSTRAINT directly — use batch mode
    with op.batch_alter_table("flats") as batch_op:
        try:
            batch_op.drop_constraint("uq_flats_block_id_unit_no", type_="unique")
        except Exception:
            pass  # constraint may not exist in SQLite
    op.create_index(
        "uq_flats_block_id_unit_no_active",
        "flats",
        ["block_id", "unit_no"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_flats_block_id_unit_no_active", table_name="flats")
    op.create_unique_constraint(
        "uq_flats_block_id_unit_no",
        "flats",
        ["block_id", "unit_no"],
    )
