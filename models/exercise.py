from sqlalchemy import String, DateTime, Text, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from typing import Optional, List
from datetime import datetime
import uuid

class Exercise(Base):
    __tablename__ = "exercises"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Exercise Fields
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    muscle_group: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    demo_video_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    equipment_needed: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    workout_exercises = relationship("WorkoutExercise", back_populates="exercise", cascade="all, delete-orphan")
    media_uploads = relationship("MediaUpload", back_populates="exercise", cascade="all, delete-orphan")
    exercise_progress = relationship("ExerciseProgress", back_populates="exercise", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Exercise(id={self.id}, name='{self.name}', category='{self.category}')>"