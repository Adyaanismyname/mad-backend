# API Documentation

This document provides comprehensive details about all API endpoints available in the Gym App backend server.

## Base URL
```
http://localhost:8000
```

## Table of Contents
1. [Authentication](#authentication)
2. [Standard Response Format](#standard-response-format)
3. [Health Check](#health-check)
4. [User Endpoints](#user-endpoints)
5. [Admin User Endpoints](#admin-user-endpoints)
6. [Workout Endpoints](#workout-endpoints)
7. [Workout Assignment Endpoints](#workout-assignment-endpoints)
8. [Workout Exercise Management](#workout-exercise-management)
9. [Media Upload Endpoints](#media-upload-endpoints)
10. [Media Query Endpoints](#media-query-endpoints)
11. [Media Management Endpoints](#media-management-endpoints)
12. [Feedback Endpoints](#feedback-endpoints)

---

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### Roles
- **CLIENT**: Can upload media, view assigned workouts, add notes
- **COACH**: Can create workouts, assign workouts, provide feedback
- **BOTH**: Has both client and coach privileges
- **ADMIN**: Has administrative privileges

---

## Standard Response Format

All API responses follow this structure:
```json
{
    "data": { /* payload object, array, or empty {} */ },
    "message": "A short message"
}
```

---

## Health Check

### Check API Status
**GET** `/health`

Check if the API is running.

**Authentication:** None required

**Response:**
```json
{
    "status": "ok"
}
```

**Status Code:** `200 OK`

---

## User Endpoints

### 1. User Login
**POST** `/users/login`

Authenticate a user and receive a JWT token.

**Authentication:** None required

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

**Response:**
```json
{
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    },
    "message": "Login successful"
}
```

**Status Codes:**
- `200 OK`: Login successful
- `401 Unauthorized`: Invalid email or password
- `500 Internal Server Error`: Server error

---

### 2. User Signup
**POST** `/users/signup`

Register a new user account and send verification OTP to email.

**Authentication:** None required

**Request Body:**
```json
{
    "email": "newuser@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
}
```

**Response:**
```json
{
    "data": {},
    "message": "Verification OTP sent to email"
}
```

**Status Codes:**
- `200 OK`: OTP sent successfully
- `400 Bad Request`: Email already registered
- `500 Internal Server Error`: Server error

**Notes:**
- OTP expires in 10 minutes
- Email is sent in background

---

### 3. Verify OTP
**POST** `/users/verify-otp`

Verify the OTP sent to user's email and receive JWT token.

**Authentication:** None required

**Request Body:**
```json
{
    "email": "newuser@example.com",
    "token": "123456"
}
```

**Response:**
```json
{
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    },
    "message": "Verification successful"
}
```

**Status Codes:**
- `200 OK`: Verification successful
- `400 Bad Request`: Invalid or used token, or token expired
- `500 Internal Server Error`: Server error

---

## Admin User Endpoints

### 1. Get All Users
**GET** `/admin/users/getAllUsers`

Retrieve all users from the database (Admin only).

**Authentication:** Required (Admin)

**Response:**
```json
{
    "data": [
        {
            "id": 1,
            "username": "johndoe",
            "email": "john@example.com"
        },
        {
            "id": 2,
            "username": "janedoe",
            "email": "jane@example.com"
        }
    ],
    "message": "Users retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Users retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin
- `503 Service Unavailable`: Database connection failed
- `500 Internal Server Error`: Server error

---

### 2. Get User by ID
**GET** `/admin/users/getUser/{user_id}`

Get specific user metadata by ID (Admin only).

**Authentication:** Required (Admin)

**Path Parameters:**
- `user_id` (integer): The ID of the user to retrieve

**Response:**
```json
{
    "data": {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com"
    },
    "message": "User retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: User retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not an admin
- `404 Not Found`: User not found
- `503 Service Unavailable`: Database connection failed
- `500 Internal Server Error`: Server error

---

## Workout Endpoints

### 1. Create Workout
**POST** `/workouts/workouts`

Create a new workout routine (Coach only).

**Authentication:** Required (Coach)

**Request Body:**
```json
{
    "name": "Full Body Workout",
    "description": "A comprehensive full body routine",
    "difficulty_level": "intermediate",
    "estimated_duration_minutes": 60,
    "category": "strength",
    "is_template": true,
    "exercises": [
        {
            "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
            "order_index": 0,
            "sets": 3,
            "reps": 10,
            "duration_seconds": null,
            "rest_seconds": 60,
            "notes": "Keep your back straight"
        }
    ]
}
```

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "coach_id": "123e4567-e89b-12d3-a456-426614174002",
        "name": "Full Body Workout",
        "description": "A comprehensive full body routine",
        "difficulty_level": "intermediate",
        "estimated_duration_minutes": 60,
        "category": "strength",
        "is_template": true,
        "created_at": "2025-11-12T10:00:00",
        "updated_at": "2025-11-12T10:00:00",
        "workout_exercises": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "workout_id": "123e4567-e89b-12d3-a456-426614174001",
                "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
                "order_index": 0,
                "sets": 3,
                "reps": 10,
                "duration_seconds": null,
                "rest_seconds": 60,
                "notes": "Keep your back straight",
                "created_at": "2025-11-12T10:00:00",
                "exercise": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Bench Press",
                    "description": "Chest exercise",
                    "category": "strength",
                    "muscle_group": ["chest", "triceps"],
                    "instructions": "Lie on bench...",
                    "demo_video_url": "https://example.com/video.mp4",
                    "difficulty": "intermediate",
                    "equipment_needed": ["barbell", "bench"],
                    "created_at": "2025-11-12T09:00:00",
                    "updated_at": "2025-11-12T09:00:00"
                }
            }
        ]
    },
    "message": "Workout created successfully"
}
```

**Status Codes:**
- `201 Created`: Workout created successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not a coach
- `422 Unprocessable Entity`: Invalid exercise ID or constraint violation
- `500 Internal Server Error`: Server error

**Notes:**
- `difficulty_level` must be one of: "beginner", "intermediate", "advanced"
- `is_template`: true for reusable templates, false for client-specific workouts
- `exercises` array is optional

---

### 2. Get All Workouts
**GET** `/workouts/workouts`

Get all workouts created by the authenticated coach.

**Authentication:** Required (Coach)

**Query Parameters:**
- `is_template` (boolean, optional): Filter by template status
- `category` (string, optional): Filter by category

**Example:** `/workouts/workouts?is_template=true&category=strength`

**Response:**
```json
{
    "data": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "coach_id": "123e4567-e89b-12d3-a456-426614174002",
            "name": "Full Body Workout",
            "description": "A comprehensive full body routine",
            "difficulty_level": "intermediate",
            "estimated_duration_minutes": 60,
            "category": "strength",
            "is_template": true,
            "created_at": "2025-11-12T10:00:00",
            "updated_at": "2025-11-12T10:00:00",
            "exercise_count": 5
        }
    ],
    "message": "Workouts retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Workouts retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not a coach
- `500 Internal Server Error`: Server error

---

### 3. Get Workout by ID
**GET** `/workouts/{workout_id}`

Get detailed information about a specific workout including exercises.

**Authentication:** Required (Coach or Client)

**Path Parameters:**
- `workout_id` (UUID): The ID of the workout

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "coach_id": "123e4567-e89b-12d3-a456-426614174002",
        "name": "Full Body Workout",
        "description": "A comprehensive full body routine",
        "difficulty_level": "intermediate",
        "estimated_duration_minutes": 60,
        "category": "strength",
        "is_template": true,
        "created_at": "2025-11-12T10:00:00",
        "updated_at": "2025-11-12T10:00:00",
        "workout_exercises": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "workout_id": "123e4567-e89b-12d3-a456-426614174001",
                "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
                "order_index": 0,
                "sets": 3,
                "reps": 10,
                "duration_seconds": null,
                "rest_seconds": 60,
                "notes": "Keep your back straight",
                "created_at": "2025-11-12T10:00:00",
                "exercise": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Bench Press",
                    "description": "Chest exercise",
                    "category": "strength",
                    "muscle_group": ["chest", "triceps"],
                    "instructions": "Lie on bench...",
                    "demo_video_url": "https://example.com/video.mp4",
                    "difficulty": "intermediate",
                    "equipment_needed": ["barbell", "bench"],
                    "created_at": "2025-11-12T09:00:00",
                    "updated_at": "2025-11-12T09:00:00"
                }
            }
        ]
    },
    "message": "Workout retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Workout retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view this workout
- `404 Not Found`: Workout not found
- `500 Internal Server Error`: Server error

**Notes:**
- Coaches can view their own workouts
- Clients can only view workouts assigned to them

---

### 4. Update Workout
**PUT** `/workouts/{workout_id}`

Update an existing workout routine (Coach only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `workout_id` (UUID): The ID of the workout

**Request Body:**
```json
{
    "name": "Updated Full Body Workout",
    "description": "Updated description",
    "difficulty_level": "advanced",
    "estimated_duration_minutes": 75,
    "category": "strength",
    "is_template": false
}
```

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "coach_id": "123e4567-e89b-12d3-a456-426614174002",
        "name": "Updated Full Body Workout",
        "description": "Updated description",
        "difficulty_level": "advanced",
        "estimated_duration_minutes": 75,
        "category": "strength",
        "is_template": false,
        "created_at": "2025-11-12T10:00:00",
        "updated_at": "2025-11-12T11:00:00",
        "workout_exercises": []
    },
    "message": "Workout updated successfully"
}
```

**Status Codes:**
- `200 OK`: Workout updated successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to update this workout
- `404 Not Found`: Workout not found
- `500 Internal Server Error`: Server error

**Notes:**
- Only the coach who created the workout can update it
- All fields are optional

---

### 5. Delete Workout
**DELETE** `/workouts/{workout_id}`

Delete a workout routine (Coach only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `workout_id` (UUID): The ID of the workout

**Response:**
```json
{
    "data": {},
    "message": "Workout deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Workout deleted successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to delete this workout
- `404 Not Found`: Workout not found
- `500 Internal Server Error`: Server error

**Notes:**
- Only the coach who created the workout can delete it
- Cascades to delete associated exercises and assignments

---

## Workout Assignment Endpoints

### 1. Assign Workout to Client
**POST** `/workouts/assignments`

Assign a workout plan to a specific client (Coach only).

**Authentication:** Required (Coach)

**Request Body:**
```json
{
    "workout_id": "123e4567-e89b-12d3-a456-426614174001",
    "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
    "assigned_date": "2025-11-12",
    "due_date": "2025-11-19",
    "coach_notes": "Focus on form, not weight"
}
```

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174020",
        "workout_id": "123e4567-e89b-12d3-a456-426614174001",
        "coach_client_relationship_id": "123e4567-e89b-12d3-a456-426614174030",
        "coach_user_id": "123e4567-e89b-12d3-a456-426614174002",
        "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
        "assigned_date": "2025-11-12",
        "due_date": "2025-11-19",
        "status": "assigned",
        "coach_notes": "Focus on form, not weight",
        "client_notes": null,
        "created_at": "2025-11-12T10:00:00",
        "updated_at": "2025-11-12T10:00:00",
        "workout": {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "coach_id": "123e4567-e89b-12d3-a456-426614174002",
            "name": "Full Body Workout",
            "description": "A comprehensive full body routine",
            "difficulty_level": "intermediate",
            "estimated_duration_minutes": 60,
            "category": "strength",
            "is_template": true,
            "created_at": "2025-11-12T10:00:00",
            "updated_at": "2025-11-12T10:00:00",
            "workout_exercises": []
        }
    },
    "message": "Workout assigned successfully"
}
```

**Status Codes:**
- `201 Created`: Workout assigned successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized or no active coach-client relationship
- `404 Not Found`: Workout not found
- `422 Unprocessable Entity`: Invalid workout or client ID
- `500 Internal Server Error`: Server error

**Notes:**
- Requires an active coach-client relationship
- `assigned_date` defaults to today if not provided
- Status is automatically set to "assigned"

---

### 2. Get My Assigned Workouts
**GET** `/workouts/assignments/my-workouts`

Get workouts assigned to the authenticated client.

**Authentication:** Required (Client)

**Query Parameters:**
- `status_filter` (string, optional): Filter by status ("assigned", "in_progress", "completed", "skipped")

**Example:** `/workouts/assignments/my-workouts?status_filter=assigned`

**Response:**
```json
{
    "data": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174020",
            "workout_id": "123e4567-e89b-12d3-a456-426614174001",
            "coach_client_relationship_id": "123e4567-e89b-12d3-a456-426614174030",
            "coach_user_id": "123e4567-e89b-12d3-a456-426614174002",
            "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
            "assigned_date": "2025-11-12",
            "due_date": "2025-11-19",
            "status": "assigned",
            "coach_notes": "Focus on form, not weight",
            "client_notes": null,
            "created_at": "2025-11-12T10:00:00",
            "updated_at": "2025-11-12T10:00:00",
            "workout": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Full Body Workout",
                "description": "A comprehensive full body routine",
                "difficulty_level": "intermediate",
                "estimated_duration_minutes": 60,
                "category": "strength",
                "is_template": true,
                "created_at": "2025-11-12T10:00:00",
                "updated_at": "2025-11-12T10:00:00",
                "workout_exercises": []
            }
        }
    ],
    "message": "Assigned workouts retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Workouts retrieved successfully
