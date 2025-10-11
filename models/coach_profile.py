from sqlalchemy import Column, String, DateTime, Integer, Boolean, DECIMAL, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class CoachProfile(Base):
    __tablename__ = "coach_profiles"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Profile Fields
    specializations = Column(ARRAY(Text), nullable=True)
    certifications = Column(ARRAY(Text), nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    base_hourly_rate = Column(DECIMAL(10, 2), nullable=True)
    accepting_clients = Column(Boolean, default=True, nullable=False)
    max_clients = Column(Integer, nullable=True)
    availability_schedule = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="coach_profile")
    
    def __repr__(self):
        return f"<CoachProfile(id={self.id}, user_id={self.user_id}, accepting_clients={self.accepting_clients})>"