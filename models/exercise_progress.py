from sqlalchemy import Column, DateTime, Date, Integer, DECIMAL, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class ExerciseProgress(Base):
    __tablename__ = "exercise_progress"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.id"), nullable=False)
    assigned_workout_id = Column(UUID(as_uuid=True), ForeignKey("assigned_workouts.id"), nullable=True)
    
    # Progress Fields
    recorded_date = Column(Date, nullable=False)
    sets_completed = Column(Integer, nullable=True)
    reps_completed = Column(Integer, nullable=True)
    weight_used = Column(DECIMAL(5, 2), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    rpe = Column(DECIMAL(3, 1), nullable=True)  # Rate of Perceived Exertion (1-10)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    client = relationship("User", back_populates="exercise_progress")
    exercise = relationship("Exercise", back_populates="exercise_progress")
    assigned_workout = relationship("AssignedWorkout", back_populates="exercise_progress")
    
    def __repr__(self):
        return f"<ExerciseProgress(id={self.id}, client_id={self.client_id}, exercise_id={self.exercise_id}, date={self.recorded_date})>"