- `401 Unauthorized`: Not authenticated
- `500 Internal Server Error`: Server error

---

### 3. Get Client Assigned Workouts
**GET** `/workouts/assignments/client/{client_id}`

Get workouts assigned to a specific client (Coach only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `client_id` (UUID): The ID of the client

**Query Parameters:**
- `status_filter` (string, optional): Filter by status

**Response:**
```json
{
    "data": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174020",
            "workout_id": "123e4567-e89b-12d3-a456-426614174001",
            "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
            "coach_user_id": "123e4567-e89b-12d3-a456-426614174002",
            "assigned_date": "2025-11-12",
            "due_date": "2025-11-19",
            "status": "assigned",
            "workout_name": "Full Body Workout",
            "created_at": "2025-11-12T10:00:00"
        }
    ],
    "message": "Client workouts retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Workouts retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized or no coach-client relationship
- `500 Internal Server Error`: Server error

**Notes:**
- Only the coach who assigned the workouts can view them

---

### 4. Update Assigned Workout
**PUT** `/workouts/assignments/{assignment_id}`

Update an assigned workout (Coach or Client).

**Authentication:** Required (Coach or Client)

**Path Parameters:**
- `assignment_id` (UUID): The ID of the assignment

**Request Body (Coach):**
```json
{
    "due_date": "2025-11-25",
    "status": "in_progress",
    "coach_notes": "Great progress!",
    "client_notes": "Felt good today"
}
```

**Request Body (Client):**
```json
{
    "status": "completed",
    "client_notes": "Finished all sets!"
}
```

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174020",
        "workout_id": "123e4567-e89b-12d3-a456-426614174001",
        "coach_client_relationship_id": "123e4567-e89b-12d3-a456-426614174030",
        "coach_user_id": "123e4567-e89b-12d3-a456-426614174002",
        "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
        "assigned_date": "2025-11-12",
        "due_date": "2025-11-25",
        "status": "completed",
        "coach_notes": "Great progress!",
        "client_notes": "Finished all sets!",
        "created_at": "2025-11-12T10:00:00",
        "updated_at": "2025-11-12T15:00:00",
        "workout": {}
    },
    "message": "Assignment updated successfully"
}
```

**Status Codes:**
- `200 OK`: Assignment updated successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to update this assignment
- `404 Not Found`: Assignment not found
- `500 Internal Server Error`: Server error

**Notes:**
- Coaches can update all fields
- Clients can only update `client_notes` and `status`
- All fields are optional

---

### 5. Delete Assigned Workout
**DELETE** `/workouts/assignments/{assignment_id}`

Delete/unassign a workout (Coach only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `assignment_id` (UUID): The ID of the assignment

**Response:**
```json
{
    "data": {},
    "message": "Assignment deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Assignment deleted successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to delete this assignment
- `404 Not Found`: Assignment not found
- `500 Internal Server Error`: Server error

---

## Workout Exercise Management

### 1. Add Exercise to Workout
**POST** `/workouts/{workout_id}/exercises`

Add an exercise to an existing workout (Coach only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `workout_id` (UUID): The ID of the workout

**Request Body:**
```json
{
    "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
    "order_index": 0,
    "sets": 3,
    "reps": 12,
    "duration_seconds": null,
    "rest_seconds": 90,
    "notes": "Focus on slow, controlled movements"
}
```

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174003",
        "workout_id": "123e4567-e89b-12d3-a456-426614174001",
        "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
        "order_index": 0,
        "sets": 3,
        "reps": 12,
        "duration_seconds": null,
        "rest_seconds": 90,
        "notes": "Focus on slow, controlled movements",
        "created_at": "2025-11-12T10:00:00",
        "exercise": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Bench Press",
            "description": "Chest exercise",
            "category": "strength",
            "muscle_group": ["chest", "triceps"],
            "instructions": "Lie on bench...",
            "demo_video_url": "https://example.com/video.mp4",
            "difficulty": "intermediate",
            "equipment_needed": ["barbell", "bench"],
            "created_at": "2025-11-12T09:00:00",
            "updated_at": "2025-11-12T09:00:00"
        }
    },
    "message": "Exercise added to workout"
}
```

**Status Codes:**
- `201 Created`: Exercise added successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to modify this workout
- `404 Not Found`: Workout not found
- `422 Unprocessable Entity`: Invalid exercise ID
- `500 Internal Server Error`: Server error

---

### 2. Update Workout Exercise
**PUT** `/workouts/{workout_id}/exercises/{exercise_id}`

Update exercise configuration in a workout (Coach only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `workout_id` (UUID): The ID of the workout
- `exercise_id` (UUID): The ID of the workout exercise

**Request Body:**
```json
{
    "order_index": 1,
    "sets": 4,
    "reps": 8,
    "rest_seconds": 120,
    "notes": "Increase weight if possible"
}
```

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174003",
        "workout_id": "123e4567-e89b-12d3-a456-426614174001",
        "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
        "order_index": 1,
        "sets": 4,
        "reps": 8,
        "duration_seconds": null,
        "rest_seconds": 120,
        "notes": "Increase weight if possible",
        "created_at": "2025-11-12T10:00:00",
        "exercise": {}
    },
    "message": "Exercise updated"
}
```

**Status Codes:**
- `200 OK`: Exercise updated successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to modify this workout
- `404 Not Found`: Exercise not found in this workout
- `500 Internal Server Error`: Server error

**Notes:**
- All fields are optional

---

### 3. Remove Exercise from Workout
**DELETE** `/workouts/{workout_id}/exercises/{exercise_id}`

Remove an exercise from a workout (Coach only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `workout_id` (UUID): The ID of the workout
- `exercise_id` (UUID): The ID of the workout exercise

**Response:**
```json
{
    "data": {},
    "message": "Exercise removed from workout"
}
```

**Status Codes:**
- `200 OK`: Exercise removed successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to modify this workout
- `404 Not Found`: Exercise not found in this workout
- `500 Internal Server Error`: Server error

---

## Media Upload Endpoints

### 1. Upload Media
**POST** `/feedback/media`

Upload media (video/image) for an exercise (Client only).

**Authentication:** Required (Client)

**Request Body:**
```json
{
    "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
    "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
    "media_url": "https://s3.amazonaws.com/bucket/video.mp4",
    "media_type": "video"
}
```

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174040",
        "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
        "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
        "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
        "media_url": "https://s3.amazonaws.com/bucket/video.mp4",
        "media_type": "video",
        "status": "ready",
        "created_at": "2025-11-12T10:00:00"
    },
    "message": "Media uploaded successfully"
}
```

**Status Codes:**
- `201 Created`: Media uploaded successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Assigned workout not found or not authorized
- `422 Unprocessable Entity`: Invalid exercise or workout ID
- `500 Internal Server Error`: Server error

**Notes:**
- `media_type` must be "video" or "image"
- `assigned_workout_id` is optional
- Status is automatically set to "ready"

---

## Media Query Endpoints

### 1. Get My Media Uploads
**GET** `/feedback/media/my-uploads`

Get all media uploads for the authenticated client.

**Authentication:** Required (Client)

**Query Parameters:**
- `assigned_workout_id` (UUID, optional): Filter by assigned workout
- `exercise_id` (UUID, optional): Filter by exercise

**Example:** `/feedback/media/my-uploads?exercise_id=123e4567-e89b-12d3-a456-426614174000`

**Response:**
```json
{
    "data": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174040",
            "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
            "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
            "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
            "media_url": "https://s3.amazonaws.com/bucket/video.mp4",
            "media_type": "video",
            "status": "ready",
            "created_at": "2025-11-12T10:00:00"
        }
    ],
    "message": "Media uploads retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Media uploads retrieved successfully
- `401 Unauthorized`: Not authenticated
- `500 Internal Server Error`: Server error

---

### 2. Get Client Media Uploads
**GET** `/feedback/media/client/{client_id}`

Get media uploads from a specific client (Coach only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `client_id` (UUID): The ID of the client

**Query Parameters:**
- `assigned_workout_id` (UUID, optional): Filter by assigned workout
- `exercise_id` (UUID, optional): Filter by exercise

**Response:**
```json
{
    "data": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174040",
            "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
            "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
            "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
            "media_url": "https://s3.amazonaws.com/bucket/video.mp4",
            "media_type": "video",
            "status": "ready",
            "created_at": "2025-11-12T10:00:00"
        }
    ],
    "message": "Client media retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Media retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: No active coach-client relationship
