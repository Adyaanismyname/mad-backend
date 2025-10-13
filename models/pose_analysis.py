from sqlalchemy import DateTime, ForeignKey, DECIMAL, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from db.base import Base
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
import uuid

class PoseAnalysis(Base):
    __tablename__ = "pose_analysis"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Key
    media_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("media_uploads.id"))
    
    # Analysis Fields
    analysis_data: Mapped[Any] = mapped_column(JSONB)  # AI analysis results
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(3, 2), nullable=True)  # 0.00 to 1.00
    keypoints: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)  # Pose keypoints data
    form_feedback: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)  # Automated form feedback
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    media = relationship("MediaUpload", back_populates="pose_analysis")
    
    def __repr__(self):
        return f"<PoseAnalysis(id={self.id}, media_id={self.media_id}, confidence={self.confidence_score})>"