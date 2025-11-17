from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from db.session import get_db
from schemas.feedbackSchema import (
    MediaUploadCreate,
    MediaUploadInitiate, 
    PresignedUploadResponse,
    MediaUploadConfirm,
    MediaUploadResponse
)
from schemas.core import StandardResponse
from core.auth import verify_user_token
from core.s3_service import get_s3_service
from models.media_upload import MediaUpload
from models.assigned_workout import AssignedWorkout
from models.pending_upload import PendingUpload
from uuid import UUID, uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media")


@router.post("/initiate-upload", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def initiate_media_upload(
    upload_data: MediaUploadInitiate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate a media upload by generating a presigned S3 URL.
    
    This endpoint provides a secure presigned URL that clients can use to upload
    files directly to S3, bypassing the API server for better performance.
    
    Workflow:
    1. Client requests presigned URL with file details
    2. Server validates file type and size
    3. Server generates presigned URL with S3
    4. Client uploads directly to S3 using the presigned URL
    5. Client calls /confirm-upload to save metadata in database
    
    Returns: {
        "data": {
            "upload_url": "https://...",  # Use this URL for PUT request
            "media_url": "https://...",   # Save this URL for confirm step
            "s3_key": "...",
            "content_type": "...",
            "expires_at": "...",
            "upload_id": "..."            # Use this ID to confirm upload
        },
        "message": "..."
    }
    
    Errors: 
        - 400: Invalid file type or size
        - 401: Unauthorized
        - 403: Forbidden (assigned workout not found)
        - 500: Server error
    """
    try:
        client_user_id = UUID(str(current_user.get("user_id")))
        
        # Verify assigned workout belongs to client if provided
        if upload_data.assigned_workout_id:
            result = await db.execute(
                select(AssignedWorkout).filter(
                    AssignedWorkout.id == upload_data.assigned_workout_id,
                    AssignedWorkout.client_user_id == client_user_id
                )
            )
            assigned_workout = result.scalar_one_or_none()
            
            if not assigned_workout:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Assigned workout not found or not authorized"
                )
        
        # Get S3 service
        s3_service = get_s3_service()
        
        # Generate presigned URL
        try:
            # Validate media_type is one of the allowed values
            if upload_data.media_type not in ['image', 'video']:
                raise ValueError("media_type must be 'image' or 'video'")
            
            presigned_data = s3_service.generate_presigned_upload_url(
                user_id=client_user_id,
                exercise_id=upload_data.exercise_id,
                filename=upload_data.filename,
                media_type=upload_data.media_type,  # type: ignore
                file_size_mb=upload_data.file_size_mb
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Generate upload ID for confirmation
        upload_id = uuid4()
        
        # Store pending upload in database (PostgreSQL with automatic cleanup)
        pending_upload = PendingUpload(
            id=upload_id,
            user_id=client_user_id,
            s3_key=presigned_data['s3_key'],
            media_url=presigned_data['media_url'],
            media_type=upload_data.media_type,
            exercise_id=upload_data.exercise_id,
            assigned_workout_id=upload_data.assigned_workout_id,
            expires_at=datetime.fromisoformat(presigned_data['expires_at'].replace('Z', '+00:00')),
            status='pending'
        )
        
        db.add(pending_upload)
        await db.commit()
        
        response_data = PresignedUploadResponse(
            upload_url=presigned_data['upload_url'],
            media_url=presigned_data['media_url'],
            s3_key=presigned_data['s3_key'],
            content_type=presigned_data['content_type'],
            expires_at=presigned_data['expires_at'],
            upload_id=upload_id
        )
        
        return StandardResponse(
            data=response_data.model_dump(),
            message="Presigned upload URL generated successfully. Use the upload_url to PUT your file."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate upload: {str(e)}"
        )


@router.post("/confirm-upload", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def confirm_media_upload(
    confirm_data: MediaUploadConfirm,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm a media upload after successful S3 upload.
    
    After the client successfully uploads to S3 using the presigned URL,
    they must call this endpoint to save the media metadata in the database.
    
    This endpoint verifies the file exists in S3 and creates the database record.
    
    Returns: {"data": {media_data}, "message": "Media upload confirmed"}
    Errors: 
        - 400: Upload ID not found or expired
        - 401: Unauthorized
        - 403: Forbidden
        - 404: File not found in S3
        - 500: Server error
    """
    try:
        client_user_id = UUID(str(current_user.get("user_id")))
        
        # Retrieve pending upload from database
        result = await db.execute(
            select(PendingUpload).filter(PendingUpload.id == confirm_data.upload_id)
        )
        pending_upload = result.scalar_one_or_none()
        
        # Verify pending upload exists and is valid
        if not pending_upload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired upload ID"
            )
        
        # Check if expired
        if not pending_upload.is_valid():
            # Mark as expired and cleanup
            pending_upload.status = 'expired'
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload ID has expired. Please initiate a new upload."
            )
        
        # Verify the user making the request is the same as who initiated
        if pending_upload.user_id != client_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to confirm this upload"
            )
        
        # Verify file exists in S3
        s3_service = get_s3_service()
        if not s3_service.verify_file_exists(pending_upload.s3_key):
            # Mark as failed
            pending_upload.status = 'failed'
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in S3. Please ensure upload completed successfully."
            )
        
        # Verify assigned workout belongs to client if provided
        if confirm_data.assigned_workout_id:
            result = await db.execute(
                select(AssignedWorkout).filter(
                    AssignedWorkout.id == confirm_data.assigned_workout_id,
                    AssignedWorkout.client_user_id == client_user_id
                )
            )
            assigned_workout = result.scalar_one_or_none()
            
            if not assigned_workout:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Assigned workout not found or not authorized"
                )
        
        # Create media upload record
        media_upload = MediaUpload(
            client_user_id=client_user_id,
            assigned_workout_id=confirm_data.assigned_workout_id,
            exercise_id=confirm_data.exercise_id,
            media_url=pending_upload.media_url,
            s3_key=pending_upload.s3_key,
            media_type=pending_upload.media_type,
            status="ready"
        )
        
        db.add(media_upload)
        
        # Mark pending upload as confirmed (soft delete for audit trail)
        pending_upload.status = 'confirmed'
        pending_upload.deleted_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(media_upload)
        
        response = MediaUploadResponse.model_validate(media_upload)
        return StandardResponse(
            data=response.model_dump(),
            message="Media upload confirmed successfully"
        )
        
    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid exercise or workout ID"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error confirming upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def upload_media_direct(
    media_data: MediaUploadCreate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Direct media upload (legacy/testing endpoint).
    
    This endpoint allows direct media upload without S3 presigned URL workflow.
    Useful for:
    - Testing
    - Legacy clients
    - Local development
    
    For production, prefer the initiate-upload → confirm-upload flow.
    
    Returns: {"data": {media_data}, "message": "Media uploaded successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 422 (validation), 500 (server error)
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
        
        # Create media upload directly (bypass S3 presigned URL workflow)
        media_upload = MediaUpload(
            client_user_id=client_user_id,
            assigned_workout_id=media_data.assigned_workout_id,
            exercise_id=media_data.exercise_id,
            media_url=media_data.media_url,
            s3_key=media_data.s3_key,
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
        logger.error(f"Error uploading media: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