- `500 Internal Server Error`: Server error

**Notes:**
- Only coaches with an active relationship with the client can view their media

---

## Media Management Endpoints

### 1. Get Media Details
**GET** `/feedback/media/{media_id}`

Get detailed information about a specific media upload.

**Authentication:** Required (Coach or Client)

**Path Parameters:**
- `media_id` (UUID): The ID of the media

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174040",
        "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
        "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
        "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
        "media_url": "https://s3.amazonaws.com/bucket/video.mp4",
        "media_type": "video",
        "status": "ready",
        "created_at": "2025-11-12T10:00:00"
    },
    "message": "Media retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Media retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view this media
- `404 Not Found`: Media not found
- `500 Internal Server Error`: Server error

**Notes:**
- Clients can view their own uploads
- Coaches can view uploads from their clients

---

### 2. Delete Media
**DELETE** `/feedback/media/{media_id}`

Delete a media upload (Client who uploaded it only).

**Authentication:** Required (Client)

**Path Parameters:**
- `media_id` (UUID): The ID of the media

**Response:**
```json
{
    "data": {},
    "message": "Media deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Media deleted successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to delete this media
- `404 Not Found`: Media not found
- `500 Internal Server Error`: Server error

---

## Feedback Endpoints

### 1. Create Feedback
**POST** `/feedback/media/{media_id}/feedback`

Create feedback/comment on client-uploaded media (Coach only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `media_id` (UUID): The ID of the media

**Request Body:**
```json
{
    "content": "Great form! Keep your elbows tucked in more.",
    "annotation_data": {
        "timestamp": 15.5,
        "coordinates": {"x": 100, "y": 200}
    },
    "parent_feedback_id": null
}
```

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174050",
        "media_id": "123e4567-e89b-12d3-a456-426614174040",
        "coach_user_id": "123e4567-e89b-12d3-a456-426614174002",
        "parent_feedback_id": null,
        "content": "Great form! Keep your elbows tucked in more.",
        "annotation_data": {
            "timestamp": 15.5,
            "coordinates": {"x": 100, "y": 200}
        },
        "created_at": "2025-11-12T10:00:00",
        "updated_at": "2025-11-12T10:00:00",
        "coach_name": "Coach John",
        "replies": []
    },
    "message": "Feedback created successfully"
}
```

