from sqlalchemy import Column, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class Feedback(Base):
    __tablename__ = "feedback"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    media_id = Column(UUID(as_uuid=True), ForeignKey("media_uploads.id"), nullable=False)
    coach_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parent_feedback_id = Column(UUID(as_uuid=True), ForeignKey("feedback.id"), nullable=True)  # For threaded feedback
    
    # Feedback Fields
    content = Column(Text, nullable=False)
    annotation_data = Column(JSONB, nullable=True)  # For storing timestamps, coordinates, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    media = relationship("MediaUpload", back_populates="feedback")
    coach = relationship("User", back_populates="feedback_given")
    parent_feedback = relationship("Feedback", remote_side=[id], backref="replies")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, media_id={self.media_id}, coach_id={self.coach_user_id})>"