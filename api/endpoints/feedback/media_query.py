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


async def get_pose_data_summary(pose_data: Optional[dict], include_frames: bool = False) -> Optional[dict]:
    """
    Return optimized pose data based on client needs.
    By default, only returns summary without full frame data to reduce payload size.
    """
    if not pose_data:
        return None
    
    if include_frames:
        return pose_data
    
    # Return lightweight summary without frame-by-frame data
    return {
        "version": pose_data.get("version"),
        "model": pose_data.get("model"),
        "processed_at": pose_data.get("processed_at"),
        "video_info": pose_data.get("video_info"),
        "settings": pose_data.get("settings"),
        "summary": pose_data.get("summary"),
        "keypoint_names": pose_data.get("keypoint_names"),
        "skeleton_connections": pose_data.get("skeleton_connections"),
        "frame_count": len(pose_data.get("frames", [])),
        "note": "Full frame data available via include_pose_frames=true query parameter"
    }


@router.get("/my-uploads", response_model=StandardResponse)
async def get_my_media_uploads(
    assigned_workout_id: Optional[UUID] = Query(None, description="Filter by assigned workout"),
    exercise_id: Optional[UUID] = Query(None, description="Filter by exercise"),
    include_pose_frames: bool = Query(False, description="Include full frame-by-frame pose data (increases payload size)"),
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all media uploads for the authenticated client.
    
    For videos, pose detection runs in background after upload. Check pose_analysis_status:
    - 'pending': Not yet started
    - 'processing': Currently analyzing
    - 'completed': Data available in pose_data
    - 'failed': Processing failed
    
    Pose coordinates are normalized (0-1) - multiply by video dimensions to get pixels.
    Use include_pose_frames=true to get full frame-by-frame data (increases response size).
    
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
            response = MediaUploadResponse.model_validate(mu)
            
            # Optimize pose data payload
            if mu.media_type == "video" and mu.pose_data:
                response.pose_data = await get_pose_data_summary(mu.pose_data, include_pose_frames)
            
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
    include_pose_frames: bool = Query(False, description="Include full frame-by-frame pose data (increases payload size)"),
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get media uploads from a specific client (Coach only).
    
    Only coaches who have an active relationship with the client can view their media.
    For videos, pose detection runs in background after upload. Check pose_analysis_status.
    Pose coordinates are normalized (0-1) - multiply by video dimensions to get pixels.
    Use include_pose_frames=true to get full frame-by-frame data (increases response size).
    
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
            response = MediaUploadResponse.model_validate(mu)
            
            # Optimize pose data payload
            if mu.media_type == "video" and mu.pose_data:
                response.pose_data = await get_pose_data_summary(mu.pose_data, include_pose_frames)
            
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


@router.get("/{media_id}/pose-data", response_model=StandardResponse)
async def get_pose_data(
    media_id: UUID,
    include_frames: bool = Query(True, description="Include full frame-by-frame data"),
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pose detection data for a specific media upload.
    
    This endpoint allows fetching pose data separately from the media list,
    useful for on-demand loading of detailed pose information.
    
    Returns pose_analysis_status: 'pending', 'processing', 'completed', or 'failed'
    
    Returns: {"data": {pose_data}, "message": "Pose data retrieved"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        user_id = UUID(str(current_user.get("user_id")))
        user_role = current_user.get("role")
        
        # Fetch media
        result = await db.execute(
            select(MediaUpload).filter(MediaUpload.id == media_id)
        )
        media = result.scalar_one_or_none()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Authorization check
        if user_role == "client":
            if media.client_user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this media"
                )
        elif user_role == "coach":
            await verify_coach_client_relationship(user_id, media.client_user_id, db)
        
        # Return pose data with status
        response_data = {
            "media_id": str(media.id),
            "media_type": media.media_type,
            "pose_analysis_status": media.pose_analysis_status or "pending",
            "pose_data": await get_pose_data_summary(media.pose_data, include_frames) if media.pose_data else None
        }
        
        return StandardResponse(
            data=response_data,
            message=f"Pose data retrieved (status: {media.pose_analysis_status or 'pending'})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pose data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
