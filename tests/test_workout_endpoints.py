"""
Test cases for Workout Management Endpoints.

This module tests workout CRUD operations, exercise management within workouts,
and authorization rules following FastAPI testing best practices.
"""

import pytest
from fastapi import status
from uuid import uuid4

from tests.conftest import create_workout_data


# ============= Workout CRUD Tests =============

@pytest.mark.workout
@pytest.mark.unit
class TestCreateWorkout:
    """Test suite for POST /workouts/workouts endpoint."""
    
    def test_create_workout_success(self, client, auth_headers, sample_exercise):
        """Test successful workout creation by coach."""
        workout_data = create_workout_data(str(sample_exercise.id))
        
        response = client.post(
            "/workouts/workouts",
            json=workout_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Workout created successfully"
        assert data["data"]["name"] == workout_data["name"]
        assert data["data"]["difficulty_level"] == workout_data["difficulty_level"]
        assert len(data["data"]["workout_exercises"]) == 1
        assert "id" in data["data"]
    
    def test_create_workout_without_exercises(self, client, auth_headers):
        """Test creating workout without exercises."""
        workout_data = create_workout_data()
        
        response = client.post(
            "/workouts/workouts",
            json=workout_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["data"]["workout_exercises"]) == 0
    
    def test_create_workout_unauthorized(self, client):
        """Test workout creation without authentication."""
        workout_data = create_workout_data()
        
        response = client.post("/workouts/workouts", json=workout_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_workout_as_client(self, client, client_auth_headers):
        """Test that clients cannot create workouts."""
        workout_data = create_workout_data()
        
        response = client.post(
            "/workouts/workouts",
            json=workout_data,
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Only coaches" in response.json()["detail"]
    
    def test_create_workout_invalid_difficulty(self, client, auth_headers):
        """Test workout creation with invalid difficulty level."""
        workout_data = create_workout_data()
        workout_data["difficulty_level"] = "super_hard"  # Invalid
        
        response = client.post(
            "/workouts/workouts",
            json=workout_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_workout_with_invalid_exercise_id(self, client, auth_headers):
        """Test workout creation with non-existent exercise ID."""
        workout_data = create_workout_data(str(uuid4()))
        
        response = client.post(
            "/workouts/workouts",
            json=workout_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_workout_missing_required_fields(self, client, auth_headers):
        """Test workout creation without required fields."""
        response = client.post(
            "/workouts/workouts",
            json={},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.workout
@pytest.mark.unit
class TestGetWorkouts:
    """Test suite for GET /workouts/workouts endpoint."""
    
    def test_get_all_workouts(self, client, auth_headers, sample_workout):
        """Test retrieving all workouts for authenticated coach."""
        response = client.get("/workouts/workouts", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Workouts retrieved successfully"
        assert len(data["data"]) >= 1
        assert "exercise_count" in data["data"][0]
    
    def test_get_workouts_filter_by_template(self, client, auth_headers, workout_template):
        """Test filtering workouts by template status."""
        response = client.get(
            "/workouts/workouts?is_template=true",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for workout in data["data"]:
            assert workout["is_template"] is True
    
    def test_get_workouts_filter_by_category(self, client, auth_headers, sample_workout):
        """Test filtering workouts by category."""
        response = client.get(
            f"/workouts/workouts?category={sample_workout.category}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for workout in data["data"]:
            assert workout["category"] == sample_workout.category
    
    def test_get_workouts_unauthorized(self, client):
        """Test getting workouts without authentication."""
        response = client.get("/workouts/workouts")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_workouts_as_client_forbidden(self, client, client_auth_headers):
        """Test that clients cannot list coach workouts."""
        response = client.get("/workouts/workouts", headers=client_auth_headers)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.workout
@pytest.mark.unit
class TestGetWorkoutDetails:
    """Test suite for GET /workouts/workouts/{workout_id} endpoint."""
    
    def test_get_workout_by_id_as_coach(self, client, auth_headers, sample_workout):
        """Test coach retrieving their own workout details."""
        response = client.get(
            f"/workouts/workouts/{sample_workout.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Workout retrieved successfully"
        assert data["data"]["id"] == str(sample_workout.id)
        assert "workout_exercises" in data["data"]
    
    def test_get_workout_as_assigned_client(self, client, client_auth_headers, assigned_workout):
        """Test client viewing their assigned workout."""
        response = client.get(
            f"/workouts/workouts/{assigned_workout.workout_id}",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["id"] == str(assigned_workout.workout_id)
    
    def test_get_workout_as_unassigned_client(self, client, another_client_token, sample_workout):
        """Test client cannot view workout not assigned to them."""
        headers = {"Authorization": f"Bearer {another_client_token}"}
        response = client.get(
            f"/workouts/workouts/{sample_workout.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_workout_by_different_coach(self, client, another_coach_token, sample_workout):
        """Test coach cannot view another coach's workout."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        response = client.get(
            f"/workouts/workouts/{sample_workout.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_nonexistent_workout(self, client, auth_headers):
        """Test retrieving non-existent workout."""
        fake_id = uuid4()
        response = client.get(
            f"/workouts/workouts/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.workout
@pytest.mark.unit
class TestUpdateWorkout:
    """Test suite for PUT /workouts/workouts/{workout_id} endpoint."""
    
    def test_update_workout_success(self, client, auth_headers, sample_workout):
        """Test successful workout update."""
        update_data = {
            "name": "Updated Workout Name",
            "difficulty_level": "advanced",
            "estimated_duration_minutes": 90
        }
        
        response = client.put(
            f"/workouts/workouts/{sample_workout.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Workout updated successfully"
        assert data["data"]["name"] == update_data["name"]
        assert data["data"]["difficulty_level"] == update_data["difficulty_level"]
    
    def test_update_workout_partial(self, client, auth_headers, sample_workout):
        """Test partial workout update."""
        update_data = {"name": "Only Name Updated"}
        
        response = client.put(
            f"/workouts/workouts/{sample_workout.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["name"] == update_data["name"]
        # Other fields should remain unchanged
        assert data["data"]["category"] == sample_workout.category
    
    def test_update_workout_by_different_coach(self, client, another_coach_token, sample_workout):
        """Test coach cannot update another coach's workout."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        update_data = {"name": "Hacked Workout"}
        
        response = client.put(
            f"/workouts/workouts/{sample_workout.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_nonexistent_workout(self, client, auth_headers):
        """Test updating non-existent workout."""
        fake_id = uuid4()
        update_data = {"name": "Updated"}
        
        response = client.put(
            f"/workouts/workouts/{fake_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.workout
@pytest.mark.unit
class TestDeleteWorkout:
    """Test suite for DELETE /workouts/workouts/{workout_id} endpoint."""
    
    def test_delete_workout_success(self, client, auth_headers, sample_workout):
        """Test successful workout deletion."""
        response = client.delete(
            f"/workouts/workouts/{sample_workout.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Workout deleted successfully"
        
        # Verify workout is actually deleted
        get_response = client.get(
            f"/workouts/workouts/{sample_workout.id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_workout_by_different_coach(self, client, another_coach_token, sample_workout):
        """Test coach cannot delete another coach's workout."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        
        response = client.delete(
            f"/workouts/workouts/{sample_workout.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_nonexistent_workout(self, client, auth_headers):
        """Test deleting non-existent workout."""
        fake_id = uuid4()
        
        response = client.delete(
            f"/workouts/workouts/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============= Workout Exercise Management Tests =============

@pytest.mark.workout
@pytest.mark.unit
class TestAddExerciseToWorkout:
    """Test suite for POST /workouts/workouts/{workout_id}/exercises endpoint."""
    
    def test_add_exercise_success(self, client, auth_headers, sample_workout, another_exercise):
        """Test successfully adding exercise to workout."""
        exercise_data = {
            "exercise_id": str(another_exercise.id),
            "order_index": 2,
            "sets": 4,
            "reps": 8,
            "rest_seconds": 90,
            "notes": "Progressive overload"
        }
        
        response = client.post(
            f"/workouts/workouts/{sample_workout.id}/exercises",
            json=exercise_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Exercise added to workout"
        assert data["data"]["exercise_id"] == exercise_data["exercise_id"]
        assert data["data"]["sets"] == exercise_data["sets"]
        assert "exercise" in data["data"]
    
    def test_add_exercise_by_different_coach(self, client, another_coach_token, sample_workout, another_exercise):
        """Test coach cannot add exercise to another coach's workout."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        exercise_data = {
            "exercise_id": str(another_exercise.id),
            "order_index": 2,
            "sets": 3,
            "reps": 10
        }
        
        response = client.post(
            f"/workouts/workouts/{sample_workout.id}/exercises",
            json=exercise_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_add_nonexistent_exercise(self, client, auth_headers, sample_workout):
        """Test adding non-existent exercise to workout."""
        exercise_data = {
            "exercise_id": str(uuid4()),
            "order_index": 2,
            "sets": 3,
            "reps": 10
        }
        
        response = client.post(
            f"/workouts/workouts/{sample_workout.id}/exercises",
            json=exercise_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.workout
@pytest.mark.unit
class TestUpdateWorkoutExercise:
    """Test suite for PUT /workouts/workouts/{workout_id}/exercises/{exercise_id} endpoint."""
    
    def test_update_exercise_success(self, client, auth_headers, sample_workout, db_session):
        """Test successfully updating exercise in workout."""
        # Get the workout exercise ID
        workout_exercise_id = sample_workout.workout_exercises[0].id
        
        update_data = {
            "sets": 5,
            "reps": 15,
            "notes": "Updated notes"
        }
        
        response = client.put(
            f"/workouts/workouts/{sample_workout.id}/exercises/{workout_exercise_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Exercise updated"
        assert data["data"]["sets"] == update_data["sets"]
        assert data["data"]["reps"] == update_data["reps"]


@pytest.mark.workout
@pytest.mark.unit
class TestRemoveExerciseFromWorkout:
    """Test suite for DELETE /workouts/workouts/{workout_id}/exercises/{exercise_id} endpoint."""
    
    def test_remove_exercise_success(self, client, auth_headers, sample_workout):
        """Test successfully removing exercise from workout."""
        workout_exercise_id = sample_workout.workout_exercises[0].id
        
        response = client.delete(
            f"/workouts/workouts/{sample_workout.id}/exercises/{workout_exercise_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Exercise removed from workout"
    
    def test_remove_nonexistent_exercise(self, client, auth_headers, sample_workout):
        """Test removing non-existent exercise from workout."""
        fake_id = uuid4()
        
        response = client.delete(
            f"/workouts/workouts/{sample_workout.id}/exercises/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============= Integration Tests =============

@pytest.mark.workout
@pytest.mark.integration
class TestWorkoutIntegration:
    """Integration tests for complete workout workflows."""
    
    def test_complete_workout_lifecycle(self, client, auth_headers, sample_exercise, another_exercise):
        """Test creating, updating, adding exercises, and deleting a workout."""
        # 1. Create workout
        workout_data = create_workout_data(str(sample_exercise.id))
        create_response = client.post(
            "/workouts/workouts",
            json=workout_data,
            headers=auth_headers
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        workout_id = create_response.json()["data"]["id"]
        
        # 2. Update workout
        update_data = {"name": "Updated Workout"}
        update_response = client.put(
            f"/workouts/workouts/{workout_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["data"]["name"] == "Updated Workout"
        
        # 3. Add another exercise
        exercise_data = {
            "exercise_id": str(another_exercise.id),
            "order_index": 2,
            "sets": 3,
            "reps": 10
        }
        add_response = client.post(
            f"/workouts/workouts/{workout_id}/exercises",
            json=exercise_data,
            headers=auth_headers
        )
        assert add_response.status_code == status.HTTP_201_CREATED
        
        # 4. Get workout details
        get_response = client.get(
            f"/workouts/workouts/{workout_id}",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_200_OK
        assert len(get_response.json()["data"]["workout_exercises"]) == 2
        
        # 5. Delete workout
        delete_response = client.delete(
            f"/workouts/workouts/{workout_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == status.HTTP_200_OK
