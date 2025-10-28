from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from db.session import get_db
from schemas.feedbackSchema import (
    MediaUploadCreate, MediaUploadResponse,
    FeedbackCreate, FeedbackUpdate, FeedbackResponse,
    MediaWithFeedbackResponse
)
from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus

from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.media_upload import MediaUpload
from models.feedback import Feedback
from models.assigned_workout import AssignedWorkout
from models.user import User, UserRole
from typing import Optional
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role, verify_coach_client_relationship

router = APIRouter()


@router.post("/media/{media_id}/feedback", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    media_id: UUID,
    feedback_data: FeedbackCreate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    FR-5.1: Create feedback/comment on client-uploaded media (Coach only).
    
    Coaches can provide feedback with optional annotations (timestamps, coordinates, etc.).
    Supports threaded replies via parent_feedback_id.
    
    Returns: {"data": {feedback_data}, "message": "Feedback created successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        # Verify media exists and coach has relationship with client
        media = db.query(MediaUpload).filter(MediaUpload.id == media_id).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Verify coach-client relationship
        verify_coach_client_relationship(coach_user_id, media.client_user_id, db)
        
        # Verify parent feedback if provided
        if feedback_data.parent_feedback_id:
            parent = db.query(Feedback).filter(
                Feedback.id == feedback_data.parent_feedback_id,
                Feedback.media_id == media_id
            ).first()
            
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent feedback not found"
                )
        
        # Create feedback
        feedback = Feedback(
            media_id=media_id,
            coach_user_id=coach_user_id,
            parent_feedback_id=feedback_data.parent_feedback_id,
            content=feedback_data.content,
            annotation_data=feedback_data.annotation_data
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        # Fetch with coach details
        feedback = db.query(Feedback).options(
            joinedload(Feedback.coach)
        ).filter(Feedback.id == feedback.id).first()
        
        # Build response with coach name
        response_data = FeedbackResponse.model_validate(feedback)
        response_dict = response_data.model_dump()
        response_dict["coach_name"] = feedback.coach.full_name if feedback.coach else None
        
        return StandardResponse(
            data=response_dict,
            message="Feedback created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

