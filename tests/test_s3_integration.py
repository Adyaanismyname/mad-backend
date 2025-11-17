"""
Integration tests for S3 service with real AWS S3.

WARNING: These tests will create and delete files in your S3 bucket!
Only run with a dedicated test bucket.
"""

import pytest
from uuid import uuid4
from core.s3_service import S3Service, get_s3_service
from core.config import settings
import requests


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--s3-integration",
        action="store_true",
        default=False,
        help="Run S3 integration tests (requires real AWS credentials)"
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", 
        "s3_integration: mark test as S3 integration test (requires real AWS)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip S3 integration tests unless --s3-integration flag is provided."""
    if config.getoption("--s3-integration"):
        return
    
    skip_integration = pytest.mark.skip(
        reason="S3 integration tests skipped. Use --s3-integration to run."
    )
    for item in items:
        if "s3_integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture(scope="module")
def s3_service_real():
    """
    Create a real S3Service instance.
    
    Requires valid AWS credentials in environment or .env file.
    """
    # Verify credentials are available
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        pytest.skip("AWS credentials not configured")
    
    if not settings.AWS_S3_BUCKET_NAME:
        pytest.skip("AWS S3 bucket not configured")
    
    return S3Service()


@pytest.fixture
def test_user_id():
    """Generate a test user ID."""
    return uuid4()


@pytest.fixture
def test_exercise_id():
    """Generate a test exercise ID."""
    return uuid4()


