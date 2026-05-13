"""add announcements and maintenance_requests tables

Revision ID: 4da41bf2f29e
Revises: 20260513_0008
Create Date: 2026-05-13 17:37:13.205931
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4da41bf2f29e'
down_revision: Union[str, None] = '20260513_0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
