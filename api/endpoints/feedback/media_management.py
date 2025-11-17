from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from schemas.feedbackSchema import MediaUploadResponse
from schemas.core import StandardResponse
from core.auth import verify_user_token
from core.s3_service import get_s3_service
from models.media_upload import MediaUpload
from models.user import User, UserRole
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_client_relationship
import logging

logger = logging.getLogger(__name__)

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
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
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
    
    This will delete both the database record and the file from S3.
    
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
        
        # Delete from S3 if s3_key exists
        if media.s3_key:
            try:
                s3_service = get_s3_service()
                s3_service.delete_file(media.s3_key)
                logger.info(f"Deleted S3 file: {media.s3_key}")
            except Exception as e:
                logger.error(f"Failed to delete S3 file {media.s3_key}: {str(e)}")
                # Continue with database deletion even if S3 deletion fails
                # Consider implementing a cleanup job for orphaned S3 files
        
        # Delete from database
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


@router.post("/{media_id}/generate-download-url", response_model=StandardResponse)
async def generate_media_download_url(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a temporary download URL for a media file.
    
    Useful for private media files. Returns a presigned URL that expires after 1 hour.
    
    Clients can access their own media. Coaches can access their clients' media.
    
    Returns: {
        "data": {
            "download_url": "https://...",
            "expires_in_seconds": 3600
        },
        "message": "Download URL generated"
    }
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
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Client can access their own media
        if media.client_user_id == user_id:
            pass
        # Coach can access media from their clients
        elif user.role in [UserRole.COACH, UserRole.BOTH]:
            await verify_coach_client_relationship(user_id, media.client_user_id, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this media"
            )
        
        # Generate presigned download URL
        if not media.s3_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Media file does not have an S3 key"
            )
        
        s3_service = get_s3_service()
        download_url = s3_service.generate_presigned_download_url(media.s3_key)
        
        return StandardResponse(
            data={
                "download_url": download_url,
                "expires_in_seconds": 3600
            },
            message="Download URL generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
