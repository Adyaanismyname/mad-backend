"""
Tests for the two-step S3 upload workflow through API endpoints.

This tests the complete flow:
1. POST /media/initiate-upload -> Get presigned URL
2. Client uploads to S3 using presigned URL
3. POST /media/confirm-upload -> Save to database

These are unit tests with mocked S3, not integration tests.
"""

import pytest
from uuid import uuid4
from fastapi import status
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_s3_service():
    """Mock S3 service for two-step upload tests."""
    with patch('api.endpoints.feedback.media_upload.get_s3_service') as mock:
        service = MagicMock()
        
        # Mock generate_presigned_upload_url
        service.generate_presigned_upload_url.return_value = {
            'upload_url': 'https://test-bucket.s3.amazonaws.com/presigned-url?signature=xyz',
            's3_key': 'videos/user123/exercise456/20251116_120000_workout.mp4',
            'media_url': 'https://test-bucket.s3.us-east-1.amazonaws.com/videos/user123/exercise456/20251116_120000_workout.mp4',
            'content_type': 'video/mp4',
            'expires_at': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        
        # Mock verify_file_exists
        service.verify_file_exists.return_value = True
        
        # Mock get_file_metadata
        service.get_file_metadata.return_value = {
            'content_type': 'video/mp4',
            'content_length': 5000000,
            'last_modified': datetime.now(timezone.utc),
            'metadata': {}
        }
        
        mock.return_value = service
        yield service


class TestTwoStepUploadInitiate:
    """Test Step 1: Initiate upload and get presigned URL."""
    
    def test_initiate_upload_success(
        self, 
        client, 
        authenticated_client_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test successful upload initiation."""
        exercise = assigned_workout.workout.exercises[0]
        
        payload = {
            "exercise_id": str(exercise.exercise_id),
            "assigned_workout_id": str(assigned_workout.id),
            "filename": "my_workout.mp4",
            "media_type": "video",
            "file_size_mb": 25.5
        }
        
        response = client.post(
            "/feedback/media/initiate-upload",
            json=payload,
            headers=authenticated_client_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify response structure
        assert 'upload_url' in data
        assert 'pending_upload_id' in data
        assert 'media_url' in data
        assert 's3_key' in data
        assert 'expires_at' in data
        
        # Verify S3 service was called correctly
        mock_s3_service.generate_presigned_upload_url.assert_called_once()
        call_args = mock_s3_service.generate_presigned_upload_url.call_args
        assert call_args.kwargs['filename'] == "my_workout.mp4"
        assert call_args.kwargs['media_type'] == "video"
        assert call_args.kwargs['file_size_mb'] == 25.5
    
    def test_initiate_upload_invalid_exercise(
        self,
        client,
        authenticated_client_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test upload initiation with invalid exercise ID."""
        payload = {
            "exercise_id": str(uuid4()),  # Random UUID that doesn't exist
            "assigned_workout_id": str(assigned_workout.id),
            "filename": "workout.mp4",
            "media_type": "video",
            "file_size_mb": 10.0
        }
        
        response = client.post(
            "/feedback/media/initiate-upload",
            json=payload,
            headers=authenticated_client_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Exercise not found" in response.json()['detail']
    
    def test_initiate_upload_without_assignment(
        self,
        client,
        authenticated_client_headers,
        exercise,
        mock_s3_service
    ):
        """Test upload initiation without assigned workout."""
        payload = {
            "exercise_id": str(exercise.id),
            "filename": "workout.mp4",
            "media_type": "video",
            "file_size_mb": 10.0
        }
        
        response = client.post(
            "/feedback/media/initiate-upload",
            json=payload,
            headers=authenticated_client_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'upload_url' in data
    
    def test_initiate_upload_file_too_large(
        self,
        client,
        authenticated_client_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test upload initiation with oversized file."""
        exercise = assigned_workout.workout.exercises[0]
        
        # Mock S3 service to raise ValueError for large files
        mock_s3_service.generate_presigned_upload_url.side_effect = ValueError(
            "File size (150.00MB) exceeds maximum allowed size (100MB) for video"
        )
        
        payload = {
            "exercise_id": str(exercise.exercise_id),
            "assigned_workout_id": str(assigned_workout.id),
            "filename": "huge_workout.mp4",
            "media_type": "video",
            "file_size_mb": 150.0
        }
        
        response = client.post(
            "/feedback/media/initiate-upload",
            json=payload,
            headers=authenticated_client_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds maximum" in response.json()['detail']
    
    def test_initiate_upload_invalid_file_type(
        self,
        client,
        authenticated_client_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test upload initiation with invalid file type."""
        exercise = assigned_workout.workout.exercises[0]
        
        # Mock S3 service to raise ValueError for invalid type
        mock_s3_service.generate_presigned_upload_url.side_effect = ValueError(
            "Invalid file type for video. Allowed extensions: .mp4, .mov, .avi, .webm, .mkv"
        )
        
        payload = {
            "exercise_id": str(exercise.exercise_id),
            "assigned_workout_id": str(assigned_workout.id),
            "filename": "workout.exe",
            "media_type": "video",
            "file_size_mb": 10.0
        }
        
        response = client.post(
            "/feedback/media/initiate-upload",
            json=payload,
            headers=authenticated_client_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid file type" in response.json()['detail']


class TestTwoStepUploadConfirm:
    """Test Step 2: Confirm upload and save to database."""
    
    def test_confirm_upload_success(
        self,
        client,
        db_session,
        authenticated_client_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test successful upload confirmation."""
        from models.pending_upload import PendingUpload
        
        exercise = assigned_workout.workout.exercises[0]
        user_id = assigned_workout.assigned_user_id
        
        # Create a pending upload
        pending_upload = PendingUpload(
            user_id=user_id,
            exercise_id=exercise.exercise_id,
            assigned_workout_id=assigned_workout.id,
            s3_key='videos/test/test/20251116_120000_workout.mp4',
            filename='workout.mp4',
            media_type='video',
            file_size_mb=25.5,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db_session.add(pending_upload)
        db_session.commit()
        
        payload = {
            "pending_upload_id": str(pending_upload.id)
        }
        
        response = client.post(
            "/feedback/media/confirm-upload",
            json=payload,
            headers=authenticated_client_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert 'id' in data
        assert data['media_type'] == 'video'
        assert data['filename'] == 'workout.mp4'
        assert 's3_key' in data
        assert data['s3_key'] == 'videos/test/test/20251116_120000_workout.mp4'
        
        # Verify S3 file existence was checked
        mock_s3_service.verify_file_exists.assert_called_once_with(
            'videos/test/test/20251116_120000_workout.mp4'
        )
    
    def test_confirm_upload_pending_not_found(
        self,
        client,
        authenticated_client_headers,
        mock_s3_service
    ):
        """Test confirming with non-existent pending upload."""
        payload = {
            "pending_upload_id": str(uuid4())
        }
        
        response = client.post(
            "/feedback/media/confirm-upload",
            json=payload,
            headers=authenticated_client_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Pending upload not found" in response.json()['detail']
    
    def test_confirm_upload_file_not_in_s3(
        self,
        client,
        db_session,
        authenticated_client_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test confirming upload when file doesn't exist in S3."""
        from models.pending_upload import PendingUpload
        
        exercise = assigned_workout.workout.exercises[0]
        user_id = assigned_workout.assigned_user_id
        
        # Mock S3 service to return file doesn't exist
        mock_s3_service.verify_file_exists.return_value = False
        
        pending_upload = PendingUpload(
            user_id=user_id,
            exercise_id=exercise.exercise_id,
            assigned_workout_id=assigned_workout.id,
            s3_key='videos/test/test/nonexistent.mp4',
            filename='workout.mp4',
            media_type='video',
            file_size_mb=25.5,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db_session.add(pending_upload)
        db_session.commit()
        
        payload = {
            "pending_upload_id": str(pending_upload.id)
        }
        
        response = client.post(
            "/feedback/media/confirm-upload",
            json=payload,
            headers=authenticated_client_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found in S3" in response.json()['detail']
    
    def test_confirm_upload_expired_pending(
        self,
        client,
        db_session,
        authenticated_client_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test confirming expired pending upload."""
        from models.pending_upload import PendingUpload
        
        exercise = assigned_workout.workout.exercises[0]
        user_id = assigned_workout.assigned_user_id
        
        # Create expired pending upload
        pending_upload = PendingUpload(
            user_id=user_id,
            exercise_id=exercise.exercise_id,
            assigned_workout_id=assigned_workout.id,
            s3_key='videos/test/test/expired.mp4',
            filename='workout.mp4',
            media_type='video',
            file_size_mb=25.5,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        )
        db_session.add(pending_upload)
        db_session.commit()
        
        payload = {
            "pending_upload_id": str(pending_upload.id)
        }
        
        response = client.post(
            "/feedback/media/confirm-upload",
            json=payload,
            headers=authenticated_client_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "expired" in response.json()['detail'].lower()
    
    def test_confirm_upload_unauthorized_user(
        self,
        client,
        db_session,
        authenticated_client_headers,
        authenticated_coach_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test user cannot confirm another user's pending upload."""
        from models.pending_upload import PendingUpload
        
        exercise = assigned_workout.workout.exercises[0]
        user_id = assigned_workout.assigned_user_id
        
        pending_upload = PendingUpload(
            user_id=user_id,
            exercise_id=exercise.exercise_id,
            s3_key='videos/test/test/workout.mp4',
            filename='workout.mp4',
            media_type='video',
            file_size_mb=25.5,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db_session.add(pending_upload)
        db_session.commit()
        
        payload = {
            "pending_upload_id": str(pending_upload.id)
        }
        
        # Try to confirm with different user (coach)
        response = client.post(
            "/feedback/media/confirm-upload",
            json=payload,
            headers=authenticated_coach_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not authorized" in response.json()['detail'].lower()


class TestCompleteWorkflow:
    """Test complete end-to-end two-step workflow."""
    
    def test_complete_two_step_workflow(
        self,
        client,
        db_session,
        authenticated_client_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test complete workflow from initiation to confirmation."""
        exercise = assigned_workout.workout.exercises[0]
        
        # Step 1: Initiate upload
        initiate_payload = {
            "exercise_id": str(exercise.exercise_id),
            "assigned_workout_id": str(assigned_workout.id),
            "filename": "complete_workflow.mp4",
            "media_type": "video",
            "file_size_mb": 30.0
        }
        
        initiate_response = client.post(
            "/feedback/media/initiate-upload",
            json=initiate_payload,
            headers=authenticated_client_headers
        )
        
        assert initiate_response.status_code == status.HTTP_200_OK
        initiate_data = initiate_response.json()
        
        pending_upload_id = initiate_data['pending_upload_id']
        upload_url = initiate_data['upload_url']
        
        # Verify we got a presigned URL
        assert upload_url.startswith('https://')
        assert 'signature=' in upload_url or 'Signature=' in upload_url
        
        # Step 2: Simulate client uploading to S3
        # (In real scenario, client would PUT to upload_url)
        # For this test, we just verify the URL was generated
        
        # Step 3: Confirm upload
        confirm_payload = {
            "pending_upload_id": pending_upload_id
        }
        
        confirm_response = client.post(
            "/feedback/media/confirm-upload",
            json=confirm_payload,
            headers=authenticated_client_headers
        )
        
        assert confirm_response.status_code == status.HTTP_201_CREATED
        confirm_data = confirm_response.json()
        
        # Verify media upload was created
        assert 'id' in confirm_data
        assert confirm_data['filename'] == 'complete_workflow.mp4'
        assert confirm_data['media_type'] == 'video'
        assert 's3_key' in confirm_data
        
        # Verify pending upload was marked as confirmed
        from models.pending_upload import PendingUpload
        pending = db_session.query(PendingUpload).filter_by(
            id=pending_upload_id
        ).first()
        assert pending is not None
        assert pending.status == 'confirmed'
        assert pending.confirmed_at is not None
    
    def test_workflow_with_image(
        self,
        client,
        db_session,
        authenticated_client_headers,
        assigned_workout,
        mock_s3_service
    ):
        """Test workflow with image file."""
        # Reconfigure mock for image
        mock_s3_service.generate_presigned_upload_url.return_value = {
            'upload_url': 'https://test-bucket.s3.amazonaws.com/presigned-url',
            's3_key': 'images/user123/exercise456/20251116_120000_photo.jpg',
            'media_url': 'https://test-bucket.s3.us-east-1.amazonaws.com/images/user123/exercise456/20251116_120000_photo.jpg',
            'content_type': 'image/jpeg',
            'expires_at': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        
        exercise = assigned_workout.workout.exercises[0]
        
        # Initiate
        initiate_response = client.post(
            "/feedback/media/initiate-upload",
            json={
                "exercise_id": str(exercise.exercise_id),
                "assigned_workout_id": str(assigned_workout.id),
                "filename": "form_check.jpg",
                "media_type": "image",
                "file_size_mb": 2.5
            },
            headers=authenticated_client_headers
        )
        
        assert initiate_response.status_code == status.HTTP_200_OK
        
        # Confirm
        confirm_response = client.post(
            "/feedback/media/confirm-upload",
            json={
                "pending_upload_id": initiate_response.json()['pending_upload_id']
            },
            headers=authenticated_client_headers
        )
        
        assert confirm_response.status_code == status.HTTP_201_CREATED
        assert confirm_response.json()['media_type'] == 'image'