@pytest.mark.s3_integration
class TestS3TwoStepUploadWorkflow:
    """
    Test the complete two-step upload workflow:
    1. Generate presigned URL
    2. Upload file to S3 using presigned URL
    3. Verify file exists
    4. Clean up
    """
    
    def test_complete_image_upload_workflow(
        self, 
        s3_service_real, 
        test_user_id, 
        test_exercise_id
    ):
        """Test complete workflow for image upload."""
        # Step 1: Generate presigned URL
        filename = "test_workout_image.jpg"
        file_size_mb = 0.5  # 500KB
        
        presigned_data = s3_service_real.generate_presigned_upload_url(
            user_id=test_user_id,
            exercise_id=test_exercise_id,
            filename=filename,
            media_type="image",
            file_size_mb=file_size_mb
        )
        
        assert 'upload_url' in presigned_data
        assert 'media_url' in presigned_data
        assert 's3_key' in presigned_data
        assert 'content_type' in presigned_data
        assert presigned_data['content_type'] == 'image/jpeg'
        
        s3_key = presigned_data['s3_key']
        upload_url = presigned_data['upload_url']
        
        # Step 2: Create test image data (small JPEG-like data)
        # This is a minimal valid JPEG header + data
        test_image_data = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
            b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
            b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342'
            b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
            b'\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08'
            b'\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9'
        )
        
        # Step 3: Upload to S3 using presigned URL
        headers = {
            'Content-Type': presigned_data['content_type']
        }
        
        # Add metadata headers (x-amz-meta-* format)
        if 'metadata' in presigned_data:
            for key, value in presigned_data['metadata'].items():
                headers[f'x-amz-meta-{key}'] = value
        
        response = requests.put(
            upload_url,
            data=test_image_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        # Step 4: Verify file exists in S3
        exists = s3_service_real.verify_file_exists(s3_key)
        assert exists is True, "File should exist in S3 after upload"
        
        # Step 5: Get file metadata
        metadata = s3_service_real.get_file_metadata(s3_key)
        assert metadata is not None
        assert metadata['content_type'] == 'image/jpeg'
        assert metadata['content_length'] > 0
        
        # Cleanup: Delete the test file
        deleted = s3_service_real.delete_file(s3_key)
        assert deleted is True
        
        # Verify deletion
        exists_after_delete = s3_service_real.verify_file_exists(s3_key)
        assert exists_after_delete is False
    
    def test_complete_video_upload_workflow(
        self, 
        s3_service_real, 
        test_user_id, 
        test_exercise_id
    ):
        """Test complete workflow for video upload."""
        # Step 1: Generate presigned URL
        filename = "test_workout_video.mp4"
        file_size_mb = 1.0  # 1MB
        
        presigned_data = s3_service_real.generate_presigned_upload_url(
            user_id=test_user_id,
            exercise_id=test_exercise_id,
            filename=filename,
            media_type="video",
            file_size_mb=file_size_mb
        )
        
        assert presigned_data['content_type'] == 'video/mp4'
        
        s3_key = presigned_data['s3_key']
        upload_url = presigned_data['upload_url']
        
        # Step 2: Create minimal valid MP4 data
        # This is a minimal MP4 ftyp atom
        test_video_data = (
            b'\x00\x00\x00\x20\x66\x74\x79\x70'  # ftyp box header
            b'\x69\x73\x6f\x6d'  # isom brand
            b'\x00\x00\x02\x00'  # minor version
            b'\x69\x73\x6f\x6d'  # compatible brands
            b'\x69\x73\x6f\x32'
            b'\x61\x76\x63\x31'
            b'\x6d\x70\x34\x31'
        ) * 100  # Repeat to make it bigger
        
        # Step 3: Upload to S3 with metadata headers
        headers = {
            'Content-Type': presigned_data['content_type']
        }
        
        # Add metadata headers to match signature
        if 'metadata' in presigned_data:
            for key, value in presigned_data['metadata'].items():
                headers[f'x-amz-meta-{key}'] = value
        
        response = requests.put(
            upload_url,
            data=test_video_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        # Step 4: Verify and cleanup
        exists = s3_service_real.verify_file_exists(s3_key)
        assert exists is True
        
        # Cleanup
        s3_service_real.delete_file(s3_key)
    
    def test_presigned_url_expiration(
        self, 
        s3_service_real, 
        test_user_id, 
        test_exercise_id
    ):
        """Test that presigned URLs have proper expiration."""
        # Generate URL with 1 hour expiration
        presigned_data = s3_service_real.generate_presigned_upload_url(
            user_id=test_user_id,
            exercise_id=test_exercise_id,
            filename="test.jpg",
            media_type="image",
            file_size_mb=0.1,
            expires_in=3600
        )
        
        # Verify expires_at is in the future
        from datetime import datetime, timezone
        expires_at = datetime.fromisoformat(presigned_data['expires_at'])
        now = datetime.now(timezone.utc)
        
        # Should expire approximately 1 hour from now (allowing 60 seconds tolerance)
        time_diff = (expires_at - now).total_seconds()
        assert 3540 < time_diff < 3660, "Expiration should be ~1 hour from now"
    
    def test_upload_with_dangerous_filename(
        self, 
        s3_service_real, 
        test_user_id, 
        test_exercise_id
    ):
        """Test that dangerous filenames are properly sanitized."""
        dangerous_filename = "../../../etc/passwd.jpg"
        
        presigned_data = s3_service_real.generate_presigned_upload_url(
            user_id=test_user_id,
            exercise_id=test_exercise_id,
            filename=dangerous_filename,
            media_type="image",
            file_size_mb=0.1
        )
        
        s3_key = presigned_data['s3_key']
        
        # Verify the key doesn't contain path traversal
        assert '../' not in s3_key
        assert 'etc' not in s3_key or 'passwd' in s3_key.split('/')[-1]
        
        # Verify proper structure: images/{user_id}/{exercise_id}/{filename}
        parts = s3_key.split('/')
        assert len(parts) == 4
        assert parts[0] == 'images'


@pytest.mark.s3_integration
class TestS3ErrorHandling:
    """Test error handling with real S3."""
    
    def test_invalid_file_type_rejected(
        self, 
        s3_service_real, 
        test_user_id, 
        test_exercise_id
    ):
        """Test that invalid file types are rejected."""
        with pytest.raises(ValueError, match="Invalid file type"):
            s3_service_real.generate_presigned_upload_url(
                user_id=test_user_id,
                exercise_id=test_exercise_id,
                filename="malware.exe",
                media_type="image",
                file_size_mb=0.1
            )
    
    def test_oversized_file_rejected(
        self, 
        s3_service_real, 
        test_user_id, 
        test_exercise_id
    ):
        """Test that oversized files are rejected."""
        with pytest.raises(ValueError, match="exceeds maximum allowed size"):
            s3_service_real.generate_presigned_upload_url(
                user_id=test_user_id,
                exercise_id=test_exercise_id,
                filename="huge_video.mp4",
                media_type="video",
                file_size_mb=150  # Exceeds 100MB limit
            )
    
    def test_delete_nonexistent_file(self, s3_service_real):
        """Test deleting a file that doesn't exist."""
        # Should not raise error, just return success
        # (S3 delete is idempotent)
        result = s3_service_real.delete_file("nonexistent/file.jpg")
        assert result is True
    
    def test_verify_nonexistent_file(self, s3_service_real):
        """Test verifying a file that doesn't exist."""
        exists = s3_service_real.verify_file_exists("definitely/not/a/real/file.mp4")
        assert exists is False


@pytest.mark.s3_integration
class TestS3URLOperations:
    """Test URL generation and parsing with real S3."""
    
    def test_media_url_format(
        self, 
        s3_service_real, 
        test_user_id, 
        test_exercise_id
    ):
        """Test that generated media URLs have correct format."""
        presigned_data = s3_service_real.generate_presigned_upload_url(
            user_id=test_user_id,
            exercise_id=test_exercise_id,
            filename="test.jpg",
            media_type="image",
            file_size_mb=0.1
        )
        
        media_url = presigned_data['media_url']
        
        # Should be HTTPS
        assert media_url.startswith('https://')
        
        # Should contain bucket name (unless using CloudFront)
        if not settings.AWS_CLOUDFRONT_DOMAIN:
            assert settings.AWS_S3_BUCKET_NAME in media_url
        
        # Should end with the S3 key
        assert media_url.endswith(presigned_data['s3_key'])
    
    def test_extract_s3_key_from_generated_url(
        self, 
        s3_service_real, 
        test_user_id, 
        test_exercise_id
    ):
        """Test extracting S3 key from generated media URL."""
        presigned_data = s3_service_real.generate_presigned_upload_url(
            user_id=test_user_id,
            exercise_id=test_exercise_id,
            filename="test.mp4",
            media_type="video",
            file_size_mb=1.0
        )
        
        media_url = presigned_data['media_url']
        expected_s3_key = presigned_data['s3_key']
        
        # Extract key from URL
        extracted_key = s3_service_real.extract_s3_key_from_url(media_url)
        
        assert extracted_key == expected_s3_key


@pytest.mark.s3_integration
class TestS3DownloadURLs:
    """Test presigned download URL generation."""
    
    def test_generate_download_url_for_existing_file(
        self, 
        s3_service_real, 
        test_user_id, 
        test_exercise_id
    ):
        """Test generating download URL for an existing file."""
        # First, upload a file
        presigned_data = s3_service_real.generate_presigned_upload_url(
            user_id=test_user_id,
            exercise_id=test_exercise_id,
            filename="download_test.jpg",
            media_type="image",
            file_size_mb=0.1
        )
        
        # Upload minimal image with metadata headers
        headers = {
            'Content-Type': presigned_data['content_type']
        }
        if 'metadata' in presigned_data:
            for key, value in presigned_data['metadata'].items():
                headers[f'x-amz-meta-{key}'] = value
        
        test_image = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9'
        response = requests.put(
            presigned_data['upload_url'],
            data=test_image,
            headers=headers
        )
        assert response.status_code == 200
        
        try:
            # Generate download URL
            download_url = s3_service_real.generate_presigned_download_url(
                s3_key=presigned_data['s3_key'],
                expires_in=300  # 5 minutes
            )
            
            assert download_url.startswith('https://')
            assert settings.AWS_S3_BUCKET_NAME in download_url
            
            # Try to download the file
            download_response = requests.get(download_url)
            assert download_response.status_code == 200
            assert download_response.content == test_image
            
        finally:
            # Cleanup
            s3_service_real.delete_file(presigned_data['s3_key'])


@pytest.mark.s3_integration
class TestS3ServiceSingleton:
    """Test singleton pattern with real service."""
    
    def test_singleton_returns_same_instance(self):
        """Test that get_s3_service returns the same instance."""
        service1 = get_s3_service()
        service2 = get_s3_service()
        
        assert service1 is service2
        assert isinstance(service1, S3Service)
