from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from db.session import get_db
from schemas.feedbackSchema import MediaWithFeedbackResponse
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.media_upload import MediaUpload
from models.feedback import Feedback
from models.user import User, UserRole
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_client_relationship
from api.endpoints.feedback.serializers import serialize_feedback

router = APIRouter(prefix="/media")



@router.get("/{media_id}/feedback", response_model=StandardResponse)
async def get_media_feedback(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    FR-5.2: Get all feedback for a specific media upload.
    
    Returns feedback in a hierarchical structure with replies.
    Client can view feedback on their media. Coach can view feedback on their clients' media.
    
    Returns: {"data": [feedback_list], "message": "Feedback retrieved successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        user_id = UUID(str(current_user.get("user_id")))
        
        # Verify media exists and user has access
        result = await db.execute(select(MediaUpload).filter(MediaUpload.id == media_id))
        media = result.scalar_one_or_none()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Check authorization
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Client can view feedback on their own media
        if media.client_user_id == user_id:
            pass
        # Coach can view feedback on their clients' media
        elif user.role in [UserRole.COACH, UserRole.BOTH]:
            await verify_coach_client_relationship(user_id, media.client_user_id, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view feedback on this media"
            )
        
        # Get all feedback for this media (with coach details)
        result = await db.execute(
            select(Feedback).options(
                joinedload(Feedback.coach)
            ).filter(Feedback.media_id == media_id).order_by(Feedback.created_at.asc())
        )
        all_feedback = result.scalars().all()
        
        # Build hierarchical structure
        feedback_map = {}
        root_feedback = []
        
        for fb in all_feedback:
            fb_dict = serialize_feedback(fb)
            feedback_map[fb.id] = fb_dict
        
        for fb in all_feedback:
            fb_dict = feedback_map[fb.id]
            if fb.parent_feedback_id and fb.parent_feedback_id in feedback_map:
                feedback_map[fb.parent_feedback_id]["replies"].append(fb_dict)
            else:
                root_feedback.append(fb_dict)
        
        return StandardResponse(
            data=root_feedback,
            message="Feedback retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/{media_id}/with-feedback", response_model=StandardResponse)
async def get_media_with_feedback(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    FR-5.2: Get media upload with all associated feedback in one response.
    
    Returns: {"data": {media_with_feedback}, "message": "Media with feedback retrieved"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        user_id = UUID(str(current_user.get("user_id")))
        
        # Verify media exists and load with feedback
        result = await db.execute(
            select(MediaUpload).options(
                joinedload(MediaUpload.feedback).joinedload(Feedback.coach)
            ).filter(MediaUpload.id == media_id)
        )
        media = result.unique().scalar_one_or_none()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Check authorization
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if media.client_user_id == user_id:
            pass
        elif user.role in [UserRole.COACH, UserRole.BOTH]:
            await verify_coach_client_relationship(user_id, media.client_user_id, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this media"
            )
        
        # Build response with hierarchical feedback
        feedback_map = {}
        root_feedback = []
        
        for fb in media.feedback:
            fb_dict = serialize_feedback(fb)
            feedback_map[fb.id] = fb_dict
        
        for fb in media.feedback:
            fb_dict = feedback_map[fb.id]
            if fb.parent_feedback_id and fb.parent_feedback_id in feedback_map:
                feedback_map[fb.parent_feedback_id]["replies"].append(fb_dict)
            else:
                root_feedback.append(fb_dict)
        
        # Generate presigned URL for secure access
        from core.s3_service import get_s3_service
        import logging
        logger = logging.getLogger(__name__)
        s3_service = get_s3_service()
        presigned_url = None
        if media.s3_key:
            try:
                presigned_url = s3_service.generate_presigned_download_url(
                    s3_key=media.s3_key,
                    expires_in=3600  # 1 hour
                )
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for media {media.id}: {e}")
        
        # Create media response
        media_response = MediaWithFeedbackResponse(
            id=media.id,
            client_user_id=media.client_user_id,
            assigned_workout_id=media.assigned_workout_id,
            exercise_id=media.exercise_id,
            presigned_url=presigned_url,
            media_type=media.media_type,
            status=media.status,
            created_at=media.created_at,
            feedback=root_feedback
        )
        
        return StandardResponse(
            data=media_response.model_dump(),
            message="Media with feedback retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
