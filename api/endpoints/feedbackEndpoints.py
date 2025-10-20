from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from db.session import get_db
from schemas.feedbackSchema import (
    MediaUploadCreate, MediaUploadResponse,
    FeedbackCreate, FeedbackUpdate, FeedbackResponse,
    MediaWithFeedbackResponse
)
from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus

from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.media_upload import MediaUpload
from models.feedback import Feedback
from models.assigned_workout import AssignedWorkout
from models.user import User, UserRole
from typing import Optional
from uuid import UUID

router = APIRouter()


# ============= Helper Functions =============

def verify_coach_role(user_id: UUID, db: Session):
    """Verify that user has coach role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if user.role not in [UserRole.COACH, UserRole.BOTH]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only coaches can perform this action"
        )
    return user


# ============= Media Upload Endpoints =============

@router.post("/media", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    media_data: MediaUploadCreate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
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
            assigned_workout = db.query(AssignedWorkout).filter(
                AssignedWorkout.id == media_data.assigned_workout_id,
                AssignedWorkout.client_user_id == client_user_id
            ).first()
            
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
        db.commit()
        db.refresh(media_upload)
        
        response = MediaUploadResponse.model_validate(media_upload)
        return StandardResponse(
            data=response.model_dump(),
            message="Media uploaded successfully"
        )
        
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid exercise or workout ID"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/media/my-uploads", response_model=StandardResponse)
async def get_my_media_uploads(
    assigned_workout_id: Optional[UUID] = Query(None, description="Filter by assigned workout"),
    exercise_id: Optional[UUID] = Query(None, description="Filter by exercise"),
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Get all media uploads for the authenticated client.
    
    Returns: {"data": [media_uploads], "message": "Media uploads retrieved"}
    Errors: 401 (unauthorized), 500 (server error)
    """
    try:
        client_user_id = UUID(str(current_user.get("user_id")))
        
        query = db.query(MediaUpload).filter(
            MediaUpload.client_user_id == client_user_id
        )
        
        if assigned_workout_id:
            query = query.filter(MediaUpload.assigned_workout_id == assigned_workout_id)
        if exercise_id:
            query = query.filter(MediaUpload.exercise_id == exercise_id)
        
        media_uploads = query.order_by(MediaUpload.created_at.desc()).all()
        
        uploads = [MediaUploadResponse.model_validate(mu).model_dump() for mu in media_uploads]
        
        return StandardResponse(
            data=uploads,
            message="Media uploads retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/media/client/{client_id}", response_model=StandardResponse)
async def get_client_media_uploads(
    client_id: UUID,
    assigned_workout_id: Optional[UUID] = Query(None, description="Filter by assigned workout"),
    exercise_id: Optional[UUID] = Query(None, description="Filter by exercise"),
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Get media uploads from a specific client (Coach only).
    
    Only coaches who have an active relationship with the client can view their media.
    
    Returns: {"data": [media_uploads], "message": "Client media retrieved"}
    Errors: 401 (unauthorized), 403 (forbidden), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        # Verify coach-client relationship
        relationship = db.query(CoachClientRelationship).filter(
            CoachClientRelationship.coach_user_id == coach_user_id,
            CoachClientRelationship.client_user_id == client_id,
            CoachClientRelationship.status == RelationshipStatus.ACTIVE
        ).first()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active coach-client relationship found"
            )
        
        query = db.query(MediaUpload).filter(
            MediaUpload.client_user_id == client_id
        )
        
        if assigned_workout_id:
            query = query.filter(MediaUpload.assigned_workout_id == assigned_workout_id)
        if exercise_id:
            query = query.filter(MediaUpload.exercise_id == exercise_id)
        
        media_uploads = query.order_by(MediaUpload.created_at.desc()).all()
        
        uploads = [MediaUploadResponse.model_validate(mu).model_dump() for mu in media_uploads]
        
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


