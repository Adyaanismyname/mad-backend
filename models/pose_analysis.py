from sqlalchemy import Column, DateTime, ForeignKey, DECIMAL, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base

class PoseAnalysis(Base):
    __tablename__ = "pose_analysis"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    
    # Foreign Key
    media_id = Column(UUID(as_uuid=True), ForeignKey("media_uploads.id"), nullable=False)
    
    # Analysis Fields
    analysis_data = Column(JSONB, nullable=False)  # AI analysis results
    confidence_score = Column(DECIMAL(3, 2), nullable=True)  # 0.00 to 1.00
    keypoints = Column(JSONB, nullable=True)  # Pose keypoints data
    form_feedback = Column(JSONB, nullable=True)  # Automated form feedback
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    media = relationship("MediaUpload", back_populates="pose_analysis")
    
    def __repr__(self):
        return f"<PoseAnalysis(id={self.id}, media_id={self.media_id}, confidence={self.confidence_score})>"