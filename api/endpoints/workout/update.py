from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from db.session import get_db
from schemas.workoutSchema import WorkoutUpdate, WorkoutResponse
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.workout import Workout
from models.workout_exercise import WorkoutExercise
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role

router = APIRouter()


@router.put("/{workout_id}", response_model=StandardResponse)
async def update_workout(
    workout_id: UUID,
    workout_data: WorkoutUpdate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    FR-4.1: Update an existing workout routine (Coach only).
    
    Only the coach who created the workout can update it.
    
    Returns: {"data": {workout_data}, "message": "Workout updated successfully"}
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
                detail="Not authorized to update this workout"
            )
        
        # Update fields
        update_data = workout_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workout, field, value)
        
        await db.commit()
        await db.refresh(workout)
        
        # Fetch with relationships
        result = await db.execute(
            select(Workout).options(
                joinedload(Workout.workout_exercises).joinedload(WorkoutExercise.exercise)
            ).filter(Workout.id == workout_id)
        )
        workout = result.unique().scalar_one_or_none()
        
        workout_response = WorkoutResponse.model_validate(workout)
        return StandardResponse(
            data=workout_response.model_dump(),
            message="Workout updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

