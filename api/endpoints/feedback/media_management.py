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
        
        # Generate presigned URL for secure access
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
        
        response = MediaUploadResponse.model_validate(media)
        response.presigned_url = presigned_url
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


@router.patch("/{media_id}/annotations", response_model=StandardResponse)
async def update_media_annotations(
    media_id: UUID,
    annotations_data: dict,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Update annotations for a media upload.
    
    Only the client who uploaded the media can update its annotations.
    Annotations are stored as JSONB and can contain any structured data
    (timestamps, coordinates, markers, notes, etc.).
    
    Returns: {
        "data": {updated_media_data},
        "message": "Annotations updated successfully"
    }
    Errors: 400 (invalid JSON), 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        client_user_id = UUID(str(current_user.get("user_id")))
        
        # Validate that annotations_data is provided
        if not annotations_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Annotations data is required"
            )
        
        # Validate that it's a dictionary
        if not isinstance(annotations_data, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Annotations must be a valid JSON object"
            )
        
        # Retrieve the media
        result = await db.execute(select(MediaUpload).filter(MediaUpload.id == media_id))
        media = result.scalar_one_or_none()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Only the client who uploaded the media can update annotations
        if media.client_user_id != client_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update annotations for this media"
            )
        
        # Update annotations
        media.annotations = annotations_data
        await db.commit()
        await db.refresh(media)
        
        logger.info(f"Updated annotations for media {media_id} by user {client_user_id}")
        
        # Generate presigned URL for response
        s3_service = get_s3_service()
        presigned_url = None
        if media.s3_key:
            try:
                presigned_url = s3_service.generate_presigned_download_url(
                    s3_key=media.s3_key,
                    expires_in=3600
                )
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for media {media.id}: {e}")
        
        response = MediaUploadResponse.model_validate(media)
        response.presigned_url = presigned_url
        
        return StandardResponse(
            data=response.model_dump(),
            message="Annotations updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating annotations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/{media_id}/annotations", response_model=StandardResponse)
async def get_media_annotations(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get annotations for a specific media upload.
    
    Clients can view annotations on their own uploads.
    Coaches can view annotations on their clients' uploads.
    
    Returns: {
        "data": {
            "media_id": "...",
            "annotations": {...}
        },
        "message": "Annotations retrieved successfully"
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
        
        # Client can view their own media annotations
        if media.client_user_id == user_id:
            pass
        # Coach can view annotations from their clients' media
        elif user.role in [UserRole.COACH, UserRole.BOTH]:
            await verify_coach_client_relationship(user_id, media.client_user_id, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view annotations for this media"
            )
        
        return StandardResponse(
            data={
                "media_id": str(media.id),
                "annotations": media.annotations or {},
                "created_at": media.created_at.isoformat()
            },
            message="Annotations retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving annotations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
