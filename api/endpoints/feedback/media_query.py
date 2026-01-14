from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from schemas.feedbackSchema import MediaUploadResponse
from schemas.core import StandardResponse
from core.auth import verify_user_token
from core.s3_service import get_s3_service
from core.pose_detection_service import get_pose_detection_service
from models.media_upload import MediaUpload
from typing import Optional
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role, verify_coach_client_relationship
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/media")


async def process_pose_data_for_video(media: MediaUpload, s3_service, db: AsyncSession) -> Optional[dict]:
    """
    Process pose detection for a video if not already done.
    Returns pose_data and saves it to the database.
    """
    # Skip if not a video
    if media.media_type != "video":
        return None
    
    # Return cached pose data if available
    if media.pose_data and media.pose_analysis_status == "completed":
        logger.info(f"[POSE DATA] Returning cached pose data for media {media.id}")
        logger.info(f"[POSE DATA] Summary: {json.dumps(media.pose_data.get('summary', {}), indent=2)}")
        return media.pose_data
    
    # Skip if no S3 key
    if not media.s3_key:
        logger.warning(f"[POSE DATA] No S3 key for media {media.id}, skipping pose detection")
        return None
    
    try:
        logger.info(f"[POSE DATA] Processing pose detection for media {media.id}...")
        
        # Get presigned URL for video
        presigned_url = s3_service.generate_presigned_download_url(
            s3_key=media.s3_key,
            expires_in=3600
        )
        
        # Run pose detection
        pose_service = get_pose_detection_service()
        pose_data = pose_service.analyze_video_from_s3(
            s3_url=presigned_url,
            fps=3.0,      # 3 frames per second
            max_frames=60,  # Max 60 frames (20 seconds of video)
            min_confidence=0.2
        )
        
        # Save to database
        media.pose_data = pose_data
        media.pose_analysis_status = "completed"
        await db.commit()
        
        # Log the pose data
        logger.info(f"[POSE DATA] Successfully processed pose data for media {media.id}")
        logger.info(f"[POSE DATA] Video info: {json.dumps(pose_data.get('video_info', {}), indent=2)}")
        logger.info(f"[POSE DATA] Summary: {json.dumps(pose_data.get('summary', {}), indent=2)}")
        logger.info(f"[POSE DATA] First frame keypoints: {json.dumps(pose_data.get('frames', [{}])[0], indent=2)}")
        
        return pose_data
        
    except Exception as e:
        logger.error(f"[POSE DATA] Failed to process pose data for media {media.id}: {e}")
        media.pose_analysis_status = "failed"
        media.pose_data = {"error": str(e)}
        await db.commit()
        return None


@router.get("/my-uploads", response_model=StandardResponse)
async def get_my_media_uploads(
    assigned_workout_id: Optional[UUID] = Query(None, description="Filter by assigned workout"),
    exercise_id: Optional[UUID] = Query(None, description="Filter by exercise"),
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all media uploads for the authenticated client.
    
    For videos, pose detection is automatically processed and returned with the response.
    Pose coordinates are normalized (0-1) - multiply by video dimensions to get pixels.
    
    Returns: {"data": [media_uploads], "message": "Media uploads retrieved"}
    Errors: 401 (unauthorized), 500 (server error)
    """
    try:
        client_user_id = UUID(str(current_user.get("user_id")))
        
        query = select(MediaUpload).filter(
            MediaUpload.client_user_id == client_user_id
        )
        
        if assigned_workout_id:
            query = query.filter(MediaUpload.assigned_workout_id == assigned_workout_id)
        if exercise_id:
            query = query.filter(MediaUpload.exercise_id == exercise_id)
        
        query = query.order_by(MediaUpload.created_at.desc())
        result = await db.execute(query)
        media_uploads = result.scalars().all()
        
        s3_service = get_s3_service()
        
        uploads = []
        for mu in media_uploads:
            # Process pose data for videos automatically
            if mu.media_type == "video":
                await process_pose_data_for_video(mu, s3_service, db)
            
            response = MediaUploadResponse.model_validate(mu)
            
            # Generate presigned URL for secure access
            if mu.s3_key:
                try:
                    response.presigned_url = s3_service.generate_presigned_download_url(
                        s3_key=mu.s3_key,
                        expires_in=3600
                    )
                except Exception as e:
                    logger.error(f"Failed to generate presigned URL for media {mu.id}: {e}")
            
            uploads.append(response.model_dump())
        
        return StandardResponse(
            data=uploads,
            message="Media uploads retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting media uploads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/client/{client_id}", response_model=StandardResponse)
async def get_client_media_uploads(
    client_id: UUID,
    assigned_workout_id: Optional[UUID] = Query(None, description="Filter by assigned workout"),
    exercise_id: Optional[UUID] = Query(None, description="Filter by exercise"),
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get media uploads from a specific client (Coach only).
    
    Only coaches who have an active relationship with the client can view their media.
    For videos, pose detection is automatically processed and returned with the response.
    Pose coordinates are normalized (0-1) - multiply by video dimensions to get pixels.
    
    Returns: {"data": [media_uploads], "message": "Client media retrieved"}
    Errors: 401 (unauthorized), 403 (forbidden), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        await verify_coach_role(coach_user_id, db)
        
        # Verify coach-client relationship
        await verify_coach_client_relationship(coach_user_id, client_id, db)
        
        query = select(MediaUpload).filter(
            MediaUpload.client_user_id == client_id
        )
        
        if assigned_workout_id:
            query = query.filter(MediaUpload.assigned_workout_id == assigned_workout_id)
        if exercise_id:
            query = query.filter(MediaUpload.exercise_id == exercise_id)
        
        query = query.order_by(MediaUpload.created_at.desc())
        result = await db.execute(query)
        media_uploads = result.scalars().all()
        
        s3_service = get_s3_service()
        
        uploads = []
        for mu in media_uploads:
            # Process pose data for videos automatically
            if mu.media_type == "video":
                await process_pose_data_for_video(mu, s3_service, db)
            
            response = MediaUploadResponse.model_validate(mu)
            
            # Generate presigned URL for secure access
            if mu.s3_key:
                try:
                    response.presigned_url = s3_service.generate_presigned_download_url(
                        s3_key=mu.s3_key,
                        expires_in=3600
                    )
                except Exception as e:
                    logger.error(f"Failed to generate presigned URL for media {mu.id}: {e}")
            
            uploads.append(response.model_dump())
        
        return StandardResponse(
            data=uploads,
            message="Client media retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client media: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
