"""
Test cases for Feedback and Media Upload Endpoints.

This module tests media upload operations, feedback creation, and
hierarchical feedback retrieval following FastAPI testing best practices.
"""

import pytest
from fastapi import status
from uuid import uuid4

from tests.conftest import create_media_data, create_feedback_data


# ============= Media Upload Tests =============

@pytest.mark.feedback
@pytest.mark.media
@pytest.mark.unit
class TestUploadMedia:
    """Test suite for POST /feedback/media endpoint."""
    
    async def test_upload_media_success(self, client, client_auth_headers, sample_exercise, assigned_workout):
        """Test successful media upload by client."""
        media_data = create_media_data(
            str(sample_exercise.id),
            str(assigned_workout.id)
        )
        
        response = await client.post(
            "/feedback/media",
            json=media_data,
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Media uploaded successfully"
        assert data["data"]["exercise_id"] == str(sample_exercise.id)
        assert data["data"]["media_type"] == "video"
        assert data["data"]["status"] == "ready"
        assert "id" in data["data"]
    
    async def test_upload_media_without_assignment(self, client, client_auth_headers, sample_exercise):
        """Test uploading media without assigned workout."""
        media_data = create_media_data(str(sample_exercise.id))
        
        response = await client.post(
            "/feedback/media",
            json=media_data,
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["data"]["assigned_workout_id"] is None
    
    async def test_upload_media_unauthorized(self, client, sample_exercise):
        """Test media upload without authentication."""
        media_data = create_media_data(str(sample_exercise.id))
        
        response = await client.post("/feedback/media", json=media_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    async def test_upload_media_invalid_exercise(self, client, client_auth_headers):
        """Test uploading media with invalid exercise ID."""
        media_data = create_media_data(str(uuid4()))
        
        response = await client.post(
            "/feedback/media",
            json=media_data,
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    async def test_upload_media_to_another_clients_assignment(self, client, another_client_token, sample_exercise, assigned_workout):
        """Test client cannot upload media to another client's assignment."""
        headers = {"Authorization": f"Bearer {another_client_token}"}
        media_data = create_media_data(
            str(sample_exercise.id),
            str(assigned_workout.id)
        )
        
        response = await client.post(
            "/feedback/media",
            json=media_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_upload_image_media(self, client, client_auth_headers, sample_exercise):
        """Test uploading image type media."""
        media_data = create_media_data(str(sample_exercise.id))
        media_data["media_type"] = "image"
        media_data["media_url"] = "https://storage.example.com/image.jpg"
        
        response = await client.post(
            "/feedback/media",
            json=media_data,
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["media_type"] == "image"


@pytest.mark.feedback
@pytest.mark.media
@pytest.mark.unit
class TestGetMyMediaUploads:
    """Test suite for GET /feedback/media/my-uploads endpoint."""
    
    async def test_get_my_uploads(self, client, client_auth_headers, sample_media):
        """Test client retrieving their media uploads."""
        response = await client.get(
            "/feedback/media/my-uploads",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Media uploads retrieved successfully"
        assert len(data["data"]) >= 1
        assert data["data"][0]["id"] == str(sample_media.id)
    
    async def test_get_my_uploads_filter_by_exercise(self, client, client_auth_headers, sample_media):
        """Test filtering uploads by exercise."""
        response = await client.get(
            f"/feedback/media/my-uploads?exercise_id={sample_media.exercise_id}",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for media in data["data"]:
            assert media["exercise_id"] == str(sample_media.exercise_id)
    
    async def test_get_my_uploads_filter_by_assignment(self, client, client_auth_headers, sample_media):
        """Test filtering uploads by assigned workout."""
        response = await client.get(
            f"/feedback/media/my-uploads?assigned_workout_id={sample_media.assigned_workout_id}",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for media in data["data"]:
            assert media["assigned_workout_id"] == str(sample_media.assigned_workout_id)


@pytest.mark.feedback
@pytest.mark.media
@pytest.mark.unit
class TestGetClientMediaUploads:
    """Test suite for GET /feedback/media/client/{client_id} endpoint."""
    
    async def test_coach_get_client_media(self, client, auth_headers, client_user, sample_media):
        """Test coach retrieving client's media uploads."""
        response = await client.get(
            f"/feedback/media/client/{client_user.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Client media retrieved successfully"
        assert len(data["data"]) >= 1
    
    async def test_coach_get_client_media_without_relationship(self, client, another_coach_token, client_user):
        """Test coach cannot view media from client without relationship."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        
        response = await client.get(
            f"/feedback/media/client/{client_user.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_client_cannot_view_other_client_media(self, client, another_client_token, client_user):
        """Test client cannot view another client's media."""
        headers = {"Authorization": f"Bearer {another_client_token}"}
        
        response = await client.get(
            f"/feedback/media/client/{client_user.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.feedback
@pytest.mark.media
@pytest.mark.unit
class TestGetMediaDetails:
    """Test suite for GET /feedback/media/{media_id} endpoint."""
    
    async def test_client_get_own_media(self, client, client_auth_headers, sample_media):
        """Test client viewing their own media details."""
        response = await client.get(
            f"/feedback/media/{sample_media.id}",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Media retrieved successfully"
        assert data["data"]["id"] == str(sample_media.id)
    
    async def test_coach_get_client_media_details(self, client, auth_headers, sample_media):
        """Test coach viewing their client's media."""
        response = await client.get(
            f"/feedback/media/{sample_media.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["id"] == str(sample_media.id)
    
    async def test_unauthorized_media_access(self, client, another_client_token, sample_media):
        """Test unauthorized user cannot view media."""
        headers = {"Authorization": f"Bearer {another_client_token}"}
        
        response = await client.get(
            f"/feedback/media/{sample_media.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_get_nonexistent_media(self, client, client_auth_headers):
        """Test retrieving non-existent media."""
        fake_id = uuid4()
        
        response = await client.get(
            f"/feedback/media/{fake_id}",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.feedback
@pytest.mark.media
@pytest.mark.unit
class TestDeleteMedia:
    """Test suite for DELETE /feedback/media/{media_id} endpoint."""
    
    async def test_delete_own_media(self, client, client_auth_headers, sample_media):
        """Test client deleting their own media."""
        response = await client.delete(
            f"/feedback/media/{sample_media.id}",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Media deleted successfully"
        
        # Verify media is deleted
        get_response = await client.get(
            f"/feedback/media/{sample_media.id}",
            headers=client_auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_client_cannot_delete_other_media(self, client, another_client_token, sample_media):
        """Test client cannot delete another client's media."""
        headers = {"Authorization": f"Bearer {another_client_token}"}
        
        response = await client.delete(
            f"/feedback/media/{sample_media.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_coach_cannot_delete_client_media(self, client, auth_headers, sample_media):
        """Test coach cannot delete client's media."""
        response = await client.delete(
            f"/feedback/media/{sample_media.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============= Feedback Tests =============

@pytest.mark.feedback
@pytest.mark.unit
class TestCreateFeedback:
    """Test suite for POST /feedback/media/{media_id}/feedback endpoint."""
    
    async def test_create_feedback_success(self, client, auth_headers, sample_media):
        """Test coach successfully creating feedback."""
        feedback_data = create_feedback_data("Great form! Keep it up!")
        
        response = await client.post(
            f"/feedback/media/{sample_media.id}/feedback",
            json=feedback_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Feedback created successfully"
        assert data["data"]["content"] == feedback_data["content"]
        assert data["data"]["media_id"] == str(sample_media.id)
        assert "coach_name" in data["data"]
        assert "id" in data["data"]
    
    async def test_create_feedback_with_annotations(self, client, auth_headers, sample_media):
        """Test creating feedback with timestamp annotations."""
        feedback_data = create_feedback_data("Watch elbow position here")
        feedback_data["annotation_data"] = {
            "timestamp": 15.5,
            "type": "form_correction",
            "coordinates": {"x": 120, "y": 300}
        }
        
        response = await client.post(
            f"/feedback/media/{sample_media.id}/feedback",
            json=feedback_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["data"]["annotation_data"]["timestamp"] == 15.5
        assert data["data"]["annotation_data"]["type"] == "form_correction"
    
    async def test_create_threaded_reply(self, client, auth_headers, sample_media, sample_feedback):
        """Test creating a reply to existing feedback."""
        reply_data = create_feedback_data("Follow-up: Try increasing weight")
        reply_data["parent_feedback_id"] = str(sample_feedback.id)
        
        response = await client.post(
            f"/feedback/media/{sample_media.id}/feedback",
            json=reply_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["data"]["parent_feedback_id"] == str(sample_feedback.id)
    
    async def test_client_cannot_create_feedback(self, client, client_auth_headers, sample_media):
        """Test client cannot create feedback."""
        feedback_data = create_feedback_data()
        
        response = await client.post(
            f"/feedback/media/{sample_media.id}/feedback",
            json=feedback_data,
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_coach_feedback_without_relationship(self, client, another_coach_token, sample_media):
        """Test coach cannot provide feedback without relationship."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        feedback_data = create_feedback_data()
        
        response = await client.post(
            f"/feedback/media/{sample_media.id}/feedback",
            json=feedback_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_create_feedback_on_nonexistent_media(self, client, auth_headers):
        """Test creating feedback on non-existent media."""
        fake_id = uuid4()
        feedback_data = create_feedback_data()
        
        response = await client.post(
            f"/feedback/media/{fake_id}/feedback",
            json=feedback_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.feedback
@pytest.mark.unit
class TestGetMediaFeedback:
    """Test suite for GET /feedback/media/{media_id}/feedback endpoint."""
    
    async def test_get_feedback_as_client(self, client, client_auth_headers, sample_media, sample_feedback):
        """Test client viewing feedback on their media."""
        response = await client.get(
            f"/feedback/media/{sample_media.id}/feedback",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Feedback retrieved successfully"
        assert len(data["data"]) >= 1
        assert data["data"][0]["id"] == str(sample_feedback.id)
        assert "coach_name" in data["data"][0]
    
    async def test_get_feedback_as_coach(self, client, auth_headers, sample_media, sample_feedback):
        """Test coach viewing feedback on client's media."""
        response = await client.get(
            f"/feedback/media/{sample_media.id}/feedback",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) >= 1
    
    async def test_get_hierarchical_feedback(self, client, client_auth_headers, sample_media, sample_feedback, auth_headers):
        """Test feedback returned in hierarchical structure."""
        # Create a reply
        reply_data = create_feedback_data("Reply to feedback")
        reply_data["parent_feedback_id"] = str(sample_feedback.id)
        
        await client.post(
            f"/feedback/media/{sample_media.id}/feedback",
            json=reply_data,
            headers=auth_headers
        )
        
        # Get feedback
        response = await client.get(
            f"/feedback/media/{sample_media.id}/feedback",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Find parent feedback
        parent = next((f for f in data["data"] if f["id"] == str(sample_feedback.id)), None)
        assert parent is not None
        assert "replies" in parent
        assert len(parent["replies"]) >= 1
    
    async def test_unauthorized_cannot_view_feedback(self, client, another_client_token, sample_media):
        """Test unauthorized user cannot view feedback."""
        headers = {"Authorization": f"Bearer {another_client_token}"}
        
        response = await client.get(
            f"/feedback/media/{sample_media.id}/feedback",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.feedback
@pytest.mark.unit
class TestGetMediaWithFeedback:
    """Test suite for GET /feedback/media/{media_id}/with-feedback endpoint."""
    
    async def test_get_media_with_feedback(self, client, client_auth_headers, sample_media, sample_feedback):
        """Test getting media with all feedback in one response."""
        response = await client.get(
            f"/feedback/media/{sample_media.id}/with-feedback",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Media with feedback retrieved successfully"
        assert data["data"]["id"] == str(sample_media.id)
        assert "feedback" in data["data"]
        assert len(data["data"]["feedback"]) >= 1
        assert data["data"]["feedback"][0]["id"] == str(sample_feedback.id)
    
    async def test_media_with_no_feedback(self, client, client_auth_headers, client_user, sample_exercise, assigned_workout, db_session):
        """Test media with no feedback returns empty list."""
        from models.media_upload import MediaUpload
        
        # Create media without feedback
        media = MediaUpload(
            id=uuid4(),
            client_user_id=client_user.id,
            assigned_workout_id=assigned_workout.id,
            exercise_id=sample_exercise.id,
            media_url="https://storage.example.com/test.mp4",
            media_type="video",
            status="ready"
        )
        db_session.add(media)
        await db_session.commit()
        
        response = await client.get(
            f"/feedback/media/{media.id}/with-feedback",
            headers=client_auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["data"]["feedback"]) == 0


@pytest.mark.feedback
@pytest.mark.unit
class TestUpdateFeedback:
    """Test suite for PUT /feedback/{feedback_id} endpoint."""
    
    async def test_update_feedback_success(self, client, auth_headers, sample_feedback):
        """Test coach updating their feedback."""
        update_data = {
            "content": "Updated feedback content",
            "annotation_data": {"timestamp": 20.0}
        }
        
        response = await client.put(
            f"/feedback/{sample_feedback.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Feedback updated successfully"
        assert data["data"]["content"] == update_data["content"]
    
    async def test_different_coach_cannot_update(self, client, another_coach_token, sample_feedback):
        """Test coach cannot update another coach's feedback."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        update_data = {"content": "Hacked feedback"}
        
        response = await client.put(
            f"/feedback/{sample_feedback.id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_update_nonexistent_feedback(self, client, auth_headers):
        """Test updating non-existent feedback."""
        fake_id = uuid4()
        update_data = {"content": "Updated"}
        
        response = await client.put(
            f"/feedback/{fake_id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.feedback
@pytest.mark.unit
class TestDeleteFeedback:
    """Test suite for DELETE /feedback/{feedback_id} endpoint."""
    
    async def test_delete_feedback_success(self, client, auth_headers, sample_feedback):
        """Test coach deleting their feedback."""
        response = await client.delete(
            f"/feedback/{sample_feedback.id}",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Feedback deleted successfully"
    
    async def test_different_coach_cannot_delete(self, client, another_coach_token, sample_feedback):
        """Test coach cannot delete another coach's feedback."""
        headers = {"Authorization": f"Bearer {another_coach_token}"}
        
        response = await client.delete(
            f"/feedback/{sample_feedback.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============= Integration Tests =============

@pytest.mark.feedback
@pytest.mark.integration
class TestFeedbackWorkflow:
    """Integration tests for complete feedback workflow."""
    
    async def test_complete_feedback_lifecycle(
        self, client, client_auth_headers, auth_headers,
        sample_exercise, assigned_workout
    ):
        """Test complete workflow: upload media, add feedback, view, update, delete."""
        # 1. Client uploads media
        media_data = create_media_data(
            str(sample_exercise.id),
            str(assigned_workout.id)
        )
        upload_response = await client.post(
            "/feedback/media",
            json=media_data,
            headers=client_auth_headers
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        media_id = upload_response.json()["data"]["id"]
        
        # 2. Coach views client media
        coach_view_response = await client.get(
            f"/feedback/media/{media_id}",
            headers=auth_headers
        )
        assert coach_view_response.status_code == status.HTTP_200_OK
        
        # 3. Coach adds feedback
        feedback_data = create_feedback_data("Great form!")
        feedback_response = await client.post(
            f"/feedback/media/{media_id}/feedback",
            json=feedback_data,
            headers=auth_headers
        )
        assert feedback_response.status_code == status.HTTP_201_CREATED
        feedback_id = feedback_response.json()["data"]["id"]
        
        # 4. Client views feedback
        view_feedback_response = await client.get(
            f"/feedback/media/{media_id}/feedback",
            headers=client_auth_headers
        )
        assert view_feedback_response.status_code == status.HTTP_200_OK
        assert len(view_feedback_response.json()["data"]) >= 1
        
        # 5. Coach updates feedback
        update_data = {"content": "Updated: Excellent form!"}
        update_response = await client.put(
            f"/feedback/{feedback_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == status.HTTP_200_OK
        
        # 6. Get media with feedback combined
        combined_response = await client.get(
            f"/feedback/media/{media_id}/with-feedback",
            headers=client_auth_headers
        )
        assert combined_response.status_code == status.HTTP_200_OK
        assert len(combined_response.json()["data"]["feedback"]) >= 1
