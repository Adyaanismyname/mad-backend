# Gym App API - Workout & Feedback Endpoints Documentation

## Overview

This document provides comprehensive documentation for the Workout Management and Feedback/Communication endpoints implemented for the Gym App FastAPI backend.

## Table of Contents

1. [Workout Management Endpoints](#workout-management-endpoints)
2. [Workout Assignment Endpoints](#workout-assignment-endpoints)
3. [Media Upload Endpoints](#media-upload-endpoints)
4. [Feedback & Communication Endpoints](#feedback--communication-endpoints)
5. [Authentication & Authorization](#authentication--authorization)
6. [Data Models](#data-models)

---

## Workout Management Endpoints

### Base URL: `/workouts`

### 1. Create Workout (FR-4.1)

**Endpoint:** `POST /workouts/workouts`

**Description:** Coaches create new workout routines with exercises.

**Authentication:** Required (Coach role)

**Request Body:**
```json
{
  "name": "Full Body Strength",
  "description": "Complete strength training workout",
  "difficulty_level": "intermediate",
  "estimated_duration_minutes": 60,
  "category": "Strength Training",
  "is_template": false,
  "exercises": [
    {
      "exercise_id": "uuid-here",
      "order_index": 1,
      "sets": 3,
      "reps": 12,
      "rest_seconds": 60,
      "notes": "Focus on form"
    }
  ]
}
```

**Response:**
```json
{
  "data": {
    "id": "workout-uuid",
    "coach_id": "coach-uuid",
    "name": "Full Body Strength",
    "description": "Complete strength training workout",
    "difficulty_level": "intermediate",
    "estimated_duration_minutes": 60,
    "category": "Strength Training",
    "is_template": false,
    "created_at": "2025-10-15T10:00:00Z",
    "updated_at": "2025-10-15T10:00:00Z",
    "workout_exercises": [...]
  },
  "message": "Workout created successfully"
}
```

**Status Codes:**
- `201`: Created successfully
- `401`: Unauthorized (no token)
- `403`: Forbidden (not a coach)
- `422`: Validation error
- `500`: Server error

---

### 2. Get All Workouts

**Endpoint:** `GET /workouts/workouts?is_template=false&category=Strength`

**Description:** Get all workouts created by the authenticated coach with optional filters.

**Authentication:** Required (Coach role)

**Query Parameters:**
- `is_template` (optional): Filter by template status (true/false)
- `category` (optional): Filter by category

**Response:**
```json
{
  "data": [
    {
      "id": "workout-uuid",
      "coach_id": "coach-uuid",
      "name": "Full Body Strength",
      "description": "...",
      "difficulty_level": "intermediate",
      "estimated_duration_minutes": 60,
      "category": "Strength Training",
      "is_template": false,
      "created_at": "2025-10-15T10:00:00Z",
      "updated_at": "2025-10-15T10:00:00Z",
      "exercise_count": 5
    }
  ],
  "message": "Workouts retrieved successfully"
}
```

---

### 3. Get Workout Details

**Endpoint:** `GET /workouts/workouts/{workout_id}`

**Description:** Get detailed workout information including all exercises.

**Authentication:** Required (Coach or assigned Client)

**Response:**
```json
{
  "data": {
    "id": "workout-uuid",
    "coach_id": "coach-uuid",
    "name": "Full Body Strength",
    "workout_exercises": [
      {
        "id": "we-uuid",
        "exercise_id": "ex-uuid",
        "order_index": 1,
        "sets": 3,
        "reps": 12,
        "duration_seconds": null,
        "rest_seconds": 60,
        "notes": "Focus on form",
        "exercise": {
          "id": "ex-uuid",
          "name": "Bench Press",
          "description": "...",
          "muscle_group": ["chest", "triceps"],
          "difficulty": "intermediate"
        }
      }
    ]
  },
  "message": "Workout retrieved successfully"
}
```

---

### 4. Update Workout (FR-4.1)

**Endpoint:** `PUT /workouts/workouts/{workout_id}`

**Description:** Update an existing workout routine.

**Authentication:** Required (Coach who created it)

**Request Body:**
```json
{
  "name": "Updated Workout Name",
  "difficulty_level": "advanced",
  "estimated_duration_minutes": 75
}
```

**Response:**
```json
{
  "data": {
    "id": "workout-uuid",
    "name": "Updated Workout Name",
    "difficulty_level": "advanced",
    "estimated_duration_minutes": 75,
    ...
  },
  "message": "Workout updated successfully"
}
```

---

### 5. Delete Workout (FR-4.1)

**Endpoint:** `DELETE /workouts/workouts/{workout_id}`

**Description:** Delete a workout routine. Cascades to delete exercises and assignments.

**Authentication:** Required (Coach who created it)

**Response:**
```json
{
  "data": {},
  "message": "Workout deleted successfully"
}
```

---

### 6. Add Exercise to Workout

**Endpoint:** `POST /workouts/workouts/{workout_id}/exercises`

**Description:** Add an exercise to an existing workout.

**Authentication:** Required (Coach who created workout)

**Request Body:**
```json
{
  "exercise_id": "exercise-uuid",
  "order_index": 3,
  "sets": 4,
  "reps": 10,
  "rest_seconds": 90,
  "notes": "Increase weight each set"
}
```

---

### 7. Update Workout Exercise

**Endpoint:** `PUT /workouts/workouts/{workout_id}/exercises/{exercise_id}`

**Description:** Update exercise configuration in a workout.

**Authentication:** Required (Coach who created workout)

---

### 8. Remove Exercise from Workout

**Endpoint:** `DELETE /workouts/workouts/{workout_id}/exercises/{exercise_id}`

**Description:** Remove an exercise from a workout.

**Authentication:** Required (Coach who created workout)

---

## Workout Assignment Endpoints

### 9. Assign Workout to Client (FR-4.2)

**Endpoint:** `POST /workouts/workouts/assignments`

**Description:** Assign a workout plan to a specific client. Requires active coach-client relationship.

**Authentication:** Required (Coach role)

**Request Body:**
```json
{
  "workout_id": "workout-uuid",
  "client_user_id": "client-uuid",
  "assigned_date": "2025-10-15",
  "due_date": "2025-10-22",
  "coach_notes": "Focus on form this week"
}
```

**Response:**
```json
{
  "data": {
    "id": "assignment-uuid",
    "workout_id": "workout-uuid",
    "coach_user_id": "coach-uuid",
    "client_user_id": "client-uuid",
    "assigned_date": "2025-10-15",
    "due_date": "2025-10-22",
    "status": "assigned",
    "coach_notes": "Focus on form this week",
    "workout": {
      ...full workout details...
    }
  },
  "message": "Workout assigned successfully"
}
```

**Status Codes:**
- `201`: Created successfully
- `403`: No active coach-client relationship
- `404`: Workout not found
- `422`: Invalid workout or client ID

---

### 10. Get My Assigned Workouts (FR-4.3)

**Endpoint:** `GET /workouts/workouts/assignments/my-workouts?status=assigned`

**Description:** Clients view their assigned workouts with full exercise details.

**Authentication:** Required (Client)

**Query Parameters:**
- `status` (optional): Filter by status (assigned, in_progress, completed, skipped)

**Response:**
```json
{
  "data": [
    {
      "id": "assignment-uuid",
      "workout_id": "workout-uuid",
      "assigned_date": "2025-10-15",
      "due_date": "2025-10-22",
      "status": "assigned",
      "coach_notes": "Focus on form this week",
      "client_notes": null,
      "workout": {
        "id": "workout-uuid",
        "name": "Full Body Strength",
        "workout_exercises": [
          {
            "exercise": {
              "name": "Bench Press",
              "instructions": "...",
              "demo_video_url": "..."
            },
            "sets": 3,
            "reps": 12
          }
        ]
      }
    }
  ],
  "message": "Assigned workouts retrieved successfully"
}
```

---

### 11. Get Client's Assigned Workouts

**Endpoint:** `GET /workouts/workouts/assignments/client/{client_id}?status=completed`

**Description:** Coaches view workouts assigned to a specific client.

**Authentication:** Required (Coach with relationship to client)

---

### 12. Update Assigned Workout

**Endpoint:** `PUT /workouts/workouts/assignments/{assignment_id}`

**Description:** Update assignment details. Coaches can update all fields; clients can only update notes and status.

**Authentication:** Required (Coach or Client)

**Request Body (Coach):**
```json
{
  "due_date": "2025-10-25",
  "status": "completed",
  "coach_notes": "Great progress!"
}
```

**Request Body (Client):**
```json
{
  "status": "completed",
  "client_notes": "Completed all sets successfully"
}
```

---

### 13. Delete Assigned Workout

**Endpoint:** `DELETE /workouts/workouts/assignments/{assignment_id}`

**Description:** Unassign a workout from a client.

**Authentication:** Required (Coach who assigned it)

---

## Media Upload Endpoints

### Base URL: `/feedback`

### 14. Upload Media

**Endpoint:** `POST /feedback/media`

**Description:** Clients upload video/image for exercise tracking.

**Authentication:** Required (Client)

**Request Body:**
```json
{
  "assigned_workout_id": "assignment-uuid",
  "exercise_id": "exercise-uuid",
  "media_url": "https://storage.example.com/video.mp4",
  "media_type": "video"
}
```

**Response:**
```json
{
  "data": {
    "id": "media-uuid",
    "client_user_id": "client-uuid",
    "assigned_workout_id": "assignment-uuid",
    "exercise_id": "exercise-uuid",
    "media_url": "https://storage.example.com/video.mp4",
    "media_type": "video",
    "status": "ready",
    "created_at": "2025-10-15T14:30:00Z"
  },
  "message": "Media uploaded successfully"
}
```

---

### 15. Get My Media Uploads

**Endpoint:** `GET /feedback/media/my-uploads?assigned_workout_id=uuid&exercise_id=uuid`

**Description:** Get all media uploads for the authenticated client.

**Authentication:** Required (Client)

---

### 16. Get Client Media Uploads

**Endpoint:** `GET /feedback/media/client/{client_id}?exercise_id=uuid`

**Description:** Coaches view media uploads from their clients.

**Authentication:** Required (Coach with relationship to client)

---

### 17. Get Media Details

**Endpoint:** `GET /feedback/media/{media_id}`

**Description:** Get detailed information about a specific media upload.

**Authentication:** Required (Client who uploaded or Coach with relationship)

---

### 18. Delete Media

**Endpoint:** `DELETE /feedback/media/{media_id}`

**Description:** Delete a media upload.

**Authentication:** Required (Client who uploaded it)

---

## Feedback & Communication Endpoints

### 19. Create Feedback (FR-5.1)

**Endpoint:** `POST /feedback/media/{media_id}/feedback`

**Description:** Coaches comment on client-uploaded media with optional annotations.

**Authentication:** Required (Coach with relationship to client)

**Request Body:**
```json
{
  "content": "Great form! Try to lower the bar a bit slower on the descent.",
  "annotation_data": {
    "timestamp": 15.5,
    "position": {"x": 120, "y": 300}
  },
  "parent_feedback_id": null
}
```

**Response:**
```json
{
  "data": {
    "id": "feedback-uuid",
    "media_id": "media-uuid",
    "coach_user_id": "coach-uuid",
    "coach_name": "John Smith",
    "content": "Great form! Try to lower the bar a bit slower on the descent.",
    "annotation_data": {
      "timestamp": 15.5,
      "position": {"x": 120, "y": 300}
    },
    "parent_feedback_id": null,
    "replies": [],
    "created_at": "2025-10-15T15:00:00Z",
    "updated_at": "2025-10-15T15:00:00Z"
  },
  "message": "Feedback created successfully"
}
```

**Use Cases:**
- Simple text comments
- Timestamped video annotations
- Image coordinate annotations
- Threaded replies (using `parent_feedback_id`)

---

### 20. Get Media Feedback (FR-5.2)

**Endpoint:** `GET /feedback/media/{media_id}/feedback`

**Description:** Get all feedback for a media upload in hierarchical structure.

**Authentication:** Required (Client who uploaded or Coach with relationship)

**Response:**
```json
{
  "data": [
    {
      "id": "feedback-1-uuid",
      "coach_name": "John Smith",
      "content": "Great form overall!",
      "annotation_data": null,
      "created_at": "2025-10-15T15:00:00Z",
      "replies": [
        {
          "id": "feedback-2-uuid",
          "coach_name": "John Smith",
          "content": "Follow-up: Try increasing weight next session",
          "parent_feedback_id": "feedback-1-uuid",
          "replies": []
        }
      ]
    }
  ],
  "message": "Feedback retrieved successfully"
}
```

---

### 21. Get Media with Feedback (FR-5.2)

**Endpoint:** `GET /feedback/media/{media_id}/with-feedback`

**Description:** Get media upload with all associated feedback in one response.

**Authentication:** Required (Client who uploaded or Coach with relationship)

**Response:**
```json
{
  "data": {
    "id": "media-uuid",
    "client_user_id": "client-uuid",
    "media_url": "https://storage.example.com/video.mp4",
    "media_type": "video",
    "created_at": "2025-10-15T14:30:00Z",
    "feedback": [
      {
        "id": "feedback-uuid",
        "coach_name": "John Smith",
        "content": "Great form!",
        "annotation_data": {"timestamp": 15.5},
        "replies": []
      }
    ]
  },
  "message": "Media with feedback retrieved successfully"
}
```

---

### 22. Update Feedback

**Endpoint:** `PUT /feedback/feedback/{feedback_id}`

**Description:** Update existing feedback.

**Authentication:** Required (Coach who created it)

**Request Body:**
```json
{
  "content": "Updated feedback content",
  "annotation_data": {"timestamp": 16.0}
}
```

---

### 23. Delete Feedback

**Endpoint:** `DELETE /feedback/feedback/{feedback_id}`

**Description:** Delete feedback and all nested replies.

**Authentication:** Required (Coach who created it)

---

## Authentication & Authorization

### Authentication
All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Authorization Roles

**Coach Role:**
- Can create, edit, delete workouts
- Can assign workouts to clients
- Can view media from their clients
- Can provide feedback on client media

**Client Role:**
- Can view assigned workouts
- Can upload media for exercises
- Can view feedback on their media
- Can update assignment status and notes

**Coach-Client Relationship:**
- Must be in `ACTIVE` status
- Required for workout assignments
- Required for coaches to view client media
- Required for coaches to provide feedback

---

## Data Models

### Workout
- `id`: UUID
- `coach_id`: UUID
- `name`: String (required)
- `description`: String (optional)
- `difficulty_level`: "beginner" | "intermediate" | "advanced"
- `estimated_duration_minutes`: Integer (1-600)
- `category`: String
- `is_template`: Boolean
- `workout_exercises`: Array of WorkoutExercise

### WorkoutExercise
- `id`: UUID
- `workout_id`: UUID
- `exercise_id`: UUID
- `order_index`: Integer (required)
- `sets`: Integer (optional)
- `reps`: Integer (optional)
- `duration_seconds`: Integer (optional)
- `rest_seconds`: Integer (optional)
- `notes`: String (optional)

### AssignedWorkout
- `id`: UUID
- `workout_id`: UUID
- `coach_user_id`: UUID
- `client_user_id`: UUID
- `assigned_date`: Date
- `due_date`: Date (optional)
- `status`: "assigned" | "in_progress" | "completed" | "skipped"
- `coach_notes`: String (optional)
- `client_notes`: String (optional)

### MediaUpload
- `id`: UUID
- `client_user_id`: UUID
- `assigned_workout_id`: UUID (optional)
- `exercise_id`: UUID
- `media_url`: String (required)
- `media_type`: "video" | "image"
- `status`: String

### Feedback
- `id`: UUID
- `media_id`: UUID
- `coach_user_id`: UUID
- `parent_feedback_id`: UUID (optional, for threaded replies)
- `content`: String (required, max 5000 chars)
- `annotation_data`: JSON (optional, for timestamps/coordinates)

---

## Error Responses

All endpoints return errors in the following format:

```json
{
  "detail": "Error message description"
}
```

### Common Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized (no token or invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `422`: Unprocessable Entity (validation error)
- `500`: Internal Server Error

---

## Best Practices

### For React Native Integration

1. **Token Management:**
   - Store JWT token securely using `@react-native-async-storage`
   - Implement token refresh logic
   - Add token to all requests automatically

2. **Error Handling:**
   - Implement global error interceptor
   - Handle 401 errors by redirecting to login
   - Show user-friendly error messages

3. **Media Upload:**
   - Use `react-native-image-picker` for media selection
   - Upload to cloud storage (S3, Cloudinary) first
   - Send media URL to backend, not raw file

4. **Real-time Updates:**
   - Consider implementing WebSocket for live feedback notifications
   - Poll for new feedback periodically
   - Use optimistic UI updates for better UX

5. **Caching:**
   - Cache workout and exercise data locally
   - Implement pull-to-refresh
   - Use React Query or SWR for data fetching

### Example React Native Usage

```javascript
// Fetch assigned workouts
const fetchAssignedWorkouts = async () => {
  try {
    const token = await AsyncStorage.getItem('authToken');
    const response = await fetch(
      'https://api.example.com/workouts/workouts/assignments/my-workouts',
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    const data = await response.json();
    return data.data;
  } catch (error) {
    console.error('Error fetching workouts:', error);
  }
};

// Upload media
const uploadExerciseVideo = async (videoUri, exerciseId, assignmentId) => {
  // 1. Upload to cloud storage
  const mediaUrl = await uploadToCloudStorage(videoUri);
  
  // 2. Send URL to backend
  const token = await AsyncStorage.getItem('authToken');
  const response = await fetch('https://api.example.com/feedback/media', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      assigned_workout_id: assignmentId,
      exercise_id: exerciseId,
      media_url: mediaUrl,
      media_type: 'video'
    })
  });
  return response.json();
};
```

---

## Implementation Summary

### Functional Requirements Implemented

✅ **FR-4.1**: Coaches can create, edit, and delete workout routines
- `POST /workouts/workouts` - Create
- `PUT /workouts/workouts/{id}` - Edit
- `DELETE /workouts/workouts/{id}` - Delete

✅ **FR-4.2**: Coaches can assign workout plans to specific clients
- `POST /workouts/workouts/assignments` - Assign
- `GET /workouts/workouts/assignments/client/{id}` - View assignments

✅ **FR-4.3**: Clients can view assigned workouts with exercise details
- `GET /workouts/workouts/assignments/my-workouts` - List
- `GET /workouts/workouts/{id}` - Details

✅ **FR-5.1**: Coaches can comment on client-uploaded media
- `POST /feedback/media/{id}/feedback` - Create feedback
- Supports annotations via `annotation_data` field

✅ **FR-5.2**: System displays feedback alongside corresponding media
- `GET /feedback/media/{id}/feedback` - Get feedback
- `GET /feedback/media/{id}/with-feedback` - Get media with feedback

### Additional Features
- Hierarchical feedback with threaded replies
- Role-based authorization
- Coach-client relationship verification
- Workout templates
- Exercise ordering and configuration
- Media upload tracking
- Comprehensive error handling
- FastAPI automatic OpenAPI documentation

---

## Testing the API

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Use these interfaces to test endpoints directly from your browser!
