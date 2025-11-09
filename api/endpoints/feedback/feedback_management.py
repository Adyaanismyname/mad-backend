from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from db.session import get_db
from schemas.feedbackSchema import FeedbackUpdate, FeedbackResponse
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.feedback import Feedback
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role
from api.endpoints.feedback.serializers import serialize_feedback

router = APIRouter()


@router.put("/{feedback_id}", response_model=StandardResponse)
async def update_feedback(
    feedback_id: UUID,
    feedback_data: FeedbackUpdate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Update existing feedback (Coach who created it only).
    
    Returns: {"data": {feedback_data}, "message": "Feedback updated successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        await verify_coach_role(coach_user_id, db)
        
        result = await db.execute(select(Feedback).filter(Feedback.id == feedback_id))
        feedback = result.scalar_one_or_none()
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        if feedback.coach_user_id != coach_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this feedback"
            )
        
        # Update fields
        update_data = feedback_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feedback, field, value)
        
        await db.commit()
        await db.refresh(feedback)
        
        # Fetch with coach details
        result = await db.execute(
            select(Feedback).options(
                joinedload(Feedback.coach)
            ).filter(Feedback.id == feedback_id)
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
            message="Feedback updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/{feedback_id}", response_model=StandardResponse)
async def delete_feedback(
    feedback_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete feedback (Coach who created it only).
    
    Also deletes any nested replies.
    
    Returns: {"data": {}, "message": "Feedback deleted successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        await verify_coach_role(coach_user_id, db)
        
        result = await db.execute(select(Feedback).filter(Feedback.id == feedback_id))
        feedback = result.scalar_one_or_none()
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        if feedback.coach_user_id != coach_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this feedback"
            )
        
        await db.delete(feedback)
        await db.commit()
        
        return StandardResponse(
            data={},
            message="Feedback deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
