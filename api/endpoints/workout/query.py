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


@router.get("/workouts", response_model=StandardResponse)
async def get_workouts(
    is_template: Optional[bool] = Query(None, description="Filter by template status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Get all workouts created by the authenticated coach.
    
    Supports filtering by template status and category.
    
    Returns: {"data": [workout_list], "message": "Workouts retrieved successfully"}
    Errors: 401 (unauthorized), 403 (not a coach), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        query = db.query(Workout).filter(Workout.coach_id == coach_user_id)
        
        if is_template is not None:
            query = query.filter(Workout.is_template == is_template)
        if category:
            query = query.filter(Workout.category == category)
        
        workouts = query.order_by(Workout.created_at.desc()).all()
        
        # Create summary responses with exercise count
        workout_summaries = []
        for workout in workouts:
            summary = WorkoutSummaryResponse(
                id=workout.id,
                coach_id=workout.coach_id,
                name=workout.name,
                description=workout.description,
                difficulty_level=workout.difficulty_level,
                estimated_duration_minutes=workout.estimated_duration_minutes,
                category=workout.category,
                is_template=workout.is_template,
                created_at=workout.created_at,
                updated_at=workout.updated_at,
                exercise_count=len(workout.workout_exercises)
            )
            workout_summaries.append(summary.model_dump())
        
        return StandardResponse(
            data=workout_summaries,
            message="Workouts retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/workouts/{workout_id}", response_model=StandardResponse)
async def get_workout(
    workout_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific workout including exercises.
    
    Returns: {"data": {workout_data}, "message": "Workout retrieved successfully"}
    Errors: 401 (unauthorized), 404 (not found), 500 (server error)
    """
    try:
        user_id = UUID(str(current_user.get("user_id")))
        
        workout = db.query(Workout).options(
            joinedload(Workout.workout_exercises).joinedload(WorkoutExercise.exercise)
        ).filter(Workout.id == workout_id).first()
        
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        # Check authorization - coaches can view their own, clients can view assigned
        user = db.query(User).filter(User.id == user_id).first()
        if user.role in [UserRole.COACH, UserRole.BOTH]:
            if workout.coach_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this workout"
                )
        elif user.role == UserRole.CLIENT:
            # Check if workout is assigned to this client
            assigned = db.query(AssignedWorkout).filter(
                AssignedWorkout.workout_id == workout_id,
                AssignedWorkout.client_user_id == user_id
            ).first()
            if not assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this workout"
                )
        
        workout_response = WorkoutResponse.model_validate(workout)
        return StandardResponse(
            data=workout_response.model_dump(),
            message="Workout retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

