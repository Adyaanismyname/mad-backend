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
    """Create pending_uploads table."""
    op.create_table(
        'pending_uploads',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('s3_key', sa.Text(), nullable=False),
        sa.Column('media_url', sa.Text(), nullable=False),
        sa.Column('media_type', sa.String(length=10), nullable=False),
        sa.Column('exercise_id', UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_workout_id', UUID(as_uuid=True), nullable=True),
        sa.Column('upload_metadata', JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), server_default=sa.text("'pending'"), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for performance
    op.create_index(op.f('ix_pending_uploads_id'), 'pending_uploads', ['id'], unique=False)
    op.create_index(op.f('ix_pending_uploads_user_id'), 'pending_uploads', ['user_id'], unique=False)
    op.create_index(op.f('ix_pending_uploads_created_at'), 'pending_uploads', ['created_at'], unique=False)
    op.create_index(op.f('ix_pending_uploads_expires_at'), 'pending_uploads', ['expires_at'], unique=False)
    
    # Create composite index for cleanup queries
    op.create_index(
        'ix_pending_uploads_cleanup',
        'pending_uploads',
        ['expires_at', 'status'],
        unique=False
    )


def downgrade() -> None:
    pass
