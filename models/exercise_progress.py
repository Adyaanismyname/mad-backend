from sqlalchemy import DateTime, Date, Integer, DECIMAL, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
import uuid

class ExerciseProgress(Base):
    __tablename__ = "exercise_progress"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercises.id"))
    assigned_workout_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("assigned_workouts.id"), nullable=True)
    
    # Progress Fields
    recorded_date: Mapped[date] = mapped_column(Date)
    sets_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reps_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_used: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rpe: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3, 1), nullable=True)  # Rate of Perceived Exertion (1-10)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("User", back_populates="exercise_progress")
    exercise = relationship("Exercise", back_populates="exercise_progress")
    assigned_workout = relationship("AssignedWorkout", back_populates="exercise_progress")
    
    def __repr__(self):
        return f"<ExerciseProgress(id={self.id}, client_id={self.client_id}, exercise_id={self.exercise_id}, date={self.recorded_date})>"