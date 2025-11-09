from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from db.session import get_db
from schemas.feedbackSchema import MediaUploadCreate, MediaUploadResponse
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.media_upload import MediaUpload
from models.assigned_workout import AssignedWorkout
from uuid import UUID

router = APIRouter(prefix="/media")


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    media_data: MediaUploadCreate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload media (video/image) for an exercise (Client only).
    
    Clients upload media for tracking their exercise performance.
    Can be associated with an assigned workout.
    
    Returns: {"data": {media_data}, "message": "Media uploaded successfully"}
    Errors: 401 (unauthorized), 422 (validation), 500 (server error)
    """
    try:
        client_user_id = UUID(str(current_user.get("user_id")))
        
        # Verify assigned workout belongs to client if provided
        if media_data.assigned_workout_id:
            result = await db.execute(
                select(AssignedWorkout).filter(
                    AssignedWorkout.id == media_data.assigned_workout_id,
                    AssignedWorkout.client_user_id == client_user_id
                )
            )
            assigned_workout = result.scalar_one_or_none()
            
            if not assigned_workout:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Assigned workout not found or not authorized"
                )
        
        # Create media upload
        media_upload = MediaUpload(
            client_user_id=client_user_id,
            assigned_workout_id=media_data.assigned_workout_id,
            exercise_id=media_data.exercise_id,
            media_url=media_data.media_url,
            media_type=media_data.media_type,
            status="ready"
        )
        
        db.add(media_upload)
        await db.commit()
        await db.refresh(media_upload)
        
        response = MediaUploadResponse.model_validate(media_upload)
        return StandardResponse(
            data=response.model_dump(),
            message="Media uploaded successfully"
        )
        
    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid exercise or workout ID"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

