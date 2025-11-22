from sqlalchemy import DateTime, ForeignKey, Text, String, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from datetime import datetime
import uuid


class PendingUpload(Base):
    """
    Temporary storage for media uploads in progress.
    
    This table stores metadata for uploads that have been initiated but not yet confirmed.
    Records are automatically cleaned up after expiration using a scheduled job or trigger.
    
    Security Features:
    - User ownership verification
    - Expiration timestamp for automatic cleanup
    - Immutable after creation (no updates allowed)
    - Audit trail of upload attempts
    """
    __tablename__ = "pending_uploads"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True
    )
    
    # Foreign Key - User who initiated the upload
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # S3 Metadata
    s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'image' or 'video'
    
    # Upload Context (optional metadata for audit/debugging)
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    assigned_workout_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Additional metadata (JSON for flexibility) - renamed to avoid conflict with SQLAlchemy's metadata
    upload_metadata: Mapped[dict] = mapped_column(JSONB, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        index=True  # Index for efficient cleanup queries
    )
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        default='pending',
        server_default=text("'pending'")
    )  # 'pending', 'confirmed', 'expired', 'failed'
    
    # Soft delete (optional - for audit trail)
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    def __repr__(self):
        return f"<PendingUpload(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    def is_expired(self) -> bool:
        """Check if this pending upload has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if this pending upload is still valid for confirmation."""
        return (
            self.status == 'pending' and 
            not self.is_expired() and 
            self.deleted_at is None
        )
