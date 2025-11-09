from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from schemas.feedbackSchema import MediaUploadResponse
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.media_upload import MediaUpload
from models.user import User, UserRole
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_client_relationship

router = APIRouter(prefix="/media")


@router.get("/{media_id}", response_model=StandardResponse)
async def get_media_details(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific media upload.
    
    Clients can view their own uploads. Coaches can view uploads from their clients.
    
    Returns: {"data": {media_data}, "message": "Media retrieved successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        user_id = UUID(str(current_user.get("user_id")))
        
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
        
        # Client can view their own media
        if media.client_user_id == user_id:
            pass
        # Coach can view media from their clients
        elif user.role in [UserRole.COACH, UserRole.BOTH]:
            await verify_coach_client_relationship(user_id, media.client_user_id, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this media"
            )
        
        response = MediaUploadResponse.model_validate(media)
        return StandardResponse(
            data=response.model_dump(),
            message="Media retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/{media_id}", response_model=StandardResponse)
async def delete_media(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a media upload (Client who uploaded it only).
    
    Returns: {"data": {}, "message": "Media deleted successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        client_user_id = UUID(str(current_user.get("user_id")))
        
        result = await db.execute(select(MediaUpload).filter(MediaUpload.id == media_id))
        media = result.scalar_one_or_none()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        if media.client_user_id != client_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this media"
            )
        
        await db.delete(media)
        await db.commit()
        
        return StandardResponse(
            data={},
            message="Media deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
