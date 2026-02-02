"""empty message

Revision ID: 4c8e7b92c6d6
Revises: 62d783428d52
Create Date: 2026-02-01 18:00:04.100532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '4c8e7b92c6d6'
down_revision: Union[str, None] = '62d783428d52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Empty migration - pending_uploads table already exists from earlier migration."""
    # The pending_uploads table was already created in the add_pending_uploads_table migration
    # This migration is kept for version tracking but performs no operations
    pass


def downgrade() -> None:
    pass
