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


@router.post("/workouts/assignments", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def assign_workout_to_client(
    assignment_data: AssignedWorkoutCreate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    FR-4.2: Assign a workout plan to a specific client (Coach only).
    
    Requires an active coach-client relationship.
    
    Returns: {"data": {assignment_data}, "message": "Workout assigned successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (validation), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        # Verify workout exists and belongs to coach
        workout = db.query(Workout).filter(Workout.id == assignment_data.workout_id).first()
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        if workout.coach_id != coach_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to assign this workout"
            )
        
        # Verify active coach-client relationship
        relationship = verify_coach_client_relationship(
            coach_user_id,
            assignment_data.client_user_id,
            db
        )
        
        # Create assignment
        assigned_workout = AssignedWorkout(
            workout_id=assignment_data.workout_id,
            coach_client_relationship_id=relationship.id,
            coach_user_id=coach_user_id,
            client_user_id=assignment_data.client_user_id,
            assigned_date=assignment_data.assigned_date,
            due_date=assignment_data.due_date,
            status=AssignmentStatus.ASSIGNED,
            coach_notes=assignment_data.coach_notes
        )
        
        db.add(assigned_workout)
        db.commit()
        db.refresh(assigned_workout)
        
        # Fetch with relationships
        assigned_workout = db.query(AssignedWorkout).options(
            joinedload(AssignedWorkout.workout).joinedload(Workout.workout_exercises).joinedload(WorkoutExercise.exercise)
        ).filter(AssignedWorkout.id == assigned_workout.id).first()
        
        response = AssignedWorkoutResponse.model_validate(assigned_workout)
        return StandardResponse(
            data=response.model_dump(),
            message="Workout assigned successfully"
        )
        
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid workout or client ID"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/workouts/assignments/my-workouts", response_model=StandardResponse)
async def get_my_assigned_workouts(
    status_filter: Optional[AssignmentStatus] = Query(None, description="Filter by status"),
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    FR-4.3: Get workouts assigned to the authenticated client.
    
    Clients can view their assigned workouts with full exercise details.
    
    Returns: {"data": [assigned_workouts], "message": "Assigned workouts retrieved"}
    Errors: 401 (unauthorized), 500 (server error)
    """
    try:
        client_user_id = UUID(str(current_user.get("user_id")))
        
        query = db.query(AssignedWorkout).options(
            joinedload(AssignedWorkout.workout).joinedload(Workout.workout_exercises).joinedload(WorkoutExercise.exercise)
        ).filter(AssignedWorkout.client_user_id == client_user_id)
        
        if status_filter:
            query = query.filter(AssignedWorkout.status == status_filter)
        
        assigned_workouts = query.order_by(AssignedWorkout.assigned_date.desc()).all()
        
        assignments = [AssignedWorkoutResponse.model_validate(aw).model_dump() for aw in assigned_workouts]
        
        return StandardResponse(
            data=assignments,
            message="Assigned workouts retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/workouts/assignments/client/{client_id}", response_model=StandardResponse)
async def get_client_assigned_workouts(
    client_id: UUID,
    status_filter: Optional[AssignmentStatus] = Query(None, description="Filter by status"),
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Get workouts assigned to a specific client (Coach only).
    
    Only the coach who assigned the workouts can view them.
    
    Returns: {"data": [assigned_workouts], "message": "Client workouts retrieved"}
    Errors: 401 (unauthorized), 403 (forbidden), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        # Verify relationship
        verify_coach_client_relationship(coach_user_id, client_id, db)
        
        query = db.query(AssignedWorkout).options(
            joinedload(AssignedWorkout.workout)
        ).filter(
            AssignedWorkout.client_user_id == client_id,
            AssignedWorkout.coach_user_id == coach_user_id
        )
        
        if status_filter:
            query = query.filter(AssignedWorkout.status == status_filter)
        
        assigned_workouts = query.order_by(AssignedWorkout.assigned_date.desc()).all()
        
        # Create summary responses
        summaries = []
        for aw in assigned_workouts:
            summary = AssignedWorkoutSummaryResponse(
                id=aw.id,
                workout_id=aw.workout_id,
                client_user_id=aw.client_user_id,
                coach_user_id=aw.coach_user_id,
                assigned_date=aw.assigned_date,
                due_date=aw.due_date,
                status=aw.status,
                workout_name=aw.workout.name,
                created_at=aw.created_at
            )
            summaries.append(summary.model_dump())
        
        return StandardResponse(
            data=summaries,
            message="Client workouts retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/workouts/assignments/{assignment_id}", response_model=StandardResponse)
async def update_assigned_workout(
    assignment_id: UUID,
    assignment_data: AssignedWorkoutUpdate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Update an assigned workout (Coach or Client).
    
    Coaches can update all fields. Clients can only update client_notes and status.
    
    Returns: {"data": {assignment_data}, "message": "Assignment updated"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        user_id = UUID(str(current_user.get("user_id")))
        
        assigned_workout = db.query(AssignedWorkout).filter(
            AssignedWorkout.id == assignment_id
        ).first()
        
        if not assigned_workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        # Check authorization
        user = db.query(User).filter(User.id == user_id).first()
        is_coach = user.role in [UserRole.COACH, UserRole.BOTH] and assigned_workout.coach_user_id == user_id
        is_client = assigned_workout.client_user_id == user_id
        
        if not (is_coach or is_client):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this assignment"
            )
        
        # Update fields based on role
        update_data = assignment_data.model_dump(exclude_unset=True)
        
        if is_client and not is_coach:
            # Clients can only update client_notes and status
            allowed_fields = {"client_notes", "status"}
            update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        for field, value in update_data.items():
            setattr(assigned_workout, field, value)
        
        db.commit()
        db.refresh(assigned_workout)
        
        # Fetch with relationships
        assigned_workout = db.query(AssignedWorkout).options(
            joinedload(AssignedWorkout.workout).joinedload(Workout.workout_exercises).joinedload(WorkoutExercise.exercise)
        ).filter(AssignedWorkout.id == assignment_id).first()
        
        response = AssignedWorkoutResponse.model_validate(assigned_workout)
        return StandardResponse(
            data=response.model_dump(),
            message="Assignment updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/workouts/assignments/{assignment_id}", response_model=StandardResponse)
async def delete_assigned_workout(
    assignment_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Delete/unassign a workout (Coach only).
    
    Returns: {"data": {}, "message": "Assignment deleted successfully"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        assigned_workout = db.query(AssignedWorkout).filter(
            AssignedWorkout.id == assignment_id
        ).first()
        
        if not assigned_workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        
        if assigned_workout.coach_user_id != coach_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this assignment"
            )
        
        db.delete(assigned_workout)
        db.commit()
        
        return StandardResponse(
            data={},
            message="Assignment deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
