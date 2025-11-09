from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from db.session import get_db
from schemas.feedbackSchema import FeedbackCreate, FeedbackResponse
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.media_upload import MediaUpload
from models.feedback import Feedback
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role, verify_coach_client_relationship
from api.endpoints.feedback.serializers import serialize_feedback

router = APIRouter(prefix="/media")


@router.post("/{media_id}/feedback", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    media_id: UUID,
    feedback_data: FeedbackCreate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
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
        await verify_coach_role(coach_user_id, db)
        
        # Verify media exists and coach has relationship with client
        result = await db.execute(select(MediaUpload).filter(MediaUpload.id == media_id))
        media = result.scalar_one_or_none()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Verify coach-client relationship
        await verify_coach_client_relationship(coach_user_id, media.client_user_id, db)
        
        # Verify parent feedback if provided
        if feedback_data.parent_feedback_id:
            result = await db.execute(
                select(Feedback).filter(
                    Feedback.id == feedback_data.parent_feedback_id,
                    Feedback.media_id == media_id
                )
            )
            parent = result.scalar_one_or_none()
            
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
        await db.commit()
        await db.refresh(feedback)
        
        # Fetch with coach details
        result = await db.execute(
            select(Feedback).options(
                joinedload(Feedback.coach)
            ).filter(Feedback.id == feedback.id)
        )
        feedback_with_coach = result.scalar_one_or_none()
        if not feedback_with_coach:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )

        response_dict = serialize_feedback(feedback_with_coach)
        response = FeedbackResponse(**response_dict)
        return StandardResponse(
            data=response.model_dump(),
            message="Feedback created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

