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

@router.delete("/workouts/{workout_id}", response_model=StandardResponse)
async def delete_workout(
    workout_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
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
        verify_coach_role(coach_user_id, db)
        
        workout = db.query(Workout).filter(Workout.id == workout_id).first()
        
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
        
        db.delete(workout)
        db.commit()
        
        return StandardResponse(
            data={},
            message="Workout deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

