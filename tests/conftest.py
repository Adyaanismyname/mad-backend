"""
Test configuration and shared fixtures for FastAPI Gym App.

This module provides reusable pytest fixtures for database setup,
authentication, and test data creation following FastAPI best practices.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from typing import AsyncGenerator
import uuid
from datetime import date, timedelta

from main import app
from db.base import Base
from db.session import get_db
from models.user import User, UserRole
from models.workout import Workout
from models.exercise import Exercise
from models.workout_exercise import WorkoutExercise
from models.assigned_workout import AssignedWorkout, AssignmentStatus
from models.coach_client_relationship import CoachClientRelationship, RelationshipStatus
from models.media_upload import MediaUpload
from models.feedback import Feedback
from core.auth import create_access_token
from core.config import settings

# ============= Database Setup =============

# Use PostgreSQL test database (separate from development database)
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

if not TEST_DATABASE_URL or TEST_DATABASE_URL == "/gym_app_test":
    raise ValueError(
        "TEST_DATABASE_URL or DATABASE_URL environment variable must be set. "
    )

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    poolclass=NullPool,  # Use NullPool to avoid event loop issues with connection pooling
)
TestingSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="session", autouse=True)
async def setup_test_database():
    """Create all database tables once for the entire test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(setup_test_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for each test."""
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = TestingSessionLocal(bind=conn)
        try:
            yield session
        finally:
            if trans.is_active:
                await trans.rollback()
            await session.close()



@pytest_asyncio.fixture()
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a FastAPI AsyncClient with database dependency override.
    
    This fixture provides a test client that uses the test database session
    instead of the production database.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============= User Fixtures =============

@pytest_asyncio.fixture()
async def coach_user(db_session) -> User:
    """Create a coach user for testing."""
    user = User(
        id=uuid.uuid4(),
        email="coach@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ySw.kF8Zy7QG",  # "password123"
        role=UserRole.COACH,
        full_name="John Coach",
        phone_number="+1234567890"
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def client_user(db_session) -> User:
    """Create a client user for testing."""
    user = User(
        id=uuid.uuid4(),
        email="client@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ySw.kF8Zy7QG",  # "password123"
        role=UserRole.CLIENT,
        full_name="Jane Client",
        phone_number="+0987654321"
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def another_client_user(db_session) -> User:
    """Create another client user for testing authorization."""
    user = User(
        id=uuid.uuid4(),
        email="client2@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ySw.kF8Zy7QG",
        role=UserRole.CLIENT,
        full_name="Bob Client",
        phone_number="+1122334455"
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def another_coach_user(db_session) -> User:
    """Create another coach user for testing authorization."""
    user = User(
        id=uuid.uuid4(),
        email="coach2@example.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ySw.kF8Zy7QG",
        role=UserRole.COACH,
        full_name="Mike Coach",
        phone_number="+5566778899"
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


# ============= Authentication Fixtures =============

@pytest.fixture
def coach_token(coach_user) -> str:
    """Generate JWT token for coach user."""
    token_data = {
        "user_id": str(coach_user.id),
        "email": coach_user.email,
        "full_name": coach_user.full_name,
        "role": coach_user.role.value,
        "is_activated": coach_user.is_activated
    }
    return create_access_token(data=token_data)


@pytest.fixture
def client_token(client_user) -> str:
    """Generate JWT token for client user."""
    token_data = {
        "user_id": str(client_user.id),
        "email": client_user.email,
        "full_name": client_user.full_name,
        "role": client_user.role.value,
        "is_activated": client_user.is_activated
    }
    return create_access_token(data=token_data)


@pytest.fixture
def another_client_token(another_client_user) -> str:
    """Generate JWT token for another client user."""
    token_data = {
        "user_id": str(another_client_user.id),
        "email": another_client_user.email,
        "full_name": another_client_user.full_name,
        "role": another_client_user.role.value,
        "is_activated": another_client_user.is_activated
    }
    return create_access_token(data=token_data)


@pytest.fixture
def another_coach_token(another_coach_user) -> str:
    """Generate JWT token for another coach user."""
    token_data = {
        "user_id": str(another_coach_user.id),
        "email": another_coach_user.email,
        "full_name": another_coach_user.full_name,
        "role": another_coach_user.role.value,
        "is_activated": another_coach_user.is_activated
    }
    return create_access_token(data=token_data)


@pytest.fixture
def auth_headers(coach_token) -> dict:
    """Create authorization headers with coach token."""
    return {"Authorization": f"Bearer {coach_token}"}


@pytest.fixture
def client_auth_headers(client_token) -> dict:
    """Create authorization headers with client token."""
    return {"Authorization": f"Bearer {client_token}"}


# ============= Relationship Fixtures =============

@pytest_asyncio.fixture()
async def coach_client_relationship(db_session, coach_user, client_user) -> CoachClientRelationship:
    """Create an active coach-client relationship."""
    relationship = CoachClientRelationship(
        id=uuid.uuid4(),
        coach_user_id=coach_user.id,
        client_user_id=client_user.id,
        status=RelationshipStatus.ACTIVE
    )
    db_session.add(relationship)
    await db_session.flush()
    await db_session.refresh(relationship)
    return relationship


# ============= Exercise Fixtures =============

@pytest_asyncio.fixture()
async def sample_exercise(db_session) -> Exercise:
    """Create a sample exercise for testing."""
    exercise = Exercise(
        id=uuid.uuid4(),
        name="Bench Press",
        description="Classic chest exercise",
        category="Strength",
        muscle_group=["chest", "triceps", "shoulders"],
        instructions="Lie on bench, lower bar to chest, press up",
        difficulty="intermediate",
        equipment_needed=["barbell", "bench"]
    )
    db_session.add(exercise)
    await db_session.flush()
    await db_session.refresh(exercise)
    return exercise


@pytest_asyncio.fixture()
async def another_exercise(db_session) -> Exercise:
    """Create another exercise for testing."""
    exercise = Exercise(
        id=uuid.uuid4(),
        name="Squat",
        description="Lower body compound exercise",
        category="Strength",
        muscle_group=["quads", "glutes", "hamstrings"],
        instructions="Stand with bar on shoulders, squat down, stand up",
        difficulty="advanced",
        equipment_needed=["barbell", "rack"]
    )
    db_session.add(exercise)
    await db_session.flush()
    await db_session.refresh(exercise)
    return exercise


# ============= Workout Fixtures =============

@pytest_asyncio.fixture()
async def sample_workout(db_session, coach_user, sample_exercise) -> Workout:
    """Create a sample workout with exercises."""
    workout = Workout(
        id=uuid.uuid4(),
        coach_id=coach_user.id,
        name="Full Body Strength",
        description="Complete strength training workout",
        difficulty_level="intermediate",
        estimated_duration_minutes=60,
        category="Strength Training",
        is_template=False
    )
    db_session.add(workout)
    await db_session.flush()

    # Add exercise to workout
    workout_exercise = WorkoutExercise(
        id=uuid.uuid4(),
        workout_id=workout.id,
        workout=workout,
        exercise_id=sample_exercise.id,
        order_index=1,
        sets=3,
        reps=12,
        rest_seconds=60,
        notes="Focus on form"
    )
    db_session.add(workout_exercise)
    await db_session.flush()
    await db_session.refresh(workout, attribute_names=["workout_exercises"])
    return workout


@pytest_asyncio.fixture()
async def workout_template(db_session, coach_user, sample_exercise) -> Workout:
    """Create a workout template."""
    workout = Workout(
        id=uuid.uuid4(),
        coach_id=coach_user.id,
        name="Beginner Template",
        description="Template for beginners",
        difficulty_level="beginner",
        estimated_duration_minutes=45,
        category="General Fitness",
        is_template=True
    )
    db_session.add(workout)
    await db_session.flush()
    await db_session.refresh(workout)
    return workout


# ============= Assignment Fixtures =============

@pytest_asyncio.fixture()
async def assigned_workout(db_session, sample_workout, coach_user, client_user, coach_client_relationship) -> AssignedWorkout:
    """Create an assigned workout."""
    assignment = AssignedWorkout(
        id=uuid.uuid4(),
        workout_id=sample_workout.id,
        coach_client_relationship_id=coach_client_relationship.id,
        coach_user_id=coach_user.id,
        client_user_id=client_user.id,
        assigned_date=date.today(),
        due_date=date.today() + timedelta(days=7),
        status=AssignmentStatus.ASSIGNED,
        coach_notes="Focus on technique this week"
    )
    db_session.add(assignment)
    await db_session.flush()
    await db_session.refresh(assignment)
    return assignment


# ============= Media Fixtures =============

@pytest_asyncio.fixture()
async def sample_media(db_session, client_user, sample_exercise, assigned_workout) -> MediaUpload:
    """Create a sample media upload."""
    media = MediaUpload(
        id=uuid.uuid4(),
        client_user_id=client_user.id,
        assigned_workout_id=assigned_workout.id,
        exercise_id=sample_exercise.id,
        media_url="https://storage.example.com/video1.mp4",
        media_type="video",
        status="ready"
    )
    db_session.add(media)
    await db_session.flush()
    await db_session.refresh(media)
    return media


# ============= Feedback Fixtures =============

@pytest_asyncio.fixture()
async def sample_feedback(db_session, sample_media, coach_user) -> Feedback:
    """Create sample feedback on media."""
    feedback = Feedback(
        id=uuid.uuid4(),
        media_id=sample_media.id,
        coach_user_id=coach_user.id,
        content="Great form! Keep it up!",
        annotation_data={"timestamp": 15.5, "note": "Watch elbow position"}
    )
    db_session.add(feedback)
    await db_session.flush()
    await db_session.refresh(feedback)
    return feedback


# ============= Helper Functions =============

def create_workout_data(exercise_id: str | None = None) -> dict:
    """Helper function to create workout request data."""
    data = {
        "name": "Test Workout",
        "description": "Test description",
        "difficulty_level": "intermediate",
        "estimated_duration_minutes": 45,
        "category": "Strength",
        "is_template": False
    }
    if exercise_id:
        data["exercises"] = [
            {
                "exercise_id": exercise_id,
                "order_index": 1,
                "sets": 3,
                "reps": 10,
                "rest_seconds": 60,
                "notes": "Test notes"
            }
        ]
    else:
        data["exercises"] = []
    return data


def create_assignment_data(workout_id: str, client_id: str) -> dict:
    """Helper function to create assignment request data."""
    return {
        "workout_id": workout_id,
        "client_user_id": client_id,
        "assigned_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "coach_notes": "Test assignment notes"
    }


def create_media_data(exercise_id: str, assigned_workout_id: str | None = None) -> dict:
    """Helper function to create media upload request data (legacy/direct upload)."""
    return {
        "assigned_workout_id": assigned_workout_id,
        "exercise_id": exercise_id,
        "media_url": "https://storage.example.com/test-video.mp4",
        "media_type": "video"
    }


def create_media_initiate_data(exercise_id: str, assigned_workout_id: str | None = None) -> dict:
    """Helper function to create media upload initiate request data (S3 presigned URL)."""
    return {
        "assigned_workout_id": assigned_workout_id,
        "exercise_id": exercise_id,
        "filename": "test-workout-video.mp4",
        "media_type": "video",
        "file_size_mb": 25.5
    }


def create_media_confirm_data(upload_id: str, exercise_id: str, assigned_workout_id: str | None = None) -> dict:
    """Helper function to create media upload confirm request data."""
    return {
        "upload_id": upload_id,
        "exercise_id": exercise_id,
        "assigned_workout_id": assigned_workout_id
    }


def create_feedback_data(content: str = "Test feedback") -> dict:
    """Helper function to create feedback request data."""
    return {
        "content": content,
        "annotation_data": {"timestamp": 10.5},
        "parent_feedback_id": None
    }
