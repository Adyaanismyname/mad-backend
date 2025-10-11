from sqlalchemy import Column, DateTime, ForeignKey, Text, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class MediaUpload(Base):
    __tablename__ = "media_uploads"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    client_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_workout_id = Column(UUID(as_uuid=True), ForeignKey("assigned_workouts.id"), nullable=True)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.id"), nullable=False)
    
    # Media Fields
    media_url = Column(Text, nullable=False)
    media_type = Column(String, nullable=False)  # e.g., "video", "image"
    status = Column(String, nullable=True)  # e.g., "processing", "ready", "failed"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    client_user = relationship("User", back_populates="media_uploads")
    assigned_workout = relationship("AssignedWorkout", back_populates="media_uploads")
    exercise = relationship("Exercise", back_populates="media_uploads")
    feedback = relationship("Feedback", back_populates="media", cascade="all, delete-orphan")
    pose_analysis = relationship("PoseAnalysis", back_populates="media", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MediaUpload(id={self.id}, client_id={self.client_user_id}, exercise_id={self.exercise_id}, type={self.media_type})>"