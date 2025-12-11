from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from schemas.feedbackSchema import MediaUploadResponse
from schemas.core import StandardResponse
from core.auth import verify_user_token
from core.s3_service import get_s3_service
from models.media_upload import MediaUpload
from typing import Optional
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role, verify_coach_client_relationship

router = APIRouter(prefix="/media")


@router.get("/my-uploads", response_model=StandardResponse)
async def get_my_media_uploads(
    assigned_workout_id: Optional[UUID] = Query(None, description="Filter by assigned workout"),
    exercise_id: Optional[UUID] = Query(None, description="Filter by exercise"),
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all media uploads for the authenticated client.
    
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
        
        # Generate presigned URLs for each media upload
        s3_service = get_s3_service()
        
        uploads = []
        for mu in media_uploads:
            response = MediaUploadResponse.model_validate(mu)
            # Generate presigned URL for secure access
            if mu.s3_key:
                try:
                    response.presigned_url = s3_service.generate_presigned_download_url(
                        s3_key=mu.s3_key,
                        expires_in=3600  # 1 hour
                    )
                except Exception as e:
                    print(f"Failed to generate presigned URL for media {mu.id}: {e}")
            uploads.append(response.model_dump())
        
        return StandardResponse(
            data=uploads,
            message="Media uploads retrieved successfully"
        )
        
    except Exception as e:
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
        
        # Generate presigned URLs for each media upload
        s3_service = get_s3_service()
        
        uploads = []
        for mu in media_uploads:
            response = MediaUploadResponse.model_validate(mu)
            # Generate presigned URL for secure access
            if mu.s3_key:
                try:
                    response.presigned_url = s3_service.generate_presigned_download_url(
                        s3_key=mu.s3_key,
                        expires_in=3600  # 1 hour
                    )
                except Exception as e:
                    print(f"Failed to generate presigned URL for media {mu.id}: {e}")
            uploads.append(response.model_dump())
        
        return StandardResponse(
            data=uploads,
            message="Client media retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
