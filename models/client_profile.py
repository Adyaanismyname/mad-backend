from sqlalchemy import Column, String, DateTime, Date, DECIMAL, ForeignKey, Text, Enum, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base
import enum

class FitnessLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ClientProfile(Base):
    __tablename__ = "client_profiles"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Profile Fields
    date_of_birth = Column(Date, nullable=True)
    height_cm = Column(DECIMAL(5, 2), nullable=True)
    weight_kg = Column(DECIMAL(5, 2), nullable=True)
    fitness_goal = Column(String, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    fitness_level = Column(Enum(FitnessLevel, name="fitness_level_enum"), nullable=True)
    injuries = Column(ARRAY(Text), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="client_profile")
    
    def __repr__(self):
        return f"<ClientProfile(id={self.id}, user_id={self.user_id}, fitness_level={self.fitness_level})>"