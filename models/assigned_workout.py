from sqlalchemy import Column, DateTime, Date, DECIMAL, ForeignKey, Text, Enum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
import enum

class AssignmentStatus(enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class AssignedWorkout(Base):
    __tablename__ = "assigned_workouts"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    workout_id = Column(UUID(as_uuid=True), ForeignKey("workouts.id"), nullable=False)
    coach_client_relationship_id = Column(UUID(as_uuid=True), ForeignKey("coach_client_relationships.id"), nullable=False)
    coach_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Assignment Fields
    assigned_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(Enum(AssignmentStatus, name="assignment_status_enum"), nullable=False, default=AssignmentStatus.ASSIGNED)
    coach_notes = Column(Text, nullable=True)
    client_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    workout = relationship("Workout", back_populates="assigned_workouts")
    coach_client_relationship = relationship("CoachClientRelationship", back_populates="assigned_workouts")
    coach = relationship("User", foreign_keys=[coach_user_id], back_populates="assigned_workouts_as_coach")
    client = relationship("User", foreign_keys=[client_user_id], back_populates="assigned_workouts_as_client")
    media_uploads = relationship("MediaUpload", back_populates="assigned_workout", cascade="all, delete-orphan")
    exercise_progress = relationship("ExerciseProgress", back_populates="assigned_workout", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AssignedWorkout(id={self.id}, workout_id={self.workout_id}, client_id={self.client_user_id}, status={self.status.value})>"