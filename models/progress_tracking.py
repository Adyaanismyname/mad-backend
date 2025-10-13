from sqlalchemy import DateTime, Date, DECIMAL, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from typing import Optional, List, Any
from datetime import datetime, date
from decimal import Decimal
import uuid

class ProgressTracking(Base):
    __tablename__ = "progress_tracking"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    client_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    coach_client_relationship_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("coach_client_relationships.id"), nullable=True)
    
    # Progress Fields
    tracking_date: Mapped[date] = mapped_column(Date)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2), nullable=True)
    body_fat_percentage: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2), nullable=True)
    measurements: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)  # e.g., {"chest": 42.5, "waist": 32.0, "bicep": 15.5}
    photo_urls: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client_user = relationship("User", back_populates="progress_tracking")
    coach_client_relationship = relationship("CoachClientRelationship", back_populates="progress_tracking")
    
    def __repr__(self):
        return f"<ProgressTracking(id={self.id}, client_id={self.client_user_id}, date={self.tracking_date})>"