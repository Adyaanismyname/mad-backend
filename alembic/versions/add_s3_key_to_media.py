"""Add s3_key column to media_uploads table

Revision ID: add_s3_key_to_media
Revises: 67dc62723a33
Create Date: 2025-11-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_s3_key_to_media'
down_revision: Union[str, None] = '67dc62723a33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add s3_key column to media_uploads table."""
    op.add_column('media_uploads', sa.Column('s3_key', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove s3_key column from media_uploads table."""
    op.drop_column('media_uploads', 's3_key')
