from sqlalchemy import DateTime, ForeignKey, Enum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
import enum
from datetime import datetime
import uuid

class RelationshipStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    TERMINATED = "terminated"

class CoachClientRelationship(Base):
    __tablename__ = "coach_client_relationships"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    coach_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    client_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationship Fields
    status: Mapped[RelationshipStatus] = mapped_column(Enum(RelationshipStatus, name="relationship_status_enum"), default=RelationshipStatus.PENDING)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    coach = relationship("User", foreign_keys=[coach_user_id], back_populates="coached_relationships")
    client = relationship("User", foreign_keys=[client_user_id], back_populates="client_relationships")
    assigned_workouts = relationship("AssignedWorkout", back_populates="coach_client_relationship", cascade="all, delete-orphan")
    progress_tracking = relationship("ProgressTracking", back_populates="coach_client_relationship", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CoachClientRelationship(id={self.id}, coach_id={self.coach_user_id}, client_id={self.client_user_id}, status={self.status.value})>"