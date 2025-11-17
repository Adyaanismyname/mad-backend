"""
AWS S3 Service for secure media upload and management.

This module provides production-grade S3 integration with security best practices:
- Presigned URLs for secure direct uploads
- File validation and sanitization
- Access control and permissions
- Automatic cleanup on deletion
- Content type validation
- File size limits
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config
import mimetypes
import os
from typing import Optional, Dict, Any, Literal
from datetime import datetime, timedelta, timezone
from uuid import UUID
import logging

from core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """
    Secure S3 service for media management.
    
    Features:
    - Presigned URL generation for direct client uploads
    - Secure file deletion
    - Public/private access control
    - Content type validation
    - Structured file organization
    """
    
    # Allowed file types and their max sizes (in MB)
    ALLOWED_TYPES = {
        'image': {
            'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            'mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            'max_size_mb': 10
        },
        'video': {
            'extensions': ['.mp4', '.mov', '.avi', '.webm', '.mkv'],
            'mime_types': ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/x-matroska'],
            'max_size_mb': 100
        }
    }
    
    def __init__(self):
        """Initialize S3 client with security configuration."""
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        
        # Configure with retry logic and timeouts
        config = Config(
            region_name=settings.AWS_REGION,
            signature_version='s3v4',
            retries={
                'max_attempts': 3,
                'mode': 'standard'
            },
            connect_timeout=5,
            read_timeout=30
        )
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=config
        )
        
        # Verify bucket exists (optional, can be disabled in production)
        if settings.ENVIRONMENT == 'development':
            self._verify_bucket_exists()
    
    def _verify_bucket_exists(self) -> None:
        """Verify that the S3 bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 bucket '{self.bucket_name}' is accessible")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                logger.error(f"S3 bucket '{self.bucket_name}' does not exist")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                logger.error(f"Error accessing S3 bucket: {e}")
    
    def _generate_s3_key(
        self,
        user_id: UUID,
        exercise_id: UUID,
        filename: str,
        media_type: Literal['image', 'video']
    ) -> str:
        """
        Generate a secure, organized S3 key (path) for the file.
        
        Structure: {media_type}/{user_id}/{exercise_id}/{timestamp}_{filename}
        
        This structure:
        - Organizes files by type
        - Isolates user content
        - Groups by exercise
        - Prevents filename collisions with timestamps
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        # Sanitize filename - remove path separators and dangerous characters
        safe_filename = os.path.basename(filename).replace('..', '').replace('/', '_').replace('\\', '_')
        
        return f"{media_type}s/{user_id}/{exercise_id}/{timestamp}_{safe_filename}"
    
    def _validate_file_type(
        self,
        filename: str,
        media_type: Literal['image', 'video']
    ) -> tuple[bool, Optional[str]]:
        """
        Validate file type against allowed extensions and return MIME type.
        
        Returns:
            tuple: (is_valid, mime_type)
        """
        file_ext = os.path.splitext(filename)[1].lower()
        allowed_config = self.ALLOWED_TYPES.get(media_type)
        
        if not allowed_config:
            return False, None
        
        if file_ext not in allowed_config['extensions']:
            return False, None
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        
        # Validate MIME type
        if mime_type and mime_type in allowed_config['mime_types']:
            return True, mime_type
        
        # Fallback to first allowed MIME type if guess fails
        return True, allowed_config['mime_types'][0]
    
    def generate_presigned_upload_url(
        self,
        user_id: UUID,
        exercise_id: UUID,
        filename: str,
        media_type: Literal['image', 'video'],
        file_size_mb: float,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Generate a presigned URL for secure direct upload to S3.
        
        This allows clients to upload directly to S3 without going through the API server,
        improving performance and reducing server load.
        
        Args:
            user_id: ID of the user uploading
            exercise_id: ID of the associated exercise
            filename: Original filename
            media_type: Type of media ('image' or 'video')
            file_size_mb: File size in megabytes
            expires_in: URL expiration time in seconds (default 1 hour)
        
        Returns:
            dict: {
                'upload_url': str,  # Presigned URL for PUT request
                's3_key': str,      # S3 object key
                'media_url': str,   # Final URL to store in database
                'expires_at': str   # ISO format expiration timestamp
            }
        
        Raises:
            ValueError: If file type or size is invalid
            Exception: If S3 operation fails
        """
        # Validate file type
        is_valid, mime_type = self._validate_file_type(filename, media_type)
        if not is_valid:
            allowed_exts = ', '.join(self.ALLOWED_TYPES[media_type]['extensions'])
            raise ValueError(
                f"Invalid file type for {media_type}. Allowed extensions: {allowed_exts}"
            )
        
        # Validate file size
        max_size = self.ALLOWED_TYPES[media_type]['max_size_mb']
        if file_size_mb > max_size:
            raise ValueError(
                f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({max_size}MB) for {media_type}"
            )
        
        # Generate S3 key
        s3_key = self._generate_s3_key(user_id, exercise_id, filename, media_type)
        
        try:
            # Generate presigned URL with metadata
            # IMPORTANT: Client MUST include these exact metadata headers when uploading
            # or the signature will fail
            metadata = {
                'user-id': str(user_id),
                'exercise-id': str(exercise_id),
                'uploaded-at': datetime.now(timezone.utc).isoformat()
            }
            
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                    'ContentType': mime_type,
                    'Metadata': metadata
                },
                ExpiresIn=expires_in,
                HttpMethod='PUT'
            )
            
            # Generate the final URL (for database storage)
            if settings.AWS_CLOUDFRONT_DOMAIN:
                # Use CloudFront for better performance and caching
                media_url = f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{s3_key}"
            else:
                # Direct S3 URL
                media_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            return {
                'upload_url': presigned_url,
                's3_key': s3_key,
                'media_url': media_url,
                'content_type': mime_type,
                'metadata': metadata,  # Include metadata so client knows what headers to send
                'expires_at': expires_at.isoformat()
            }
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Failed to generate upload URL: {str(e)}")
    
    def generate_presigned_download_url(
        self,
        s3_key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a presigned URL for secure file download.
        
        Useful for private files that shouldn't be publicly accessible.
        
        Args:
            s3_key: S3 object key
            expires_in: URL expiration time in seconds (default 1 hour)
        
        Returns:
            str: Presigned download URL
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expires_in
            )
            return presigned_url
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to generate presigned download URL: {e}")
            raise Exception(f"Failed to generate download URL: {str(e)}")
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Successfully deleted S3 object: {s3_key}")
            return True
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete S3 object {s3_key}: {e}")
            return False
    
    def extract_s3_key_from_url(self, media_url: str) -> Optional[str]:
        """
        Extract S3 key from a media URL.
        
        Handles both direct S3 URLs and CloudFront URLs.
        
        Args:
            media_url: Full media URL
        
        Returns:
            str: S3 key or None if invalid URL
        """
        try:
            # Remove protocol
            url_without_protocol = media_url.replace('https://', '').replace('http://', '')
            
            # Handle CloudFront URL
            if settings.AWS_CLOUDFRONT_DOMAIN and settings.AWS_CLOUDFRONT_DOMAIN in url_without_protocol:
                return url_without_protocol.split(settings.AWS_CLOUDFRONT_DOMAIN + '/', 1)[1]
            
            # Handle direct S3 URL
            # Format: bucket.s3.region.amazonaws.com/key
            if '.s3.' in url_without_protocol and '.amazonaws.com/' in url_without_protocol:
                return url_without_protocol.split('.amazonaws.com/', 1)[1]
            
            # Handle s3://bucket/key format
            if media_url.startswith('s3://'):
                return media_url.split('/', 3)[3]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract S3 key from URL {media_url}: {e}")
            return None
    
    def verify_file_exists(self, s3_key: str) -> bool:
        """
        Verify that a file exists in S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404':
                return False
            logger.error(f"Error checking if S3 object exists: {e}")
            return False
    
    def get_file_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a file in S3.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            dict: File metadata including size, content type, etc.
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to get metadata for {s3_key}: {e}")
            return None


# Singleton instance
_s3_service: Optional[S3Service] = None


def get_s3_service() -> S3Service:
    """
    Get or create S3 service singleton instance.
    
    Returns:
        S3Service: Configured S3 service instance
    """
    global _s3_service
    if _s3_service is None:
        _s3_service = S3Service()
    return _s3_service
