"""
Tests for S3 Service functionality.

These tests verify the S3 service operations including:
- Presigned URL generation
- File validation
- S3 key generation
- File metadata extraction
"""

import pytest
from uuid import uuid4
from core.s3_service import S3Service, get_s3_service
from unittest.mock import patch
from botocore.exceptions import ClientError


@pytest.fixture
def mock_s3_client():
    """Mock boto3 S3 client."""
    with patch('core.s3_service.boto3.client') as mock_client:
        yield mock_client.return_value


@pytest.fixture
def s3_service(mock_s3_client):
    """Create S3Service instance with mocked client."""
    with patch('core.s3_service.settings') as mock_settings:
        mock_settings.AWS_S3_BUCKET_NAME = 'test-bucket'
        mock_settings.AWS_REGION = 'us-east-1'
        mock_settings.AWS_ACCESS_KEY_ID = 'test-key'
        mock_settings.AWS_SECRET_ACCESS_KEY = 'test-secret'
        mock_settings.AWS_CLOUDFRONT_DOMAIN = None
        mock_settings.ENVIRONMENT = 'test'
        
        service = S3Service()
        service.s3_client = mock_s3_client
        return service


class TestS3KeyGeneration:
    """Test S3 key generation and sanitization."""
    
    def test_generate_s3_key_basic(self, s3_service):
        """Test basic S3 key generation."""
        user_id = uuid4()
        exercise_id = uuid4()
        filename = "workout.mp4"
        
        s3_key = s3_service._generate_s3_key(user_id, exercise_id, filename, "video")
        
        assert s3_key.startswith("videos/")
        assert str(user_id) in s3_key
        assert str(exercise_id) in s3_key
        assert filename in s3_key
    
    def test_generate_s3_key_sanitizes_filename(self, s3_service):
        """Test filename sanitization in S3 key."""
        user_id = uuid4()
        exercise_id = uuid4()
        dangerous_filename = "../../../etc/passwd"
        
        s3_key = s3_service._generate_s3_key(user_id, exercise_id, dangerous_filename, "image")
        
        assert "../" not in s3_key
        assert "passwd" in s3_key
        assert s3_key.startswith("images/")
    
    def test_generate_s3_key_removes_path_separators(self, s3_service):
        """Test path separator removal from filename."""
        user_id = uuid4()
        exercise_id = uuid4()
        filename_with_slashes = "path/to/file.jpg"
        
        s3_key = s3_service._generate_s3_key(user_id, exercise_id, filename_with_slashes, "image")
        
        # Should only have slashes from the key structure, not from filename
        parts = s3_key.split('/')
        assert len(parts) == 4  # images/{user_id}/{exercise_id}/{timestamp_filename}
        assert 'path' not in parts[-1] or 'to' not in parts[-1]


class TestFileValidation:
    """Test file type and size validation."""
    
    def test_validate_valid_image(self, s3_service):
        """Test validation of valid image file."""
        is_valid, mime_type = s3_service._validate_file_type("photo.jpg", "image")
        
        assert is_valid is True
        assert mime_type == "image/jpeg"
    
    def test_validate_valid_video(self, s3_service):
        """Test validation of valid video file."""
        is_valid, mime_type = s3_service._validate_file_type("workout.mp4", "video")
        
        assert is_valid is True
        assert mime_type == "video/mp4"
    
    def test_validate_invalid_extension(self, s3_service):
        """Test rejection of invalid file extension."""
        is_valid, mime_type = s3_service._validate_file_type("document.pdf", "image")
        
        assert is_valid is False
        assert mime_type is None
    
    def test_validate_case_insensitive(self, s3_service):
        """Test case-insensitive file extension validation."""
        is_valid, mime_type = s3_service._validate_file_type("PHOTO.JPG", "image")
        
        assert is_valid is True
        assert mime_type in ["image/jpeg", "image/jpg"]
    
    @pytest.mark.parametrize("filename,media_type,expected_valid", [
        ("test.jpg", "image", True),
        ("test.png", "image", True),
        ("test.gif", "image", True),
        ("test.webp", "image", True),
        ("test.mp4", "video", True),
        ("test.mov", "video", True),
        ("test.avi", "video", True),
        ("test.webm", "video", True),
        ("test.exe", "image", False),
        ("test.txt", "video", False),
        ("test.mp4", "image", False),
        ("test.jpg", "video", False),
    ])
    def test_various_file_types(self, s3_service, filename, media_type, expected_valid):
        """Test various file type combinations."""
        is_valid, _ = s3_service._validate_file_type(filename, media_type)
        assert is_valid == expected_valid


