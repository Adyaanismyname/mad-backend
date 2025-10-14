from sqlalchemy import DateTime, Integer, Boolean, DECIMAL, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import uuid

class CoachProfile(Base):
    __tablename__ = "coach_profiles"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Key
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    
    # Profile Fields
    specializations: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    certifications: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_hourly_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    accepting_clients: Mapped[bool] = mapped_column(Boolean, default=True)
    max_clients: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    availability_schedule: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="coach_profile")
    
    def __repr__(self):
        return f"<CoachProfile(id={self.id}, user_id={self.user_id}, accepting_clients={self.accepting_clients})>"