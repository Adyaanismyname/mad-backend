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


def verify_coach_client_relationship(coach_id: UUID, client_id: UUID, db: Session):
    """Verify active coach-client relationship."""
    relationship = db.query(CoachClientRelationship).filter(
        CoachClientRelationship.coach_user_id == coach_id,
        CoachClientRelationship.client_user_id == client_id,
        CoachClientRelationship.status == RelationshipStatus.ACTIVE
    ).first()
    
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active coach-client relationship found"
        )
    return relationship