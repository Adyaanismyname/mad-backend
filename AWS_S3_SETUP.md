# AWS S3 Media Management - Setup & Usage Guide

## Overview

This guide covers the AWS S3 integration for media upload and management in the Gym-App backend.

## Features

- Presigned URLs for secure direct uploads
- Content type validation
- File size limits (10MB for images, 100MB for videos)
- Access control based on user roles
- Secure deletion from both S3 and database


- Direct client-to-S3 uploads (bypasses API server)
- Retry logic and timeout configuration


- Structured S3 key format: `{media_type}s/{user_id}/{exercise_id}/{timestamp}_{filename}`
- Prevents filename collisions
- Easy user/exercise-based queries

## AWS S3 Setup

### 1. Create an S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://your-gym-app-media-bucket --region us-east-1

# Or use AWS Console: https://console.aws.amazon.com/s3/
```

### 2. Configure Bucket Policy

Set up CORS for direct browser uploads:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["PUT", "POST", "GET"],
        "AllowedOrigins": [""],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
```

### 3. Create IAM User for Programmatic Access and save the Access Key ID and Secret Access Key


## Environment Configuration

Add these variables to your `.env` file:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-gym-app-media-bucket


# Environment
ENVIRONMENT=production
```

### Environment Variable Details

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | Yes | IAM user access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Yes | IAM user secret key | `wJalrXUtnFEMI/K7MDENG...` |
| `AWS_REGION` | No | AWS region | `us-east-1` (default) |
| `AWS_S3_BUCKET_NAME` | Yes | S3 bucket name | `gym-app-media` |
| `ENVIRONMENT` | No | Environment name | `development`, `staging`, `production` |

## Database Migration

Run the migration to add the `s3_key` column:

```bash
# Apply migration
alembic upgrade head

# Or if using a specific migration
alembic upgrade add_s3_key_to_media
```

## API Endpoints

### 1. Initiate Upload

**POST** `/media/initiate-upload`

Request a presigned URL for uploading media.

**Request Body:**
```json
{
  "assigned_workout_id": "uuid-optional",
  "exercise_id": "uuid-required",
  "filename": "workout_video.mp4",
  "media_type": "video",
  "file_size_mb": 45.5
}
```

**Response:**
```json
{
  "data": {
    "upload_url": "https://bucket.s3.amazonaws.com/path?signature=...",
    "media_url": "https://bucket.s3.amazonaws.com/videos/user-id/exercise-id/20251115_120000_workout_video.mp4",
    "s3_key": "videos/user-id/exercise-id/20251115_120000_workout_video.mp4",
    "content_type": "video/mp4",
    "expires_at": "2025-11-15T13:00:00Z",
    "upload_id": "uuid-for-confirmation"
  },
  "message": "Presigned upload URL generated successfully"
}
```

**Client Upload (JavaScript Example):**
```javascript
const response = await fetch('/media/initiate-upload', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    exercise_id: 'exercise-uuid',
    filename: file.name,
    media_type: 'video',
    file_size_mb: file.size / (1024 * 1024)
  })
});

const { data } = await response.json();

// Upload directly to S3
await fetch(data.upload_url, {
  method: 'PUT',
  headers: {
    'Content-Type': data.content_type
  },
  body: file
});

// Confirm upload
await fetch('/media/confirm-upload', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    upload_id: data.upload_id,
    exercise_id: 'exercise-uuid'
  })
});
```

### 2. Confirm Upload

**POST** `/media/confirm-upload`

Confirm successful upload and save metadata.

**Request Body:**
```json
{
  "upload_id": "uuid-from-initiate-response",
  "assigned_workout_id": "uuid-optional",
  "exercise_id": "uuid-required"
}
```

**Response:**
```json
{
  "data": {
    "id": "media-uuid",
    "client_user_id": "user-uuid",
    "exercise_id": "exercise-uuid",
    "media_url": "https://bucket.s3.amazonaws.com/...",
    "media_type": "video",
    "status": "ready",
    "created_at": "2025-11-15T12:00:00Z"
  },
  "message": "Media upload confirmed successfully"
}
```

### 3. Get Media Details

**GET** `/media/{media_id}`

Get information about a specific media upload.

### 4. Delete Media

**DELETE** `/media/{media_id}`

Delete media from both S3 and database.

### 5. Generate Download URL

**POST** `/media/{media_id}/generate-download-url`

Generate a temporary presigned download URL (expires in 1 hour).

**Response:**
```json
{
  "data": {
    "download_url": "https://bucket.s3.amazonaws.com/path?signature=...",
    "expires_in_seconds": 3600
  },
  "message": "Download URL generated successfully"
}
```

### 6. List Media

**GET** `/media/my-uploads`

Query Parameters:
- `assigned_workout_id` (optional)
- `exercise_id` (optional)

**GET** `/media/client/{client_id}` (Coach only)

## Supported File Types

### Images
- **Extensions:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **MIME Types:** `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- **Max Size:** 10 MB

### Videos
- **Extensions:** `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv`
- **MIME Types:** `video/mp4`, `video/quicktime`, `video/x-msvideo`, `video/webm`, `video/x-matroska`
- **Max Size:** 100 MB


## Error Handling

| Status Code | Description |
|-------------|-------------|
| 400 | Invalid file type or size |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (not owner or no coach relationship) |
| 404 | Media not found |
| 422 | Invalid exercise/workout ID |
| 500 | Server error |

## Additional Considerations

### 1. Cleanup Jobs

Implement background job to clean orphaned S3 files (files in S3 but not in DB) older than 24 hours.


### 2. Monitoring

- Track S3 API errors
- Monitor upload success rates
- Alert on quota limits
- Log deletion operations

### 3. Bucket Lifecycle Policies

Configure S3 lifecycle rules:



## Testing

### Manual Test with cURL

```bash
# 1. Initiate upload
curl -X POST http://localhost:8000/media/initiate-upload \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_id": "uuid",
    "filename": "test.mp4",
    "media_type": "video",
    "file_size_mb": 10
  }'

# 2. Upload to S3 (use upload_url from response)
curl -X PUT "<upload_url>" \
  -H "Content-Type: video/mp4" \
  --data-binary "@test.mp4"

# 3. Confirm upload
curl -X POST http://localhost:8000/media/confirm-upload \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "uuid-from-step-1",
    "exercise_id": "uuid"
  }'
```
