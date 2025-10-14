from sqlalchemy import DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from typing import Optional, Any
from datetime import datetime
import uuid

class Feedback(Base):
    __tablename__ = "feedback"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    media_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("media_uploads.id"))
    coach_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    parent_feedback_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("feedback.id"), nullable=True)  # For threaded feedback
    
    # Feedback Fields
    content: Mapped[str] = mapped_column(Text)
    annotation_data: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)  # For storing timestamps, coordinates, etc.
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    media = relationship("MediaUpload", back_populates="feedback")
    coach = relationship("User", back_populates="feedback_given")
    parent_feedback = relationship("Feedback", remote_side=[id], backref="replies")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, media_id={self.media_id}, coach_id={self.coach_user_id})>"