@router.get("/media/{media_id}", response_model=StandardResponse)
async def get_media_details(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific media upload.
    
    Clients can view their own uploads. Coaches can view uploads from their clients.
    
    Returns: {"data": {media_data}, "message": "Media retrieved successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        user_id = UUID(str(current_user.get("user_id")))
        
        media = db.query(MediaUpload).filter(MediaUpload.id == media_id).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Check authorization
        user = db.query(User).filter(User.id == user_id).first()
        
        # Client can view their own media
        if media.client_user_id == user_id:
            pass
        # Coach can view media from their clients
        elif user.role in [UserRole.COACH, UserRole.BOTH]:
            from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus
            relationship = db.query(CoachClientRelationship).filter(
                CoachClientRelationship.coach_user_id == user_id,
                CoachClientRelationship.client_user_id == media.client_user_id,
                CoachClientRelationship.status == RelationshipStatus.ACTIVE
            ).first()
            
            if not relationship:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this media"
                )
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


@router.delete("/media/{media_id}", response_model=StandardResponse)
async def delete_media(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Delete a media upload (Client who uploaded it only).
    
    Returns: {"data": {}, "message": "Media deleted successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        client_user_id = UUID(str(current_user.get("user_id")))
        
        media = db.query(MediaUpload).filter(MediaUpload.id == media_id).first()
        
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
        
        db.delete(media)
        db.commit()
        
        return StandardResponse(
            data={},
            message="Media deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


# ============= Feedback Endpoints =============

@router.post("/media/{media_id}/feedback", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    media_id: UUID,
    feedback_data: FeedbackCreate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    FR-5.1: Create feedback/comment on client-uploaded media (Coach only).
    
    Coaches can provide feedback with optional annotations (timestamps, coordinates, etc.).
    Supports threaded replies via parent_feedback_id.
    
    Returns: {"data": {feedback_data}, "message": "Feedback created successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        # Verify media exists and coach has relationship with client
        media = db.query(MediaUpload).filter(MediaUpload.id == media_id).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Verify coach-client relationship
        from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus
        relationship = db.query(CoachClientRelationship).filter(
            CoachClientRelationship.coach_user_id == coach_user_id,
            CoachClientRelationship.client_user_id == media.client_user_id,
            CoachClientRelationship.status == RelationshipStatus.ACTIVE
        ).first()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active coach-client relationship found"
            )
        
        # Verify parent feedback if provided
        if feedback_data.parent_feedback_id:
            parent = db.query(Feedback).filter(
                Feedback.id == feedback_data.parent_feedback_id,
                Feedback.media_id == media_id
            ).first()
            
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent feedback not found"
                )
        
        # Create feedback
        feedback = Feedback(
            media_id=media_id,
            coach_user_id=coach_user_id,
            parent_feedback_id=feedback_data.parent_feedback_id,
            content=feedback_data.content,
            annotation_data=feedback_data.annotation_data
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        # Fetch with coach details
        feedback = db.query(Feedback).options(
            joinedload(Feedback.coach)
        ).filter(Feedback.id == feedback.id).first()
        
        # Build response with coach name
        response_data = FeedbackResponse.model_validate(feedback)
        response_dict = response_data.model_dump()
        response_dict["coach_name"] = feedback.coach.full_name if feedback.coach else None
        
        return StandardResponse(
            data=response_dict,
            message="Feedback created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/media/{media_id}/feedback", response_model=StandardResponse)
async def get_media_feedback(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
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
        media = db.query(MediaUpload).filter(MediaUpload.id == media_id).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Check authorization
        user = db.query(User).filter(User.id == user_id).first()
        
        # Client can view feedback on their own media
        if media.client_user_id == user_id:
            pass
        # Coach can view feedback on their clients' media
        elif user.role in [UserRole.COACH, UserRole.BOTH]:
            from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus
            relationship = db.query(CoachClientRelationship).filter(
                CoachClientRelationship.coach_user_id == user_id,
                CoachClientRelationship.client_user_id == media.client_user_id,
                CoachClientRelationship.status == RelationshipStatus.ACTIVE
            ).first()
            
            if not relationship:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view feedback on this media"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view feedback on this media"
            )
        
        # Get all feedback for this media (with coach details)
        all_feedback = db.query(Feedback).options(
            joinedload(Feedback.coach)
        ).filter(Feedback.media_id == media_id).order_by(Feedback.created_at.asc()).all()
        
        # Build hierarchical structure
        feedback_map = {}
        root_feedback = []
        
        for fb in all_feedback:
            fb_response = FeedbackResponse.model_validate(fb)
            fb_dict = fb_response.model_dump()
            fb_dict["coach_name"] = fb.coach.full_name if fb.coach else None
            fb_dict["replies"] = []
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


@router.get("/media/{media_id}/with-feedback", response_model=StandardResponse)
async def get_media_with_feedback(
    media_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    FR-5.2: Get media upload with all associated feedback in one response.
    
    Returns: {"data": {media_with_feedback}, "message": "Media with feedback retrieved"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        user_id = UUID(str(current_user.get("user_id")))
        
        # Verify media exists and load with feedback
        media = db.query(MediaUpload).options(
            joinedload(MediaUpload.feedback).joinedload(Feedback.coach)
        ).filter(MediaUpload.id == media_id).first()
        
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media not found"
            )
        
        # Check authorization
        user = db.query(User).filter(User.id == user_id).first()
        
        if media.client_user_id == user_id:
            pass
        elif user.role in [UserRole.COACH, UserRole.BOTH]:
            from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus
            relationship = db.query(CoachClientRelationship).filter(
                CoachClientRelationship.coach_user_id == user_id,
                CoachClientRelationship.client_user_id == media.client_user_id,
                CoachClientRelationship.status == RelationshipStatus.ACTIVE
            ).first()
            
            if not relationship:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this media"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this media"
            )
        
        # Build response with hierarchical feedback
        feedback_map = {}
        root_feedback = []
        
        for fb in media.feedback:
            fb_response = FeedbackResponse.model_validate(fb)
            fb_dict = fb_response.model_dump()
            fb_dict["coach_name"] = fb.coach.full_name if fb.coach else None
            fb_dict["replies"] = []
            feedback_map[fb.id] = fb_dict
        
        for fb in media.feedback:
            fb_dict = feedback_map[fb.id]
            if fb.parent_feedback_id and fb.parent_feedback_id in feedback_map:
                feedback_map[fb.parent_feedback_id]["replies"].append(fb_dict)
            else:
                root_feedback.append(fb_dict)
        
        # Create media response
        media_response = MediaWithFeedbackResponse(
            id=media.id,
            client_user_id=media.client_user_id,
            assigned_workout_id=media.assigned_workout_id,
            exercise_id=media.exercise_id,
            media_url=media.media_url,
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


@router.put("/feedback/{feedback_id}", response_model=StandardResponse)
async def update_feedback(
    feedback_id: UUID,
    feedback_data: FeedbackUpdate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Update existing feedback (Coach who created it only).
    
    Returns: {"data": {feedback_data}, "message": "Feedback updated successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        
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
        
        db.commit()
        db.refresh(feedback)
        
        # Fetch with coach details
        feedback = db.query(Feedback).options(
            joinedload(Feedback.coach)
        ).filter(Feedback.id == feedback_id).first()
        
        response_data = FeedbackResponse.model_validate(feedback)
        response_dict = response_data.model_dump()
        response_dict["coach_name"] = feedback.coach.full_name if feedback.coach else None
        
        return StandardResponse(
            data=response_dict,
            message="Feedback updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/feedback/{feedback_id}", response_model=StandardResponse)
async def delete_feedback(
    feedback_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Delete feedback (Coach who created it only).
    
    Also deletes any nested replies.
    
    Returns: {"data": {}, "message": "Feedback deleted successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        
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
        
        db.delete(feedback)
        db.commit()
        
        return StandardResponse(
            data={},
            message="Feedback deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
