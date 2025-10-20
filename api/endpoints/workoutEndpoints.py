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


# ============= Workout CRUD Endpoints =============

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


@router.put("/workouts/{workout_id}", response_model=StandardResponse)
async def update_workout(
    workout_id: UUID,
    workout_data: WorkoutUpdate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    FR-4.1: Update an existing workout routine (Coach only).
    
    Only the coach who created the workout can update it.
    
    Returns: {"data": {workout_data}, "message": "Workout updated successfully"}
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
                detail="Not authorized to update this workout"
            )
        
        # Update fields
        update_data = workout_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workout, field, value)
        
        db.commit()
        db.refresh(workout)
        
        # Fetch with relationships
        workout = db.query(Workout).options(
            joinedload(Workout.workout_exercises).joinedload(WorkoutExercise.exercise)
        ).filter(Workout.id == workout_id).first()
        
        workout_response = WorkoutResponse.model_validate(workout)
        return StandardResponse(
            data=workout_response.model_dump(),
            message="Workout updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


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


# ============= Workout Exercise Management =============

@router.post("/workouts/{workout_id}/exercises", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def add_exercise_to_workout(
    workout_id: UUID,
    exercise_data: WorkoutExerciseCreate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Add an exercise to an existing workout (Coach only).
    
    Returns: {"data": {workout_exercise_data}, "message": "Exercise added to workout"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 422 (validation), 500 (server error)
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
        db.commit()
        db.refresh(workout_exercise)
        
        # Fetch with exercise details
        workout_exercise = db.query(WorkoutExercise).options(
            joinedload(WorkoutExercise.exercise)
        ).filter(WorkoutExercise.id == workout_exercise.id).first()
        
        response = WorkoutExerciseResponse.model_validate(workout_exercise)
        return StandardResponse(
            data=response.model_dump(),
            message="Exercise added to workout"
        )
        
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid exercise ID"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.put("/workouts/{workout_id}/exercises/{exercise_id}", response_model=StandardResponse)
async def update_workout_exercise(
    workout_id: UUID,
    exercise_id: UUID,
    exercise_data: WorkoutExerciseUpdate,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Update exercise configuration in a workout (Coach only).
    
    Returns: {"data": {workout_exercise_data}, "message": "Exercise updated"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        workout = db.query(Workout).filter(Workout.id == workout_id).first()
        
        if not workout or workout.coach_id != coach_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this workout"
            )
        
        workout_exercise = db.query(WorkoutExercise).filter(
            WorkoutExercise.id == exercise_id,
            WorkoutExercise.workout_id == workout_id
        ).first()
        
        if not workout_exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found in this workout"
            )
        
        # Update fields
        update_data = exercise_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workout_exercise, field, value)
        
        db.commit()
        db.refresh(workout_exercise)
        
        # Fetch with exercise details
        workout_exercise = db.query(WorkoutExercise).options(
            joinedload(WorkoutExercise.exercise)
        ).filter(WorkoutExercise.id == exercise_id).first()
        
        response = WorkoutExerciseResponse.model_validate(workout_exercise)
        return StandardResponse(
            data=response.model_dump(),
            message="Exercise updated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/workouts/{workout_id}/exercises/{exercise_id}", response_model=StandardResponse)
async def remove_exercise_from_workout(
    workout_id: UUID,
    exercise_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: Session = Depends(get_db)
):
    """
    Remove an exercise from a workout (Coach only).
    
    Returns: {"data": {}, "message": "Exercise removed from workout"}
    Errors: 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        verify_coach_role(coach_user_id, db)
        
        workout = db.query(Workout).filter(Workout.id == workout_id).first()
        
        if not workout or workout.coach_id != coach_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this workout"
            )
        
        workout_exercise = db.query(WorkoutExercise).filter(
            WorkoutExercise.id == exercise_id,
            WorkoutExercise.workout_id == workout_id
        ).first()
        
        if not workout_exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found in this workout"
            )
        
        db.delete(workout_exercise)
        db.commit()
        
        return StandardResponse(
            data={},
            message="Exercise removed from workout"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


# ============= Workout Assignment Endpoints =============

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
