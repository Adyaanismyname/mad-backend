from sqlalchemy import DateTime, Date, ForeignKey, Text, Enum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
import enum
from typing import Optional
from datetime import datetime, date
import uuid

class AssignmentStatus(enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class AssignedWorkout(Base):
    __tablename__ = "assigned_workouts"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    workout_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workouts.id"))
    coach_client_relationship_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("coach_client_relationships.id"))
    coach_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    client_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Assignment Fields
    assigned_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[AssignmentStatus] = mapped_column(Enum(AssignmentStatus, name="assignment_status_enum"), default=AssignmentStatus.ASSIGNED)
    coach_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    client_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    workout = relationship("Workout", back_populates="assigned_workouts")
    coach_client_relationship = relationship("CoachClientRelationship", back_populates="assigned_workouts")
    coach = relationship("User", foreign_keys=[coach_user_id], back_populates="assigned_workouts_as_coach")
    client = relationship("User", foreign_keys=[client_user_id], back_populates="assigned_workouts_as_client")
    exercise_progress = relationship("ExerciseProgress", back_populates="assigned_workout", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AssignedWorkout(id={self.id}, workout_id={self.workout_id}, client_id={self.client_user_id}, status={self.status.value})>"