from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from typing import Optional
from datetime import datetime
import uuid

class Workout(Base):
    __tablename__ = "workouts"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Key
    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Workout Fields
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    coach = relationship("User", back_populates="created_workouts")
    workout_exercises = relationship("WorkoutExercise", back_populates="workout", cascade="all, delete-orphan")
    assigned_workouts = relationship("AssignedWorkout", back_populates="workout", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workout(id={self.id}, name='{self.name}', coach_id={self.coach_id}, is_template={self.is_template})>"