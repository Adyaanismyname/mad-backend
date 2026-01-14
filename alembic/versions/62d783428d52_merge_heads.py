"""merge heads

Revision ID: 62d783428d52
Revises: 14bf7fa87b73, add_pose_data_to_media
Create Date: 2026-01-14 17:52:11.643548

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62d783428d52'
down_revision: Union[str, None] = ('14bf7fa87b73', 'add_pose_data_to_media')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
