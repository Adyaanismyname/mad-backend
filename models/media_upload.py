from sqlalchemy import DateTime, ForeignKey, Text, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from typing import Optional
from datetime import datetime
import uuid

class MediaUpload(Base):
    __tablename__ = "media_uploads"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    client_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_workout_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("assigned_workouts.id"), nullable=True)
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercises.id"))
    
    # Media Fields
    media_url: Mapped[str] = mapped_column(Text)
    s3_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # S3 object key for file operations
    media_type: Mapped[str] = mapped_column(String)  # e.g., "video", "image"
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g., "processing", "ready", "failed"
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client_user = relationship("User", back_populates="media_uploads")
    assigned_workout = relationship("AssignedWorkout", back_populates="media_uploads")
    exercise = relationship("Exercise", back_populates="media_uploads")
    feedback = relationship("Feedback", back_populates="media", cascade="all, delete-orphan")
    pose_analysis = relationship("PoseAnalysis", back_populates="media", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MediaUpload(id={self.id}, client_id={self.client_user_id}, exercise_id={self.exercise_id}, type={self.media_type})>"