"""
Test configuration and shared fixtures for FastAPI Gym App.

This module provides reusable pytest fixtures for database setup,
authentication, and test data creation following FastAPI best practices.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Generator
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

engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL debugging
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create test database tables once per test session.
    This runs automatically before any tests.
    """
    Base.metadata.create_all(bind=engine)
    yield
    # Optionally drop tables after all tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Create a fresh database session for each test.
    
    This fixture provides a clean database state by truncating all tables
    before each test, ensuring test isolation while reusing the schema.
    """
    session = TestingSessionLocal()
    
    # Clear all data from tables 
    try:
        # Disable foreign key checks temporarily
        session.execute(text("SET session_replication_role = 'replica';"))
        
        # Truncate all tables
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE;'))
        
        # Re-enable foreign key checks
        session.execute(text("SET session_replication_role = 'origin';"))
        session.commit()
    except Exception:
        session.rollback()
        # If truncate fails (e.g., first run), just continue
        pass
    
    try:
        yield session
    finally:
        session.close()



@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """
    Create a FastAPI TestClient with database dependency override.
    
    This fixture provides a test client that uses the test database session
    instead of the production database.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============= User Fixtures =============

@pytest.fixture
def coach_user(db_session) -> User:
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
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client_user(db_session) -> User:
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
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def another_client_user(db_session) -> User:
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
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def another_coach_user(db_session) -> User:
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
    db_session.commit()
    db_session.refresh(user)
    return user


# ============= Authentication Fixtures =============

@pytest.fixture
def coach_token(coach_user) -> str:
    """Generate JWT token for coach user."""
    token_data = {
        "user_id": str(coach_user.id),
        "email": coach_user.email,
        "is_admin": False
    }
    return create_access_token(data=token_data)


@pytest.fixture
def client_token(client_user) -> str:
    """Generate JWT token for client user."""
    token_data = {
        "user_id": str(client_user.id),
        "email": client_user.email,
        "is_admin": False
    }
    return create_access_token(data=token_data)


@pytest.fixture
def another_client_token(another_client_user) -> str:
    """Generate JWT token for another client user."""
    token_data = {
        "user_id": str(another_client_user.id),
        "email": another_client_user.email,
        "is_admin": False
    }
    return create_access_token(data=token_data)


@pytest.fixture
def another_coach_token(another_coach_user) -> str:
    """Generate JWT token for another coach user."""
    token_data = {
        "user_id": str(another_coach_user.id),
        "email": another_coach_user.email,
        "is_admin": False
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

@pytest.fixture
def coach_client_relationship(db_session, coach_user, client_user) -> CoachClientRelationship:
    """Create an active coach-client relationship."""
    relationship = CoachClientRelationship(
        id=uuid.uuid4(),
        coach_user_id=coach_user.id,
        client_user_id=client_user.id,
        status=RelationshipStatus.ACTIVE
    )
    db_session.add(relationship)
    db_session.commit()
    db_session.refresh(relationship)
    return relationship


# ============= Exercise Fixtures =============

@pytest.fixture
def sample_exercise(db_session) -> Exercise:
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
    db_session.commit()
    db_session.refresh(exercise)
    return exercise


@pytest.fixture
def another_exercise(db_session) -> Exercise:
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
    db_session.commit()
    db_session.refresh(exercise)
    return exercise


# ============= Workout Fixtures =============

@pytest.fixture
def sample_workout(db_session, coach_user, sample_exercise) -> Workout:
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
    db_session.flush()
    
    # Add exercise to workout
    workout_exercise = WorkoutExercise(
        id=uuid.uuid4(),
        workout_id=workout.id,
        exercise_id=sample_exercise.id,
        order_index=1,
        sets=3,
        reps=12,
        rest_seconds=60,
        notes="Focus on form"
    )
    db_session.add(workout_exercise)
    db_session.commit()
    db_session.refresh(workout)
    return workout


@pytest.fixture
def workout_template(db_session, coach_user, sample_exercise) -> Workout:
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
    db_session.commit()
    db_session.refresh(workout)
    return workout


# ============= Assignment Fixtures =============

@pytest.fixture
def assigned_workout(db_session, sample_workout, coach_user, client_user, coach_client_relationship) -> AssignedWorkout:
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
    db_session.commit()
    db_session.refresh(assignment)
    return assignment


# ============= Media Fixtures =============

@pytest.fixture
def sample_media(db_session, client_user, sample_exercise, assigned_workout) -> MediaUpload:
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
    db_session.commit()
    db_session.refresh(media)
    return media


# ============= Feedback Fixtures =============

@pytest.fixture
def sample_feedback(db_session, sample_media, coach_user) -> Feedback:
    """Create sample feedback on media."""
    feedback = Feedback(
        id=uuid.uuid4(),
        media_id=sample_media.id,
        coach_user_id=coach_user.id,
        content="Great form! Keep it up!",
        annotation_data={"timestamp": 15.5, "note": "Watch elbow position"}
    )
    db_session.add(feedback)
    db_session.commit()
    db_session.refresh(feedback)
    return feedback


# ============= Helper Functions =============

def create_workout_data(exercise_id: str = None) -> dict:
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


def create_media_data(exercise_id: str, assigned_workout_id: str = None) -> dict:
    """Helper function to create media upload request data."""
    return {
        "assigned_workout_id": assigned_workout_id,
        "exercise_id": exercise_id,
        "media_url": "https://storage.example.com/test-video.mp4",
        "media_type": "video"
    }


def create_feedback_data(content: str = "Test feedback") -> dict:
    """Helper function to create feedback request data."""
    return {
        "content": content,
        "annotation_data": {"timestamp": 10.5},
        "parent_feedback_id": None
    }