class TestPresignedURLGeneration:
    """Test presigned URL generation."""
    
    def test_generate_presigned_upload_url_success(self, s3_service, mock_s3_client):
        """Test successful presigned URL generation."""
        mock_s3_client.generate_presigned_url.return_value = "https://bucket.s3.amazonaws.com/presigned-url"
        
        user_id = uuid4()
        exercise_id = uuid4()
        
        result = s3_service.generate_presigned_upload_url(
            user_id=user_id,
            exercise_id=exercise_id,
            filename="workout.mp4",
            media_type="video",
            file_size_mb=50
        )
        
        assert 'upload_url' in result
        assert 'media_url' in result
        assert 's3_key' in result
        assert 'content_type' in result
        assert 'expires_at' in result
        assert result['content_type'] == 'video/mp4'
    
    def test_generate_presigned_upload_url_file_too_large(self, s3_service):
        """Test rejection of oversized files."""
        user_id = uuid4()
        exercise_id = uuid4()
        
        with pytest.raises(ValueError, match="exceeds maximum allowed size"):
            s3_service.generate_presigned_upload_url(
                user_id=user_id,
                exercise_id=exercise_id,
                filename="huge.mp4",
                media_type="video",
                file_size_mb=150  # Exceeds 100MB limit
            )
    
    def test_generate_presigned_upload_url_invalid_type(self, s3_service):
        """Test rejection of invalid file type."""
        user_id = uuid4()
        exercise_id = uuid4()
        
        with pytest.raises(ValueError, match="Invalid file type"):
            s3_service.generate_presigned_upload_url(
                user_id=user_id,
                exercise_id=exercise_id,
                filename="document.pdf",
                media_type="image",
                file_size_mb=5
            )
    
    

class TestS3URLParsing:
    """Test S3 URL parsing and key extraction."""
    
    def test_extract_s3_key_from_standard_url(self, s3_service):
        """Test extracting key from standard S3 URL."""
        url = "https://bucket.s3.us-east-1.amazonaws.com/videos/user/exercise/file.mp4"
        
        key = s3_service.extract_s3_key_from_url(url)
        
        assert key == "videos/user/exercise/file.mp4"
    
    
    def test_extract_s3_key_from_s3_protocol(self, s3_service):
        """Test extracting key from s3:// protocol URL."""
        url = "s3://bucket/videos/user/exercise/file.mp4"
        
        key = s3_service.extract_s3_key_from_url(url)
        
        assert key == "videos/user/exercise/file.mp4"
    
    def test_extract_s3_key_invalid_url(self, s3_service):
        """Test handling of invalid URL."""
        url = "https://example.com/not-an-s3-url"
        
        key = s3_service.extract_s3_key_from_url(url)
        
        assert key is None


class TestFileOperations:
    """Test file operations (delete, verify, metadata)."""
    
    def test_delete_file_success(self, s3_service, mock_s3_client):
        """Test successful file deletion."""
        s3_key = "videos/user/exercise/file.mp4"
        
        result = s3_service.delete_file(s3_key)
        
        assert result is True
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key=s3_key
        )
    
    def test_delete_file_error(self, s3_service, mock_s3_client):
        """Test file deletion error handling."""
        mock_s3_client.delete_object.side_effect = ClientError(
            {'Error': {'Code': '500', 'Message': 'Internal Error'}},
            'DeleteObject'
        )
        
        result = s3_service.delete_file("some-key")
        
        assert result is False
    
    def test_verify_file_exists_true(self, s3_service, mock_s3_client):
        """Test file existence verification when file exists."""
        mock_s3_client.head_object.return_value = {'ContentLength': 1000}
        
        exists = s3_service.verify_file_exists("videos/test.mp4")
        
        assert exists is True
    
    def test_verify_file_exists_false(self, s3_service, mock_s3_client):
        """Test file existence verification when file doesn't exist."""
        mock_s3_client.head_object.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}},
            'HeadObject'
        )
        
        exists = s3_service.verify_file_exists("videos/nonexistent.mp4")
        
        assert exists is False
    
    def test_get_file_metadata_success(self, s3_service, mock_s3_client):
        """Test retrieving file metadata."""
        mock_s3_client.head_object.return_value = {
            'ContentType': 'video/mp4',
            'ContentLength': 5000000,
            'LastModified': '2025-11-15',
            'Metadata': {'user_id': 'test-user'}
        }
        
        metadata = s3_service.get_file_metadata("videos/test.mp4")
        
        assert metadata is not None
        assert metadata['content_type'] == 'video/mp4'
        assert metadata['content_length'] == 5000000
        assert metadata['metadata']['user_id'] == 'test-user'


class TestS3ServiceSingleton:
    """Test S3 service singleton pattern."""
    
    def test_get_s3_service_singleton(self):
        """Test that get_s3_service returns same instance."""
        with patch('core.s3_service.S3Service'):
            service1 = get_s3_service()
            service2 = get_s3_service()
            
            assert service1 is service2
