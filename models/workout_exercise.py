from sqlalchemy import DateTime, Integer, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from typing import Optional
from datetime import datetime
import uuid

class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    workout_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workouts.id"))
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercises.id"))
    
    # Exercise Configuration
    order_index: Mapped[int] = mapped_column(Integer)
    sets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rest_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    workout = relationship("Workout", back_populates="workout_exercises")
    exercise = relationship("Exercise", back_populates="workout_exercises")
    
    def __repr__(self):
        return f"<WorkoutExercise(id={self.id}, workout_id={self.workout_id}, exercise_id={self.exercise_id}, order={self.order_index})>"