from sqlalchemy import Column, String, DateTime, Date, Boolean, DECIMAL, ForeignKey, Text, Enum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
import enum

class RelationshipStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"

class CoachClientRelationship(Base):
    __tablename__ = "coach_client_relationships"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    coach_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationship Fields
    status = Column(Enum(RelationshipStatus, name="relationship_status_enum"), nullable=False, default=RelationshipStatus.PENDING)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    coach = relationship("User", foreign_keys=[coach_user_id], back_populates="coached_relationships")
    client = relationship("User", foreign_keys=[client_user_id], back_populates="client_relationships")
    assigned_workouts = relationship("AssignedWorkout", back_populates="coach_client_relationship", cascade="all, delete-orphan")
    progress_tracking = relationship("ProgressTracking", back_populates="coach_client_relationship", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CoachClientRelationship(id={self.id}, coach_id={self.coach_user_id}, client_id={self.client_user_id}, status={self.status.value})>"