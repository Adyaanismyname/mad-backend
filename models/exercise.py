from sqlalchemy import Column, String, DateTime, Text, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class Exercise(Base):
    __tablename__ = "exercises"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Exercise Fields
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    muscle_group = Column(ARRAY(Text), nullable=True)
    instructions = Column(Text, nullable=True)
    demo_video_url = Column(Text, nullable=True)
    difficulty = Column(String, nullable=True)
    equipment_needed = Column(ARRAY(Text), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    workout_exercises = relationship("WorkoutExercise", back_populates="exercise", cascade="all, delete-orphan")
    media_uploads = relationship("MediaUpload", back_populates="exercise", cascade="all, delete-orphan")
    exercise_progress = relationship("ExerciseProgress", back_populates="exercise", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Exercise(id={self.id}, name='{self.name}', category='{self.category}')>"