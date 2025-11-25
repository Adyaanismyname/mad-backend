from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from models.assigned_workout import AssignmentStatus

# ============= Exercise Schemas =============

class ExerciseBase(BaseModel):
    """Base exercise schema with common fields."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    muscle_group: Optional[List[str]] = None
    instructions: Optional[str] = None
    demo_video_url: Optional[str] = None
    difficulty: Optional[str] = None
    equipment_needed: Optional[List[str]] = None


class ExerciseResponse(ExerciseBase):
    """Exercise response schema."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ExerciseCreate(ExerciseBase):
    """Schema for creating a new exercise."""
    pass


class ExerciseUpdate(BaseModel):
    """Schema for updating an existing exercise."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    muscle_group: Optional[List[str]] = None
    instructions: Optional[str] = None
    demo_video_url: Optional[str] = None
    difficulty: Optional[str] = None
    equipment_needed: Optional[List[str]] = None


# ============= Workout Exercise Schemas =============

class WorkoutExerciseCreate(BaseModel):
    """Schema for adding an exercise to a workout."""
    exercise_id: UUID
    order_index: int
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_seconds: Optional[int] = None
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None


class WorkoutExerciseUpdate(BaseModel):
    """Schema for updating an exercise in a workout."""
    order_index: Optional[int] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_seconds: Optional[int] = None
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None


class WorkoutExerciseResponse(BaseModel):
    """Response schema for workout exercise with full exercise details."""
    id: UUID
    workout_id: UUID
    exercise_id: UUID
    order_index: int
    sets: Optional[int] = None
    reps: Optional[int] = None
    duration_seconds: Optional[int] = None
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    exercise: ExerciseResponse
    
    model_config = ConfigDict(from_attributes=True)


# ============= Workout Schemas =============

class WorkoutCreate(BaseModel):
    """Schema for creating a new workout routine."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    difficulty_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    category: Optional[str] = None
    is_template: bool = False
    exercises: Optional[List[WorkoutExerciseCreate]] = []


class WorkoutUpdate(BaseModel):
    """Schema for updating an existing workout routine."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    difficulty_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    estimated_duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    category: Optional[str] = None
    is_template: Optional[bool] = None


class WorkoutResponse(BaseModel):
    """Response schema for workout with exercises."""
    id: UUID
    coach_id: UUID
    name: str
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    category: Optional[str] = None
    is_template: bool
    created_at: datetime
    updated_at: datetime
    workout_exercises: List[WorkoutExerciseResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class WorkoutSummaryResponse(BaseModel):
    """Condensed workout response without exercises (for list views)."""
    id: UUID
    coach_id: UUID
    name: str
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    category: Optional[str] = None
    is_template: bool
    created_at: datetime
    updated_at: datetime
    exercise_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# ============= Assigned Workout Schemas =============

class AssignedWorkoutCreate(BaseModel):
    """Schema for assigning a workout to a client."""
    workout_id: UUID
    client_user_id: UUID
    assigned_date: date = Field(default_factory=date.today)
    due_date: Optional[date] = None
    coach_notes: Optional[str] = None


class AssignedWorkoutUpdate(BaseModel):
    """Schema for updating an assigned workout."""
    due_date: Optional[date] = None
    status: Optional[AssignmentStatus] = None
    coach_notes: Optional[str] = None
    client_notes: Optional[str] = None


class AssignedWorkoutResponse(BaseModel):
    """Response schema for assigned workout."""
    id: UUID
    workout_id: UUID
    coach_client_relationship_id: UUID
    coach_user_id: UUID
    client_user_id: UUID
    assigned_date: date
    due_date: Optional[date] = None
    status: AssignmentStatus
    coach_notes: Optional[str] = None
    client_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    workout: WorkoutResponse
    
    model_config = ConfigDict(from_attributes=True)


class AssignedWorkoutSummaryResponse(BaseModel):
    """Condensed assigned workout response for list views."""
    id: UUID
    workout_id: UUID
    client_user_id: UUID
    coach_user_id: UUID
    assigned_date: date
    due_date: Optional[date] = None
    status: AssignmentStatus
    workout_name: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
