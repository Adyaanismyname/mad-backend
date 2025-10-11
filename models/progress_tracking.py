from sqlalchemy import Column, DateTime, Date, DECIMAL, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class ProgressTracking(Base):
    __tablename__ = "progress_tracking"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Keys
    client_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    coach_client_relationship_id = Column(UUID(as_uuid=True), ForeignKey("coach_client_relationships.id"), nullable=True)
    
    # Progress Fields
    tracking_date = Column(Date, nullable=False)
    weight_kg = Column(DECIMAL(5, 2), nullable=True)
    body_fat_percentage = Column(DECIMAL(5, 2), nullable=True)
    measurements = Column(JSONB, nullable=True)  # e.g., {"chest": 42.5, "waist": 32.0, "bicep": 15.5}
    photo_urls = Column(ARRAY(Text), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    client_user = relationship("User", back_populates="progress_tracking")
    coach_client_relationship = relationship("CoachClientRelationship", back_populates="progress_tracking")
    
    def __repr__(self):
        return f"<ProgressTracking(id={self.id}, client_id={self.client_user_id}, date={self.tracking_date})>"