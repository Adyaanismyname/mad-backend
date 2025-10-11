from sqlalchemy import Column, String, DateTime, Enum, text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
import enum

class UserRole(enum.Enum):
    COACH = "coach"
    CLIENT = "client"
    BOTH = "both"

class User(Base):
    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Core Fields
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.CLIENT)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    profile_picture_url = Column(String, nullable=True)

    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
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

