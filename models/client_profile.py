from sqlalchemy import String, DateTime, Date, DECIMAL, ForeignKey, Text, Enum, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
import enum
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
import uuid

class FitnessLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ClientProfile(Base):
    __tablename__ = "client_profiles"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Key
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    
    # Profile Fields
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    height_cm: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2), nullable=True)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2), nullable=True)
    fitness_goal: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    medical_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fitness_level: Mapped[Optional[FitnessLevel]] = mapped_column(Enum(FitnessLevel, name="fitness_level_enum"), nullable=True)
    injuries: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="client_profile")
    
    def __repr__(self):
        return f"<ClientProfile(id={self.id}, user_id={self.user_id}, fitness_level={self.fitness_level})>"