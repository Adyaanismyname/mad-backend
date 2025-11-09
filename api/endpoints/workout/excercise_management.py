from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from db.session import get_db
from schemas.workoutSchema import (
    WorkoutExerciseCreate, WorkoutExerciseUpdate, WorkoutExerciseResponse
)
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.workout import Workout
from models.workout_exercise import WorkoutExercise
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role

router = APIRouter()


@router.post("/{workout_id}/exercises", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def add_exercise_to_workout(
    workout_id: UUID,
    exercise_data: WorkoutExerciseCreate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Add an exercise to an existing workout (Coach only).
    
    Returns: {"data": {workout_exercise_data}, "message": "Exercise added to workout"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (validation), 500 (server error)
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
                detail="Not authorized to modify this workout"
            )
        
        workout_exercise = WorkoutExercise(
            workout_id=workout_id,
            exercise_id=exercise_data.exercise_id,
            order_index=exercise_data.order_index,
            sets=exercise_data.sets,
            reps=exercise_data.reps,
            duration_seconds=exercise_data.duration_seconds,
            rest_seconds=exercise_data.rest_seconds,
            notes=exercise_data.notes
        )
        
        db.add(workout_exercise)
        await db.commit()
        await db.refresh(workout_exercise)
        
        # Fetch with exercise details
        result = await db.execute(
            select(WorkoutExercise).options(
                joinedload(WorkoutExercise.exercise)
            ).filter(WorkoutExercise.id == workout_exercise.id)
        )
        workout_exercise = result.scalar_one_or_none()
        
        response = WorkoutExerciseResponse.model_validate(workout_exercise)
        return StandardResponse(
            data=response.model_dump(),
            message="Exercise added to workout"
        )
        
    except HTTPException:
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid exercise ID"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/{workout_id}/exercises/{exercise_id}", response_model=StandardResponse)
async def update_workout_exercise(
    workout_id: UUID,
    exercise_id: UUID,
    exercise_data: WorkoutExerciseUpdate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Update exercise configuration in a workout (Coach only).
    
    Returns: {"data": {workout_exercise_data}, "message": "Exercise updated"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        await verify_coach_role(coach_user_id, db)
        
        result = await db.execute(select(Workout).filter(Workout.id == workout_id))
        workout = result.scalar_one_or_none()
        
        if not workout or workout.coach_id != coach_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this workout"
            )
        
        result = await db.execute(
            select(WorkoutExercise).filter(
                WorkoutExercise.id == exercise_id,
                WorkoutExercise.workout_id == workout_id
            )
        )
        workout_exercise = result.scalar_one_or_none()
        
        if not workout_exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found in this workout"
            )
        
        # Update fields
        update_data = exercise_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workout_exercise, field, value)
        
        await db.commit()
        await db.refresh(workout_exercise)
        
        # Fetch with exercise details
        result = await db.execute(
            select(WorkoutExercise).options(
                joinedload(WorkoutExercise.exercise)
            ).filter(WorkoutExercise.id == exercise_id)
        )
        workout_exercise = result.scalar_one_or_none()
        
        response = WorkoutExerciseResponse.model_validate(workout_exercise)
        return StandardResponse(
            data=response.model_dump(),
            message="Exercise updated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/{workout_id}/exercises/{exercise_id}", response_model=StandardResponse)
async def remove_exercise_from_workout(
    workout_id: UUID,
    exercise_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove an exercise from a workout (Coach only).
    
    Returns: {"data": {}, "message": "Exercise removed from workout"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        await verify_coach_role(coach_user_id, db)
        
        result = await db.execute(select(Workout).filter(Workout.id == workout_id))
        workout = result.scalar_one_or_none()
        
        if not workout or workout.coach_id != coach_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this workout"
            )
        
        result = await db.execute(
            select(WorkoutExercise).filter(
                WorkoutExercise.id == exercise_id,
                WorkoutExercise.workout_id == workout_id
            )
        )
        workout_exercise = result.scalar_one_or_none()
        
        if not workout_exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found in this workout"
            )
        
        await db.delete(workout_exercise)
        await db.commit()
        
        return StandardResponse(
            data={},
            message="Exercise removed from workout"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
