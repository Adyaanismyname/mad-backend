from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.workout import Workout
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role

router = APIRouter()

@router.delete("/{workout_id}", response_model=StandardResponse)
async def delete_workout(
    workout_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    FR-4.1: Delete a workout routine (Coach only).
    
    Only the coach who created the workout can delete it.
    Cascades to delete associated exercises and assignments.
    
    Returns: {"data": {}, "message": "Workout deleted successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        await verify_coach_role(coach_user_id, db)
        
        result = await db.execute(select(Workout).filter(Workout.id == workout_id))
        workout = result.scalar_one_or_none()
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        if workout.coach_id != coach_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this workout"
            )
        
        await db.delete(workout)
        await db.commit()
        
        return StandardResponse(
            data={},
            message="Workout deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

