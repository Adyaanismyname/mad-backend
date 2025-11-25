from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from schemas.workoutSchema import ExerciseCreate, ExerciseResponse, ExerciseUpdate
from schemas.core import StandardResponse
from core.auth import verify_user_token
from models.exercise import Exercise
from uuid import UUID
from api.endpoints.helper_methods import verify_coach_role
from typing import List, Optional

router = APIRouter()

@router.post("/exercises", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    exercise_data: ExerciseCreate,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new exercise in the library (Coach only).
    
    Returns: {"data": {exercise_data}, "message": "Exercise created successfully"}
    Errors: 401 (unauthorized), 403 (not a coach), 500 (server error)
    """
    try:
        coach_user_id = UUID(str(current_user.get("user_id")))
        await verify_coach_role(coach_user_id, db)
        
        new_exercise = Exercise(
            name=exercise_data.name,
            description=exercise_data.description,
            category=exercise_data.category,
            muscle_group=exercise_data.muscle_group,
            instructions=exercise_data.instructions,
            demo_video_url=exercise_data.demo_video_url,
            difficulty=exercise_data.difficulty,
            equipment_needed=exercise_data.equipment_needed
        )
        
        db.add(new_exercise)
        await db.commit()
        await db.refresh(new_exercise)
        
        response = ExerciseResponse.model_validate(new_exercise)
        return StandardResponse(
            data=response.model_dump(),
            message="Exercise created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.get("/exercises", response_model=StandardResponse)
async def list_exercises(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    List all exercises in the library.
    
    Returns: {"data": [exercises], "message": "Exercises retrieved"}
    Errors: 401 (unauthorized), 500 (server error)
    """
    try:
        query = select(Exercise)
        
        if category:
            query = query.filter(Exercise.category == category)
        if difficulty:
            query = query.filter(Exercise.difficulty == difficulty)
            
        query = query.order_by(Exercise.name)
        
        result = await db.execute(query)
        exercises = result.scalars().all()
        
        response_data = [ExerciseResponse.model_validate(ex).model_dump() for ex in exercises]
        
        return StandardResponse(
            data=response_data,
            message="Exercises retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.get("/exercises/{exercise_id}", response_model=StandardResponse)
async def get_exercise(
    exercise_id: UUID,
    current_user: dict = Depends(verify_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific exercise.
    
    Returns: {"data": {exercise_data}, "message": "Exercise retrieved"}
    Errors: 401 (unauthorized), 404 (not found), 500 (server error)
    """
    try:
        result = await db.execute(select(Exercise).filter(Exercise.id == exercise_id))
        exercise = result.scalar_one_or_none()
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
            
        response = ExerciseResponse.model_validate(exercise)
        return StandardResponse(
            data=response.model_dump(),
            message="Exercise retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
