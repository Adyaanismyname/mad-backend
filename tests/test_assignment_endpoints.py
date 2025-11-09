"""
Test cases for Workout Assignment Endpoints.

This module tests workout assignment operations, client access to assigned workouts,
and authorization rules following FastAPI testing best practices.
"""

import pytest
from fastapi import status
from uuid import uuid4
from datetime import date, timedelta

from tests.conftest import create_assignment_data


# ============= Assignment Creation Tests =============

@pytest.mark.workout
@pytest.mark.unit
class TestAssignWorkout:
    """Test suite for POST /workouts/assignments endpoint."""
    
    async def test_assign_workout_success(self, client, auth_headers, sample_workout, client_user, coach_client_relationship):
        """Test successful workout assignment to client."""
        assignment_data = create_assignment_data(
            str(sample_workout.id),
            str(client_user.id)
        )
        
        response = await client.post(
            "/workouts/assignments",
            json=assignment_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Workout assigned successfully"
        assert data["data"]["workout_id"] == str(sample_workout.id)
        assert data["data"]["client_user_id"] == str(client_user.id)
        assert data["data"]["status"] == "assigned"
        assert "workout" in data["data"]
    
    async def test_assign_workout_without_relationship(self, client, auth_headers, sample_workout, another_client_user):
        """Test assignment fails without active coach-client relationship."""
        assignment_data = create_assignment_data(
            str(sample_workout.id),
            str(another_client_user.id)
        )
        
        response = await client.post(
            "/workouts/assignments",
            json=assignment_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "relationship" in response.json()["detail"].lower()
    
    async def test_assign_workout_different_coach(self, client, another_coach_token, sample_workout, client_user):
        """Test coach cannot assign another coach's workout."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        assignment_data = create_assignment_data(
            str(sample_workout.id),
            str(client_user.id)
        )
        
        response = await client.post(
            "/workouts/assignments",
            json=assignment_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_assign_nonexistent_workout(self, client, auth_headers, client_user, coach_client_relationship):
        """Test assigning non-existent workout."""
        assignment_data = create_assignment_data(
            str(uuid4()),
            str(client_user.id)
        )
        
        response = await client.post(
            "/workouts/assignments",
            json=assignment_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_assign_as_client_forbidden(self, client, client_auth_headers, sample_workout, client_user):
        """Test clients cannot assign workouts."""
        assignment_data = create_assignment_data(
            str(sample_workout.id),
            str(client_user.id)
        )
        
        response = await client.post(
            "/workouts/assignments",
            json=assignment_data,
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_assign_workout_with_due_date(self, client, auth_headers, sample_workout, client_user, coach_client_relationship):
        """Test assignment with specific due date."""
        assignment_data = create_assignment_data(
            str(sample_workout.id),
            str(client_user.id)
        )
        assignment_data["due_date"] = (date.today() + timedelta(days=14)).isoformat()
        
        response = await client.post(
            "/workouts/assignments",
            json=assignment_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["due_date"] == assignment_data["due_date"]


# ============= Get Assigned Workouts Tests =============

@pytest.mark.workout
@pytest.mark.unit
class TestGetMyAssignedWorkouts:
    """Test suite for GET /workouts/assignments/my-workouts endpoint."""
    
    async def test_get_my_workouts_success(self, client, client_auth_headers, assigned_workout):
        """Test client retrieving their assigned workouts."""
        response = await client.get(
            "/workouts/assignments/my-workouts",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Assigned workouts retrieved successfully"
        assert len(data["data"]) >= 1
        assert data["data"][0]["workout_id"] == str(assigned_workout.workout_id)
        # Verify full workout details are included
        assert "workout" in data["data"][0]
        assert "workout_exercises" in data["data"][0]["workout"]
    
    async def test_get_my_workouts_filter_by_status(self, client, client_auth_headers, assigned_workout):
        """Test filtering assigned workouts by status."""
        response = await client.get(
            "/workouts/assignments/my-workouts?status_filter=assigned",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for assignment in data["data"]:
            assert assignment["status"] == "assigned"
    
    async def test_get_my_workouts_empty_list(self, client, another_client_token):
        """Test client with no assignments gets empty list."""
        headers = {"Authorization": f"Bearer {another_client_token}"}
        
        response = await client.get(
            "/workouts/assignments/my-workouts",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 0
    
    async def test_get_my_workouts_unauthorized(self, client):
        """Test getting assignments without authentication."""
        response = await client.get("/workouts/assignments/my-workouts")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.workout
@pytest.mark.unit
class TestGetClientAssignedWorkouts:
    """Test suite for GET /workouts/assignments/client/{client_id} endpoint."""
    
    async def test_get_client_workouts_success(self, client, auth_headers, client_user, assigned_workout):
        """Test coach retrieving client's assigned workouts."""
        response = await client.get(
            f"/workouts/assignments/client/{client_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Client workouts retrieved successfully"
        assert len(data["data"]) >= 1
        assert data["data"][0]["client_user_id"] == str(client_user.id)
    
    async def test_get_client_workouts_filter_by_status(self, client, auth_headers, client_user, assigned_workout):
        """Test filtering client workouts by status."""
        response = await client.get(
            f"/workouts/assignments/client/{client_user.id}?status_filter=assigned",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for assignment in data["data"]:
            assert assignment["status"] == "assigned"
    
    async def test_get_client_workouts_without_relationship(self, client, another_coach_token, client_user):
        """Test coach cannot view workouts of client without relationship."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        
        response = await client.get(
            f"/workouts/assignments/client/{client_user.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_get_client_workouts_as_client_forbidden(self, client, client_auth_headers, another_client_user):
        """Test client cannot view another client's workouts."""
        response = await client.get(
            f"/workouts/assignments/client/{another_client_user.id}",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============= Update Assignment Tests =============

@pytest.mark.workout
@pytest.mark.unit
class TestUpdateAssignedWorkout:
    """Test suite for PUT /workouts/assignments/{assignment_id} endpoint."""
    
    async def test_coach_update_assignment(self, client, auth_headers, assigned_workout):
        """Test coach updating assignment details."""
        update_data = {
            "due_date": (date.today() + timedelta(days=14)).isoformat(),
            "status": "in_progress",
            "coach_notes": "Updated notes from coach"
        }
        
        response = await client.put(
            f"/workouts/assignments/{assigned_workout.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Assignment updated successfully"
        assert data["data"]["coach_notes"] == update_data["coach_notes"]
        assert data["data"]["status"] == update_data["status"]
    
    async def test_client_update_assignment(self, client, client_auth_headers, assigned_workout):
        """Test client updating their assignment status and notes."""
        update_data = {
            "status": "completed",
            "client_notes": "Finished all sets successfully!"
        }
        
        response = await client.put(
            f"/workouts/assignments/{assigned_workout.id}",
            json=update_data,
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["status"] == update_data["status"]
        assert data["data"]["client_notes"] == update_data["client_notes"]
    
    async def test_client_cannot_update_coach_fields(self, client, client_auth_headers, assigned_workout):
        """Test client cannot update coach-specific fields."""
        update_data = {
            "coach_notes": "Hacking coach notes",
            "due_date": (date.today() + timedelta(days=30)).isoformat()
        }
        
        response = await client.put(
            f"/workouts/assignments/{assigned_workout.id}",
            json=update_data,
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Coach notes should not be updated by client
        assert data["data"]["coach_notes"] != update_data["coach_notes"]
    
    async def test_update_another_clients_assignment(self, client, another_client_token, assigned_workout):
        """Test client cannot update another client's assignment."""
        headers = {"Authorization": f"Bearer {another_client_token}"}
        update_data = {"status": "completed"}
        
        response = await client.put(
            f"/workouts/assignments/{assigned_workout.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_update_nonexistent_assignment(self, client, auth_headers):
        """Test updating non-existent assignment."""
        fake_id = uuid4()
        update_data = {"status": "completed"}
        
        response = await client.put(
            f"/workouts/assignments/{fake_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============= Delete Assignment Tests =============

@pytest.mark.workout
@pytest.mark.unit
class TestDeleteAssignedWorkout:
    """Test suite for DELETE /workouts/assignments/{assignment_id} endpoint."""
    
    async def test_delete_assignment_success(self, client, auth_headers, assigned_workout):
        """Test coach successfully deleting assignment."""
        response = await client.delete(
            f"/workouts/assignments/{assigned_workout.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Assignment deleted successfully"
    
    async def test_delete_assignment_by_different_coach(self, client, another_coach_token, assigned_workout):
        """Test coach cannot delete another coach's assignment."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        
        response = await client.delete(
            f"/workouts/assignments/{assigned_workout.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_delete_assignment_as_client_forbidden(self, client, client_auth_headers, assigned_workout):
        """Test client cannot delete assignments."""
        response = await client.delete(
            f"workouts/assignments/{assigned_workout.id}",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_delete_nonexistent_assignment(self, client, auth_headers):
        """Test deleting non-existent assignment."""
        fake_id = uuid4()
        
        response = await client.delete(
            f"workouts/assignments/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============= Integration Tests =============

@pytest.mark.workout
@pytest.mark.integration
class TestAssignmentWorkflow:
    """Integration tests for complete assignment workflows."""
    
    async def test_complete_assignment_lifecycle(
        self, client, auth_headers, client_auth_headers,
        sample_workout, client_user, coach_client_relationship
    ):
        """Test complete workflow: assign, view, update, delete."""
        # 1. Coach assigns workout
        assignment_data = create_assignment_data(
            str(sample_workout.id),
            str(client_user.id)
        )
        assign_response = await client.post(
            "/workouts/assignments",
            json=assignment_data,
            headers=auth_headers
        )
        assert assign_response.status_code == status.HTTP_201_CREATED
        assignment_id = assign_response.json()["data"]["id"]
        
        # 2. Client views their workouts
        view_response = await client.get(
            "/workouts/assignments/my-workouts",
            headers=client_auth_headers
        )
        assert view_response.status_code == status.HTTP_200_OK
        assert len(view_response.json()["data"]) >= 1
        
        # 3. Client updates status
        client_update = {
            "status": "in_progress",
            "client_notes": "Started today"
        }
        client_update_response = await client.put(
            f"/workouts/assignments/{assignment_id}",
            json=client_update,
            headers=client_auth_headers
        )
        assert client_update_response.status_code == status.HTTP_200_OK
        
        # 4. Coach checks progress
        coach_check_response = await client.get(
            f"/workouts/assignments/client/{client_user.id}",
            headers=auth_headers
        )
        assert coach_check_response.status_code == status.HTTP_200_OK
        assignments = coach_check_response.json()["data"]
        assert any(a["status"] == "in_progress" for a in assignments)
        
        # 5. Client completes workout
        complete_update = {"status": "completed"}
        complete_response = await client.put(
            f"/workouts/assignments/{assignment_id}",
            json=complete_update,
            headers=client_auth_headers
        )
        assert complete_response.status_code == status.HTTP_200_OK
        assert complete_response.json()["data"]["status"] == "completed"
    
    async def test_multiple_assignments_to_same_client(
        self, client, auth_headers, client_auth_headers, sample_workout, workout_template,
        client_user, coach_client_relationship
    ):
        """Test assigning multiple workouts to the same client."""
        # Assign first workout
        assignment1_data = create_assignment_data(
            str(sample_workout.id),
            str(client_user.id)
        )
        response1 = await client.post(
            "/workouts/assignments",
            json=assignment1_data,
            headers=auth_headers
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Assign second workout
        assignment2_data = create_assignment_data(
            str(workout_template.id),
            str(client_user.id)
        )
        response2 = await client.post(
            "/workouts/assignments",
            json=assignment2_data,
            headers=auth_headers
        )
        assert response2.status_code == status.HTTP_201_CREATED
        
        # Verify client sees both assignments
        get_response = await client.get(
            "/workouts/assignments/my-workouts",
            headers=client_auth_headers  # Use client's auth headers to get their workouts
        )
        assert get_response.status_code == status.HTTP_200_OK
        assert len(get_response.json()["data"]) >= 2


# ============= Edge Case Tests =============

@pytest.mark.workout
@pytest.mark.unit
class TestAssignmentEdgeCases:
    """Test edge cases and boundary conditions."""
    
    async def test_assign_workout_past_due_date(self, client, auth_headers, sample_workout, client_user, coach_client_relationship):
        """Test assignment with past due date."""
        assignment_data = create_assignment_data(
            str(sample_workout.id),
            str(client_user.id)
        )
        # Set due date in the past
        assignment_data["due_date"] = (date.today() - timedelta(days=1)).isoformat()
        
        response = await client.post(
            "/workouts/assignments",
            json=assignment_data,
            headers=auth_headers
        )
        
        # Should still create the assignment (business logic might vary)
        assert response.status_code == status.HTTP_201_CREATED
    
    async def test_update_assignment_all_status_transitions(self, client, client_user, client_token, db_session, sample_workout, coach_client_relationship):
        """Test all valid status transitions."""
        from models.assigned_workout import AssignedWorkout, AssignmentStatus
        
        # Create fresh assignment for this test
        assignment = AssignedWorkout(
            id=uuid4(),
            workout_id=sample_workout.id,
            coach_client_relationship_id=coach_client_relationship.id,
            coach_user_id=coach_client_relationship.coach_user_id,
            client_user_id=client_user.id,
            assigned_date=date.today(),
            status=AssignmentStatus.ASSIGNED
        )
        db_session.add(assignment)
        await db_session.commit()
        
        client_headers = {"Authorization": f"Bearer {client_token}"}
        statuses = ["in_progress", "completed", "skipped"]
        
        for status_value in statuses:
            update_data = {"status": status_value}
            response = await client.put(
                f"/workouts/assignments/{assignment.id}",
                json=update_data,
                headers=client_headers
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["data"]["status"] == status_value
