"""Add pose_data and pose_analysis_status to media_uploads

Revision ID: add_pose_data_to_media
Revises: add_s3_key_to_media
Create Date: 2026-01-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_pose_data_to_media'
down_revision: Union[str, None] = 'add_s3_key_to_media'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pose_data column (JSONB for storing pose keypoints per frame)
    op.add_column(
        'media_uploads',
        sa.Column('pose_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    
    # Add pose_analysis_status column for tracking processing state
    op.add_column(
        'media_uploads',
        sa.Column('pose_analysis_status', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('media_uploads', 'pose_analysis_status')
    op.drop_column('media_uploads', 'pose_data')
