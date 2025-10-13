from sqlalchemy import String, DateTime, Enum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
import enum
from typing import Optional
from datetime import datetime
import uuid

class UserRole(enum.Enum):
    COACH = "coach"
    CLIENT = "client"
    BOTH = "both"

class User(Base):
    __tablename__ = "users"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Core Fields
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role_enum"), default=UserRole.CLIENT)
    full_name: Mapped[str] = mapped_column(String)
    phone_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # --- Authentication Relationships ---
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    email_verification_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    # --- Profile Relationships ---
    coach_profile = relationship("CoachProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    client_profile = relationship("ClientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # --- Coach-Client Relationships ---
    # As a coach - clients they train
    coached_relationships = relationship(
        "CoachClientRelationship", 
        foreign_keys="CoachClientRelationship.coach_user_id",
        back_populates="coach",
        cascade="all, delete-orphan"
    )
    # As a client - coaches who train them
    client_relationships = relationship(
        "CoachClientRelationship",
        foreign_keys="CoachClientRelationship.client_user_id", 
        back_populates="client",
        cascade="all, delete-orphan"
    )
    
    # --- Workout Relationships ---
    created_workouts = relationship("Workout", back_populates="coach", cascade="all, delete-orphan")
    
    # --- Assignment Relationships ---
    # As a coach - workouts they assign
    assigned_workouts_as_coach = relationship(
        "AssignedWorkout",
        foreign_keys="AssignedWorkout.coach_user_id",
        back_populates="coach",
        cascade="all, delete-orphan"
    )
    # As a client - workouts assigned to them
    assigned_workouts_as_client = relationship(
        "AssignedWorkout",
        foreign_keys="AssignedWorkout.client_user_id", 
        back_populates="client",
        cascade="all, delete-orphan"
    )
    
    # --- Media & Feedback Relationships ---
    media_uploads = relationship("MediaUpload", back_populates="client_user", cascade="all, delete-orphan")
    feedback_given = relationship("Feedback", back_populates="coach", cascade="all, delete-orphan")
    
    # --- Progress Tracking Relationships ---
    progress_tracking = relationship("ProgressTracking", back_populates="client_user", cascade="all, delete-orphan")
    exercise_progress = relationship("ExerciseProgress", back_populates="client", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}', full_name='{self.full_name}')>"

