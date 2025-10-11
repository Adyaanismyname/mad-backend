from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class Workout(Base):
    __tablename__ = "workouts"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Key
    coach_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Workout Fields
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    difficulty_level = Column(String, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    category = Column(String, nullable=True)
    is_template = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    coach = relationship("User", back_populates="created_workouts")
    workout_exercises = relationship("WorkoutExercise", back_populates="workout", cascade="all, delete-orphan")
    assigned_workouts = relationship("AssignedWorkout", back_populates="workout", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workout(id={self.id}, name='{self.name}', coach_id={self.coach_id}, is_template={self.is_template})>"