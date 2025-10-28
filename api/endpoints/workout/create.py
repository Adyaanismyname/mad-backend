from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from db.session import get_db
from schemas.workoutSchema import (
    WorkoutCreate, WorkoutUpdate, WorkoutResponse, WorkoutSummaryResponse,
    WorkoutExerciseCreate, WorkoutExerciseUpdate, WorkoutExerciseResponse,
    AssignedWorkoutCreate, AssignedWorkoutUpdate, AssignedWorkoutResponse,
    AssignedWorkoutSummaryResponse
)
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.workout import Workout
from models.workout_exercise import WorkoutExercise
from models.assigned_workout import AssignedWorkout, AssignmentStatus
from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus
from models.user import User, UserRole
from typing import Optional
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role, verify_coach_client_relationship

router = APIRouter()


@router.post("/workouts", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    workout_data: WorkoutCreate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    FR-4.1: Create a new workout routine (Coach only).
    
    Creates a workout with optional exercises. Coach can create templates or client-specific workouts.
    
    Returns: {"data": {workout_data}, "message": "Workout created successfully"}
    Errors: 401 (unauthorized), 403 (not a coach), 422 (validation), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        # Create the workout
        new_workout = Workout(
            coach_id=coach_user_id,
            name=workout_data.name,
            description=workout_data.description,
            difficulty_level=workout_data.difficulty_level,
            estimated_duration_minutes=workout_data.estimated_duration_minutes,
            category=workout_data.category,
            is_template=workout_data.is_template
        )
        
        db.add(new_workout)
        db.flush()  # Get the workout ID
        
        # Add exercises to the workout
        if workout_data.exercises:
            for exercise_data in workout_data.exercises:
                workout_exercise = WorkoutExercise(
                    workout_id=new_workout.id,
                    exercise_id=exercise_data.exercise_id,
                    order_index=exercise_data.order_index,
                    sets=exercise_data.sets,
                    reps=exercise_data.reps,
                    duration_seconds=exercise_data.duration_seconds,
                    rest_seconds=exercise_data.rest_seconds,
                    notes=exercise_data.notes
                )
                db.add(workout_exercise)
        
        db.commit()
        db.refresh(new_workout)
        
        # Fetch with relationships
        workout = db.query(Workout).options(
            joinedload(Workout.workout_exercises).joinedload(WorkoutExercise.exercise)
        ).filter(Workout.id == new_workout.id).first()
        
        workout_response = WorkoutResponse.model_validate(workout)
        return StandardResponse(
            data=workout_response.model_dump(),
            message="Workout created successfully"
        )
        
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid exercise ID or constraint violation"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
