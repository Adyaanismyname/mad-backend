from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, List
from datetime import datetime
from uuid import UUID

# ============= Media Upload Schemas =============

class MediaUploadCreate(BaseModel):
    """Schema for creating a media upload."""
    assigned_workout_id: Optional[UUID] = None
    exercise_id: UUID
    media_url: str = Field(..., min_length=1)
    media_type: str = Field(..., pattern="^(video|image)$")


class MediaUploadInitiate(BaseModel):
    """Schema for initiating a presigned upload URL."""
    assigned_workout_id: Optional[UUID] = None
    exercise_id: UUID
    filename: str = Field(..., min_length=1, max_length=255)
    media_type: str = Field(..., pattern="^(video|image)$")
    file_size_mb: float = Field(..., gt=0, description="File size in megabytes")


class PresignedUploadResponse(BaseModel):
    """Response schema for presigned upload URL."""
    upload_url: str = Field(..., description="Presigned URL for uploading file")
    content_type: str = Field(..., description="Content type to use in upload request")
    expires_at: str = Field(..., description="ISO timestamp when URL expires")
    upload_id: UUID = Field(..., description="Temporary ID to confirm upload")


class MediaUploadConfirm(BaseModel):
    """Schema for confirming a successful upload."""
    upload_id: UUID = Field(..., description="ID from presigned upload response")
    assigned_workout_id: Optional[UUID] = None
    exercise_id: UUID


class MediaUploadResponse(BaseModel):
    """Response schema for media upload."""
    id: UUID
    client_user_id: UUID
    assigned_workout_id: Optional[UUID] = None
    exercise_id: UUID
    presigned_url: Optional[str] = Field(None, description="Presigned URL for secure media access (expires in 1 hour)")
    media_type: str
    status: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============= Feedback Schemas =============

class FeedbackCreate(BaseModel):
    """Schema for creating feedback on media."""
    content: str = Field(..., min_length=1, max_length=5000)
    annotation_data: Optional[Any] = None  # JSON data for timestamps, coordinates, etc.
    parent_feedback_id: Optional[UUID] = None  # For threaded replies


class FeedbackUpdate(BaseModel):
    """Schema for updating existing feedback."""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    annotation_data: Optional[Any] = None


class FeedbackResponse(BaseModel):
    """Response schema for feedback."""
    id: UUID
    media_id: UUID
    coach_user_id: UUID
    parent_feedback_id: Optional[UUID] = None
    content: str
    annotation_data: Optional[Any] = None
    created_at: datetime
    updated_at: datetime
    coach_name: Optional[str] = None  # Added for convenience
    replies: List["FeedbackResponse"] = Field(default_factory=list)  # Nested replies
    
    model_config = ConfigDict(from_attributes=True)


# Allow forward references for nested replies
FeedbackResponse.model_rebuild()


# ============= Media with Feedback Schemas =============

class MediaWithFeedbackResponse(BaseModel):
    """Response schema for media with its feedback."""
    id: UUID
    client_user_id: UUID
    assigned_workout_id: Optional[UUID] = None
    exercise_id: UUID
    presigned_url: Optional[str] = Field(None, description="Presigned URL for secure media access (expires in 1 hour)")
    media_type: str
    status: Optional[str] = None
    created_at: datetime
    feedback: List[FeedbackResponse] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)