**Status Codes:**
- `201 Created`: Feedback created successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not a coach or no coach-client relationship
- `404 Not Found`: Media or parent feedback not found
- `500 Internal Server Error`: Server error

**Notes:**
- `annotation_data` can contain timestamps, coordinates, or any JSON data
- `parent_feedback_id` enables threaded replies
- Requires active coach-client relationship

---

### 2. Get Media Feedback
**GET** `/feedback/media/{media_id}/feedback`

Get all feedback for a specific media upload.

**Authentication:** Required (Coach or Client)

**Path Parameters:**
- `media_id` (UUID): The ID of the media

**Response:**
```json
{
    "data": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174050",
            "media_id": "123e4567-e89b-12d3-a456-426614174040",
            "coach_user_id": "123e4567-e89b-12d3-a456-426614174002",
            "parent_feedback_id": null,
            "content": "Great form! Keep your elbows tucked in more.",
            "annotation_data": {
                "timestamp": 15.5,
                "coordinates": {"x": 100, "y": 200}
            },
            "created_at": "2025-11-12T10:00:00",
            "updated_at": "2025-11-12T10:00:00",
            "coach_name": "Coach John",
            "replies": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174051",
                    "media_id": "123e4567-e89b-12d3-a456-426614174040",
                    "coach_user_id": "123e4567-e89b-12d3-a456-426614174002",
                    "parent_feedback_id": "123e4567-e89b-12d3-a456-426614174050",
                    "content": "Also, slow down the eccentric phase.",
                    "annotation_data": null,
                    "created_at": "2025-11-12T10:05:00",
                    "updated_at": "2025-11-12T10:05:00",
                    "coach_name": "Coach John",
                    "replies": []
                }
            ]
        }
    ],
    "message": "Feedback retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Feedback retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view feedback on this media
- `404 Not Found`: Media not found
- `500 Internal Server Error`: Server error

**Notes:**
- Returns feedback in hierarchical structure with replies
- Clients can view feedback on their media
- Coaches can view feedback on their clients' media

---

### 3. Get Media with Feedback
**GET** `/feedback/media/{media_id}/with-feedback`

Get media upload with all associated feedback in one response.

**Authentication:** Required (Coach or Client)

**Path Parameters:**
- `media_id` (UUID): The ID of the media

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174040",
        "client_user_id": "123e4567-e89b-12d3-a456-426614174010",
        "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
        "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
        "media_url": "https://s3.amazonaws.com/bucket/video.mp4",
        "media_type": "video",
        "status": "ready",
        "created_at": "2025-11-12T10:00:00",
        "feedback": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174050",
                "media_id": "123e4567-e89b-12d3-a456-426614174040",
                "coach_user_id": "123e4567-e89b-12d3-a456-426614174002",
                "parent_feedback_id": null,
                "content": "Great form! Keep your elbows tucked in more.",
                "annotation_data": {
                    "timestamp": 15.5,
                    "coordinates": {"x": 100, "y": 200}
                },
                "created_at": "2025-11-12T10:00:00",
                "updated_at": "2025-11-12T10:00:00",
                "coach_name": "Coach John",
                "replies": []
            }
        ]
    },
    "message": "Media with feedback retrieved successfully"
}
```

**Status Codes:**
- `200 OK`: Media with feedback retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view this media
- `404 Not Found`: Media not found
- `500 Internal Server Error`: Server error

---

### 4. Update Feedback
**PUT** `/feedback/{feedback_id}`

Update existing feedback (Coach who created it only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `feedback_id` (UUID): The ID of the feedback

**Request Body:**
```json
{
    "content": "Updated: Great form! Keep your elbows tucked in more and slow down.",
    "annotation_data": {
        "timestamp": 15.5,
        "coordinates": {"x": 120, "y": 210}
    }
}
```

**Response:**
```json
{
    "data": {
        "id": "123e4567-e89b-12d3-a456-426614174050",
        "media_id": "123e4567-e89b-12d3-a456-426614174040",
        "coach_user_id": "123e4567-e89b-12d3-a456-426614174002",
        "parent_feedback_id": null,
        "content": "Updated: Great form! Keep your elbows tucked in more and slow down.",
        "annotation_data": {
            "timestamp": 15.5,
            "coordinates": {"x": 120, "y": 210}
        },
        "created_at": "2025-11-12T10:00:00",
        "updated_at": "2025-11-12T10:30:00",
        "coach_name": "Coach John",
        "replies": []
    },
    "message": "Feedback updated successfully"
}
```

**Status Codes:**
- `200 OK`: Feedback updated successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to update this feedback
- `404 Not Found`: Feedback not found
- `500 Internal Server Error`: Server error

**Notes:**
- Only the coach who created the feedback can update it
- All fields are optional

---

### 5. Delete Feedback
**DELETE** `/feedback/{feedback_id}`

Delete feedback (Coach who created it only).

**Authentication:** Required (Coach)

**Path Parameters:**
- `feedback_id` (UUID): The ID of the feedback

**Response:**
```json
{
    "data": {},
    "message": "Feedback deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Feedback deleted successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to delete this feedback
- `404 Not Found`: Feedback not found
- `500 Internal Server Error`: Server error

**Notes:**
- Only the coach who created the feedback can delete it
- Also deletes any nested replies

---

## Error Handling

All error responses follow this format:
```json
{
    "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: User doesn't have permission
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error or constraint violation
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Database or service unavailable

---

## Data Types Reference

### UUID Format
All IDs use UUID format:
```
123e4567-e89b-12d3-a456-426614174000
```

### Date Format
Dates use ISO 8601 format:
```
2025-11-12
```

### DateTime Format
DateTimes use ISO 8601 format with timezone:
```
2025-11-12T10:00:00
```

### Assignment Status Enum
- `assigned`: Workout has been assigned
- `in_progress`: Client is working on it
- `completed`: Client finished the workout
- `skipped`: Client skipped the workout

### Difficulty Level Enum
- `beginner`
- `intermediate`
- `advanced`

### Media Type Enum
- `video`
- `image`

---

## Rate Limiting

Currently, there are no rate limits implemented. This may change in future versions.

---

## Versioning

Current API version: **v1.0.0**

The API does not currently use versioning in URLs. Future versions may introduce versioning like `/api/v2/`.

---

## Support

For issues or questions, please contact the development team or create an issue in the repository.
