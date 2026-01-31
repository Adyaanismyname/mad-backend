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
6. [Coach-Client Relationship Endpoints](#coach-client-relationship-endpoints)
7. [Workout Endpoints](#workout-endpoints)
8. [Exercise Library Endpoints](#exercise-library-endpoints)
9. [Workout Assignment Endpoints](#workout-assignment-endpoints)
10. [Workout Exercise Management](#workout-exercise-management)
11. [Media Upload Endpoints](#media-upload-endpoints)
12. [Media Query Endpoints](#media-query-endpoints)
13. [Media Management Endpoints](#media-management-endpoints)
14. [Feedback Endpoints](#feedback-endpoints)

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

### JWT Token Structure

JWT tokens contain comprehensive user information for efficient authorization and reduced database queries:

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "client",
  "is_activated": true,
  "exp": 1732140000
}
```

**Token Fields:**

- `user_id`: User's unique identifier
- `email`: User's email address
- `full_name`: User's display name
- `role`: User's role ("client", "coach", or "both")
- `is_activated`: Account activation status
- `exp`: Token expiration timestamp

---

## Standard Response Format

All API responses follow this structure:

```json
{
  "data": {
    /* payload object, array, or empty {} */
  },
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

Authenticate a user and receive a JWT token. If the account is not activated, an OTP will be automatically sent for activation.

**Authentication:** None required

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (Activated Account):**

```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "Login successful"
}
```

**Response (Unactivated Account):**

```json
{
  "data": {
    "requires_activation": true
  },
  "message": "Account not activated. Verification OTP sent to email"
}
```

**Status Codes:**

- `200 OK`: Login successful (activated) or OTP sent (unactivated)
- `401 Unauthorized`: Invalid email or password
- `500 Internal Server Error`: Server error

**Notes:**

- New accounts start as unactivated and require OTP verification
- If account is not activated, OTP is automatically sent to the registered email
- OTP expires in 10 minutes
- After successful OTP verification, account is activated

---

### 2. User Signup

**POST** `/users/signup`

Register a new user account and send verification OTP to email. Account will be created but not activated until OTP is verified.

**Authentication:** None required

**Request Body:**

```json
{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "role": "client"
}
```

**Fields:**

- `email`: User's email address (required)
- `password`: User's password (required)
- `full_name`: User's full name (optional)
- `role`: User's role - "client", "coach", or "both" (optional, defaults to "client")

**Response:**

```json
{
  "data": {},
  "message": "Verification OTP sent to email"
}
```

**Status Codes:**

- `200 OK`: Account created and OTP sent successfully
- `400 Bad Request`: Email already registered
- `500 Internal Server Error`: Server error

**Notes:**

- User account is created with `is_activated = false`
- OTP is stored directly on the user record
- OTP expires in 10 minutes
- Email is sent in background
- User must verify OTP to activate account and login

---

### 3. Verify OTP

**POST** `/users/verify-otp`

Verify the OTP sent to user's email, activate the account, and receive JWT token.

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
  "message": "Account activated successfully"
}
```

**Status Codes:**

- `200 OK`: Account activated and JWT token returned
- `400 Bad Request`: User not found, invalid OTP, expired OTP, or missing OTP
- `500 Internal Server Error`: Server error

**Error Messages:**

- `"User not found"`: Email doesn't exist in the system
- `"No OTP found for this user"`: No OTP has been generated for this user
- `"Invalid OTP"`: The provided OTP doesn't match
- `"OTP timestamp not found"`: OTP creation timestamp is missing
- `"OTP has expired"`: OTP is older than 10 minutes

**Notes:**

- OTP expires after 10 minutes from generation
- After successful verification:
  - User account is activated (`is_activated = true`)
  - OTP and timestamp are cleared from user record
  - JWT token is returned for immediate login
- Each OTP can only be used once
- Use this endpoint after signup or when login returns `requires_activation: true`

---

### 4. Get Current User Data

**GET** `/users/me`

Get the authenticated user's profile data by decoding their JWT token.

**Authentication:** Required (JWT token in Authorization header)

**Request:** No body required

**Response:**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "message": "User data retrieved successfully"
}
```

**Status Codes:**

- `200 OK`: User data retrieved successfully
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: User not found in database
- `500 Internal Server Error`: Server error

**Notes:**

- Automatically extracts user ID from JWT token
- Returns basic user profile information
- Useful for frontend to display current user info
- No need to pass user_id as parameter

---

### User Authentication Flow

**New User Registration:**

1. User calls `POST /users/signup` with email, password, and full_name
2. Account is created with `is_activated = false`
3. 6-digit OTP is generated and sent to user's email
4. User receives OTP via email (valid for 10 minutes)
5. User calls `POST /users/verify-otp` with email and OTP
6. Account is activated and JWT token is returned
7. User can now login normally

**Existing User Login (Activated):**

1. User calls `POST /users/login` with email and password
2. If account is activated, JWT token is returned
3. User can access protected endpoints

**Existing User Login (Not Activated):**

1. User calls `POST /users/login` with email and password
2. System detects account is not activated
3. New OTP is automatically generated and sent to email
4. Response includes `requires_activation: true` flag
5. User calls `POST /users/verify-otp` with email and new OTP
6. Account is activated and JWT token is returned

---

## Admin User Endpoints

### 1. Get All Users

**GET** `/users/getAllUsers`

Retrieve all users from the database (Admin only).

**Authentication:** Required (Admin)

**Response:**

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "john@example.com",
      "full_name": "John Doe",
      "role": "client",
      "is_activated": true,
      "created_at": "2025-11-12T10:00:00",
      "updated_at": "2025-11-12T10:00:00"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "email": "jane@example.com",
      "full_name": "Jane Doe",
      "role": "coach",
      "is_activated": true,
      "created_at": "2025-11-12T09:00:00",
      "updated_at": "2025-11-12T09:00:00"
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

**Notes:**

- Returns all users with their activation status
- User IDs are UUIDs, not integers

---

### 2. Get User by ID

**GET** `/users/getUser/{user_id}`

Get specific user metadata by ID (Admin only).

**Authentication:** Required (Admin)

**Path Parameters:**

- `user_id` (UUID): The ID of the user to retrieve

**Response:**

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "client",
    "is_activated": true,
    "phone_number": "+1234567890",
    "profile_picture_url": "https://example.com/profile.jpg",
    "created_at": "2025-11-12T10:00:00",
    "updated_at": "2025-11-12T10:00:00"
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

**Notes:**

- `user_id` must be a valid UUID
- Returns complete user profile including activation status

---

## Coach-Client Relationship Endpoints

These endpoints manage the connections between coaches and clients. A relationship must be ACTIVE before a coach can assign workouts to a client.

### Relationship Status Flow

```
PENDING → ACTIVE (accepted)
PENDING → TERMINATED (rejected)
ACTIVE → PAUSED
ACTIVE → TERMINATED
PAUSED → ACTIVE (reactivated)
PAUSED → TERMINATED
```

---

### 1. Create Relationship

**POST** `/relationships`

Create a coach-client relationship. Can be initiated by either party.

**Authentication:** Required

**Scenarios:**

1. **Coach invites client**: Provide `client_user_id`
2. **Client requests coach**: Provide `coach_user_id`

**Request Body (Coach inviting client):**

```json
{
  "client_user_id": "123e4567-e89b-12d3-a456-426614174001"
}
```

**Request Body (Client requesting coach):**

```json
{
  "coach_user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Response:**

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "coach_user_id": "123e4567-e89b-12d3-a456-426614174000",
    "client_user_id": "123e4567-e89b-12d3-a456-426614174001",
    "status": "pending",
    "created_at": "2025-11-20T10:00:00",
    "updated_at": "2025-11-20T10:00:00"
  },
  "message": "Relationship request created successfully"
}
```

**Status Codes:**

- `201 Created`: Relationship created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: User doesn't have required role (e.g., not a coach)
- `404 Not Found`: Specified user not found
- `409 Conflict`: Relationship already exists
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Notes:**

- Only one of `coach_user_id` or `client_user_id` should be provided
- Relationship starts with `pending` status
- The recipient must accept to make it `active`

---

### 2. Get My Relationships

**GET** `/relationships`

Get all relationships for the current user (as coach or client).

**Authentication:** Required

**Query Parameters:**

- `status_filter` (optional): Filter by status (`pending`, `active`, `paused`, `terminated`)

**Example Request:**

```
GET /relationships?status_filter=active
```

**Response:**

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "coach_user_id": "123e4567-e89b-12d3-a456-426614174000",
      "coach_email": "coach@example.com",
      "coach_name": "John Coach",
      "client_user_id": "123e4567-e89b-12d3-a456-426614174001",
      "client_email": "client@example.com",
      "client_name": "Jane Client",
      "status": "active",
      "created_at": "2025-11-20T10:00:00",
      "updated_at": "2025-11-20T10:15:00"
    }
  ],
  "message": "Relationships retrieved successfully"
}
```

**Status Codes:**

- `200 OK`: Relationships retrieved successfully
- `401 Unauthorized`: Not authenticated
- `422 Unprocessable Entity`: Invalid status filter
- `500 Internal Server Error`: Server error

**Notes:**

- Returns relationships where user is either coach or client
- Includes user details for both parties
- Without `status_filter`, returns all statuses

---

### 3. Get Relationship Details

**GET** `/relationships/{relationship_id}`

Get details of a specific relationship.

**Authentication:** Required

**Path Parameters:**

- `relationship_id` (UUID): The ID of the relationship

**Response:**

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "coach_user_id": "123e4567-e89b-12d3-a456-426614174000",
    "coach_email": "coach@example.com",
    "coach_name": "John Coach",
    "client_user_id": "123e4567-e89b-12d3-a456-426614174001",
    "client_email": "client@example.com",
    "client_name": "Jane Client",
    "status": "active",
    "created_at": "2025-11-20T10:00:00",
    "updated_at": "2025-11-20T10:15:00"
  },
  "message": "Relationship retrieved successfully"
}
```

**Status Codes:**

- `200 OK`: Relationship retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: User not part of this relationship
- `404 Not Found`: Relationship not found
- `500 Internal Server Error`: Server error

**Notes:**

- User must be either the coach or client in the relationship

---

### 4. Update Relationship Status

**PUT** `/relationships/{relationship_id}`

Update relationship status (Accept, Reject, Pause, Reactivate, Terminate).

**Authentication:** Required

**Path Parameters:**

- `relationship_id` (UUID): The ID of the relationship

**Request Body:**

```json
{
  "status": "active"
}
```

**Valid Status Values:**

- `active`: Accept a pending relationship or reactivate a paused one
- `paused`: Pause an active relationship
- `terminated`: Reject a pending relationship or terminate active/paused ones

**Response:**

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174002",
    "coach_user_id": "123e4567-e89b-12d3-a456-426614174000",
    "client_user_id": "123e4567-e89b-12d3-a456-426614174001",
    "status": "active",
    "created_at": "2025-11-20T10:00:00",
    "updated_at": "2025-11-20T10:15:00"
  },
  "message": "Relationship accepted"
}
```

**Status Codes:**

- `200 OK`: Relationship updated successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: User not authorized to update this relationship
- `404 Not Found`: Relationship not found
- `422 Unprocessable Entity`: Invalid status transition
- `500 Internal Server Error`: Server error

**Valid Status Transitions:**

- `pending` → `active` (accept) or `terminated` (reject)
- `active` → `paused` or `terminated`
- `paused` → `active` (reactivate) or `terminated`
- `terminated` → Cannot be changed

**Notes:**

- User must be part of the relationship
- Terminated relationships cannot be modified

---

### 5. Delete Relationship

**DELETE** `/relationships/{relationship_id}`

Permanently delete a relationship (hard delete).

**Authentication:** Required

**Path Parameters:**

- `relationship_id` (UUID): The ID of the relationship

**Response:**

```json
{
  "data": {},
  "message": "Relationship deleted successfully"
}
```

**Status Codes:**

- `200 OK`: Relationship deleted successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: User not authorized to delete this relationship
- `404 Not Found`: Relationship not found
- `422 Unprocessable Entity`: Cannot delete active/paused relationship
- `500 Internal Server Error`: Server error

**Notes:**

- Can only delete `pending` or `terminated` relationships
- For `active`/`paused` relationships, must terminate first
- Either party can delete
- This is a permanent action

---

### 6. Get Available Coaches

**GET** `/relationships/coaches/available`

Get list of coaches available to connect with (for clients).

**Authentication:** Required

**Response:**

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "coach1@example.com",
      "full_name": "John Coach",
      "role": "coach"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "email": "coach2@example.com",
      "full_name": "Jane Trainer",
      "role": "both"
    }
  ],
  "message": "Available coaches retrieved successfully"
}
```

**Status Codes:**

- `200 OK`: Coaches retrieved successfully
- `401 Unauthorized`: Not authenticated
- `500 Internal Server Error`: Server error

**Notes:**

- Returns coaches not already connected to current user
- Excludes coaches with existing relationships (any status)
- Useful for client UI to browse coaches

---

### 7. Get Available Clients

**GET** `/relationships/clients/available`

Get list of clients available to invite (for coaches).

**Authentication:** Required (Coach only)

**Response:**

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "email": "client1@example.com",
      "full_name": "Alice Client",
      "role": "client"
    },
    {
      "id": "123e4567-e89b-12d3-a456-426614174004",
      "email": "user@example.com",
      "full_name": "Bob User",
      "role": "both"
    }
  ],
  "message": "Available clients retrieved successfully"
}
```

**Status Codes:**

- `200 OK`: Clients retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: User is not a coach
- `500 Internal Server Error`: Server error

**Notes:**

- Only coaches can access this endpoint
- Returns users not already connected to current coach
- Excludes users with existing relationships (any status)
- Useful for coach UI to browse and invite clients

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

## Exercise Library Endpoints

### 1. Create Exercise

**POST** `/workouts/exercises`

Create a new exercise in the library (Coach only).

**Authentication:** Required (Coach)

**Request Body:**

```json
{
  "name": "Bulgarian Split Squat",
  "description": "A unilateral leg exercise.",
  "category": "strength",
  "muscle_group": ["quadriceps", "glutes"],
  "instructions": "Stand with back to bench...",
  "demo_video_url": "https://example.com/video.mp4",
  "difficulty": "intermediate",
  "equipment_needed": ["dumbbell", "bench"]
}
```

**Response:**

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Bulgarian Split Squat",
    "description": "A unilateral leg exercise.",
    "category": "strength",
    "muscle_group": ["quadriceps", "glutes"],
    "instructions": "Stand with back to bench...",
    "demo_video_url": "https://example.com/video.mp4",
    "difficulty": "intermediate",
    "equipment_needed": ["dumbbell", "bench"],
    "created_at": "2025-11-12T10:00:00",
    "updated_at": "2025-11-12T10:00:00"
  },
  "message": "Exercise created successfully"
}
```

**Status Codes:**

- `201 Created`: Exercise created successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not a coach
- `500 Internal Server Error`: Server error

---

### 2. List Exercises

**GET** `/workouts/exercises`

List all exercises in the library.

**Authentication:** Required

**Query Parameters:**

- `category` (string, optional): Filter by category
- `difficulty` (string, optional): Filter by difficulty

**Response:**

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Bulgarian Split Squat",
      "category": "strength",
      "difficulty": "intermediate"
    }
  ],
  "message": "Exercises retrieved successfully"
}
```

**Status Codes:**

- `200 OK`: Exercises retrieved successfully
- `401 Unauthorized`: Not authenticated
- `500 Internal Server Error`: Server error

---

### 3. Get Exercise Details

**GET** `/workouts/exercises/{exercise_id}`

Get details of a specific exercise.

**Authentication:** Required

**Path Parameters:**

- `exercise_id` (UUID): The ID of the exercise

**Response:**

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Bulgarian Split Squat",
    "description": "A unilateral leg exercise.",
    "category": "strength",
    "muscle_group": ["quadriceps", "glutes"],
    "instructions": "Stand with back to bench...",
    "demo_video_url": "https://example.com/video.mp4",
    "difficulty": "intermediate",
    "equipment_needed": ["dumbbell", "bench"],
    "created_at": "2025-11-12T10:00:00",
    "updated_at": "2025-11-12T10:00:00"
  },
  "message": "Exercise retrieved successfully"
}
```

**Status Codes:**

- `200 OK`: Exercise retrieved successfully
- `401 Unauthorized`: Not authenticated
- `404 Not Found`: Exercise not found
- `500 Internal Server Error`: Server error

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

> **🎯 RECOMMENDED APPROACH:** Use the **Two-Step Presigned URL Workflow** (Steps 1-3 below) for production. This provides secure, efficient uploads directly to S3 without proxying large files through your backend.

### Overview: How Media Upload Works

The backend implements a **two-step presigned URL workflow** for uploading workout videos and images to AWS S3:

1. **Initiate Upload** - Request a temporary presigned URL from backend
2. **Upload to S3** - Upload file directly to S3 using presigned URL (bypasses backend)
3. **Confirm Upload** - Notify backend that upload completed successfully

**Why this approach?**

- ✅ **Better Performance** - Files upload directly to S3, not through your server
- ✅ **Reduced Server Load** - Backend doesn't handle large file transfers
- ✅ **Scalability** - Can handle many concurrent uploads
- ✅ **Security** - Presigned URLs expire after 1 hour
- ✅ **Industry Standard** - Used by Dropbox, Instagram, YouTube, etc.

**File Constraints:**

- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` - Max 10 MB
- **Videos**: `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv` - Max 100 MB

---

### 1. Initiate Upload (Get Presigned URL)

**POST** `/feedback/media/initiate-upload`

Request a presigned S3 URL for uploading a media file. This validates your file and provides a temporary secure URL for direct S3 upload.

**Authentication:** Required (Client role)

**Request Body:**

```json
{
  "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
  "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
  "filename": "workout_video.mp4",
  "media_type": "video",
  "file_size_mb": 25.5
}
```

**Field Descriptions:**

| Field                 | Type   | Required    | Description                              |
| --------------------- | ------ | ----------- | ---------------------------------------- |
| `exercise_id`         | UUID   | ✅ Yes      | ID of the exercise this media belongs to |
| `assigned_workout_id` | UUID   | ❌ Optional | ID of assigned workout (if applicable)   |
| `filename`            | string | ✅ Yes      | Original filename (e.g., "my_squat.mp4") |
| `media_type`          | string | ✅ Yes      | Either `"video"` or `"image"`            |
| `file_size_mb`        | number | ✅ Yes      | File size in megabytes (e.g., 25.5)      |

**Response (200 OK):**

```json
{
  "data": {
    "upload_url": "https://bucket.s3.amazonaws.com/videos/user-id/exercise-id/20251203_143022_workout_video.mp4?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...",
    "media_url": "https://bucket.s3.us-east-1.amazonaws.com/videos/user-id/exercise-id/20251203_143022_workout_video.mp4",
    "s3_key": "videos/550e8400-e29b-41d4-a716-446655440000/123e4567-e89b-12d3-a456-426614174000/20251203_143022_workout_video.mp4",
    "content_type": "video/mp4",
    "expires_at": "2025-12-03T15:30:22Z",
    "upload_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  },
  "message": "Presigned upload URL generated successfully. Use the upload_url to PUT your file."
}
```

**Response Field Descriptions:**

| Field          | Description                                                   |
| -------------- | ------------------------------------------------------------- |
| `upload_url`   | **USE THIS** to upload your file via PUT request (see Step 2) |
| `media_url`    | Final URL where file will be accessible (save for later)      |
| `s3_key`       | S3 object key (internal identifier)                           |
| `content_type` | MIME type to use in upload headers                            |
| `expires_at`   | ISO timestamp when upload_url expires (1 hour from now)       |
| `upload_id`    | **SAVE THIS** - needed for confirmation in Step 3             |

**Status Codes:**

- `200 OK` - Presigned URL generated successfully
- `400 Bad Request` - Invalid file type, size, or missing fields
- `401 Unauthorized` - Not authenticated or invalid token
- `403 Forbidden` - `assigned_workout_id` doesn't belong to you
- `500 Internal Server Error` - Server or AWS S3 error

**Important Notes:**

- ⚠️ **URL expires in 1 hour** - If it expires, request a new one
- ⚠️ **Don't modify the upload_url** - Any changes will invalidate the signature
- ✅ **Save the `upload_id`** - You need it for Step 3 (confirm)
- ✅ **File validation happens here** - Invalid files rejected before upload

---

### 2. Upload File to S3

**PUT** `{upload_url}` (from Step 1)

Upload the actual file binary directly to AWS S3 using the presigned URL. **This request goes to S3, not to your backend.**

**Authentication:** None (presigned URL is self-authenticating)

**Request Headers:**

```
Content-Type: {content_type from Step 1}
```

**Request Body:** Raw file binary (no JSON, no form data)

**Frontend Implementation Examples:**

<details>
<summary><b>JavaScript / React / React Native</b></summary>

```javascript
// After Step 1, you have presignedData with upload_url and content_type
const uploadToS3 = async (file, presignedData) => {
  try {
    const response = await fetch(presignedData.upload_url, {
      method: "PUT",
      headers: {
        "Content-Type": presignedData.content_type,
      },
      body: file, // Raw File object
    });

    if (!response.ok) {
      throw new Error(`S3 upload failed: ${response.status}`);
    }

    console.log("Upload successful!");
    return true;
  } catch (error) {
    console.error("Upload error:", error);
    throw error;
  }
};

// Usage
const file = document.querySelector('input[type="file"]').files[0];
await uploadToS3(file, presignedData);
```

</details>

<details>
<summary><b>React Native with Expo</b></summary>

```javascript
import * as FileSystem from "expo-file-system";

const uploadToS3 = async (fileUri, presignedData) => {
  try {
    const response = await FileSystem.uploadAsync(
      presignedData.upload_url,
      fileUri,
      {
        httpMethod: "PUT",
        headers: {
          "Content-Type": presignedData.content_type,
        },
      }
    );

    if (response.status !== 200) {
      throw new Error(`S3 upload failed: ${response.status}`);
    }

    return true;
  } catch (error) {
    console.error("Upload error:", error);
    throw error;
  }
};
```

</details>

<details>
<summary><b>Axios</b></summary>

```javascript
import axios from "axios";

const uploadToS3 = async (file, presignedData) => {
  await axios.put(presignedData.upload_url, file, {
    headers: {
      "Content-Type": presignedData.content_type,
    },
  });
};
```

</details>

**Response:** S3 returns `200 OK` on success (no JSON body)

**Status Codes:**

- `200 OK` - Upload successful
- `403 Forbidden` - Invalid signature or expired URL
- `400 Bad Request` - Invalid request

**Important Notes:**

- ⚠️ **Use PUT, not POST** - S3 requires PUT method
- ⚠️ **Content-Type must match** - Use exact value from Step 1
- ⚠️ **Send raw file, not form data** - Direct binary upload
- ⚠️ **No Authorization header** - Presigned URL handles auth
- ✅ **Monitor upload progress** - Implement progress indicators for UX

---

### 3. Confirm Upload

**POST** `/feedback/media/confirm-upload`

After successfully uploading to S3 (Step 2), confirm the upload to create the database record. This verifies the file exists in S3 and makes it available in your app.

**Authentication:** Required (Client role)

**Request Body:**

```json
{
  "upload_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
  "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020"
}
```

**Field Descriptions:**

| Field                 | Type | Required    | Description              |
| --------------------- | ---- | ----------- | ------------------------ |
| `upload_id`           | UUID | ✅ Yes      | ID from Step 1 response  |
| `exercise_id`         | UUID | ✅ Yes      | Same as Step 1           |
| `assigned_workout_id` | UUID | ❌ Optional | Same as Step 1 (if used) |

**Response (201 Created):**

```json
{
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
    "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
    "media_url": "https://bucket.s3.us-east-1.amazonaws.com/videos/...",
    "media_type": "video",
    "status": "ready",
    "created_at": "2025-12-03T14:31:00Z"
  },
  "message": "Media upload confirmed successfully"
}
```

**Status Codes:**

- `201 Created` - Upload confirmed, media record created
- `400 Bad Request` - Invalid/expired upload_id or upload already confirmed
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Upload_id belongs to different user or invalid workout
- `404 Not Found` - File not found in S3 (Step 2 didn't complete)
- `422 Unprocessable Entity` - Invalid exercise_id or assigned_workout_id
- `500 Internal Server Error` - Server error

**What Happens Internally:**

1. ✅ Validates `upload_id` exists and hasn't expired
2. ✅ Verifies you're the user who initiated the upload
3. ✅ Checks file actually exists in S3
4. ✅ Creates permanent `MediaUpload` database record
5. ✅ Marks pending upload as confirmed (audit trail)

---

### 4. Direct Upload (Legacy/Testing Only)

**POST** `/feedback/media`

⚠️ **NOT RECOMMENDED FOR PRODUCTION** - Direct media upload bypassing the presigned URL workflow. Only use for testing or if you're managing S3 uploads externally.

**Authentication:** Required (Client role)

**Request Body:**

```json
{
  "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
  "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
  "media_url": "https://bucket.s3.amazonaws.com/videos/my-file.mp4",
  "media_type": "video",
  "s3_key": "videos/user-id/exercise-id/my-file.mp4"
}
```

**Response (201 Created):**

```json
{
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "client_user_id": "550e8400-e29b-41d4-a716-446655440000",
    "assigned_workout_id": "123e4567-e89b-12d3-a456-426614174020",
    "exercise_id": "123e4567-e89b-12d3-a456-426614174000",
    "media_url": "https://bucket.s3.amazonaws.com/videos/my-file.mp4",
    "media_type": "video",
    "status": "ready",
    "created_at": "2025-12-03T14:00:00Z"
  },
  "message": "Media uploaded successfully"
}
```

**Status Codes:**

- `201 Created` - Media record created
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Unauthorized access to workout
- `422 Unprocessable Entity` - Invalid exercise or workout ID
- `500 Internal Server Error` - Server error

---

## Complete Upload Workflow - Frontend Integration Guide

### Full Example Implementation (JavaScript/TypeScript)

```javascript
/**
 * Complete media upload workflow with error handling and progress tracking
 */
class MediaUploader {
  constructor(apiBaseUrl, authToken) {
    this.apiBaseUrl = apiBaseUrl;
    this.authToken = authToken;
  }

  /**
   * Upload a file using the two-step presigned URL workflow
   */
  async uploadMedia(file, exerciseId, assignedWorkoutId = null) {
    try {
      // Validate file before starting
      this.validateFile(file);

      // Step 1: Initiate upload - get presigned URL
      console.log("Step 1: Requesting presigned URL...");
      const presignedData = await this.initiateUpload(
        file,
        exerciseId,
        assignedWorkoutId
      );

      // Step 2: Upload to S3
      console.log("Step 2: Uploading to S3...");
      await this.uploadToS3(file, presignedData);

      // Step 3: Confirm upload
      console.log("Step 3: Confirming upload...");
      const mediaRecord = await this.confirmUpload(
        presignedData.upload_id,
        exerciseId,
        assignedWorkoutId
      );

      console.log("Upload complete!", mediaRecord);
      return mediaRecord;
    } catch (error) {
      console.error("Upload failed:", error);
      throw error;
    }
  }

  /**
   * Step 1: Request presigned URL from backend
   */
  async initiateUpload(file, exerciseId, assignedWorkoutId) {
    const mediaType = file.type.startsWith("video/") ? "video" : "image";
    const fileSizeMB = file.size / (1024 * 1024);

    const response = await fetch(
      `${this.apiBaseUrl}/feedback/media/initiate-upload`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.authToken}`,
        },
        body: JSON.stringify({
          filename: file.name,
          media_type: mediaType,
          file_size_mb: fileSizeMB,
          exercise_id: exerciseId,
          assigned_workout_id: assignedWorkoutId,
        }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to initiate upload");
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * Step 2: Upload file directly to S3
   */
  async uploadToS3(file, presignedData, onProgress = null) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            onProgress(percentComplete);
          }
        });
      }

      xhr.addEventListener("load", () => {
        if (xhr.status === 200) {
          resolve();
        } else {
          reject(new Error(`S3 upload failed: ${xhr.status}`));
        }
      });

      xhr.addEventListener("error", () => {
        reject(new Error("Network error during S3 upload"));
      });

      xhr.addEventListener("abort", () => {
        reject(new Error("Upload aborted"));
      });

      xhr.open("PUT", presignedData.upload_url);
      xhr.setRequestHeader("Content-Type", presignedData.content_type);
      xhr.send(file);
    });
  }

  /**
   * Step 3: Confirm upload with backend
   */
  async confirmUpload(uploadId, exerciseId, assignedWorkoutId) {
    const response = await fetch(
      `${this.apiBaseUrl}/feedback/media/confirm-upload`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.authToken}`,
        },
        body: JSON.stringify({
          upload_id: uploadId,
          exercise_id: exerciseId,
          assigned_workout_id: assignedWorkoutId,
        }),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to confirm upload");
    }

    const result = await response.json();
    return result.data;
  }

  /**
   * Validate file before upload
   */
  validateFile(file) {
    const validImageTypes = [
      "image/jpeg",
      "image/png",
      "image/gif",
      "image/webp",
    ];
    const validVideoTypes = [
      "video/mp4",
      "video/quicktime",
      "video/x-msvideo",
      "video/webm",
      "video/x-matroska",
    ];
    const maxImageSize = 10 * 1024 * 1024; // 10 MB
    const maxVideoSize = 100 * 1024 * 1024; // 100 MB

    const isImage = validImageTypes.includes(file.type);
    const isVideo = validVideoTypes.includes(file.type);

    if (!isImage && !isVideo) {
      throw new Error(`Invalid file type: ${file.type}`);
    }

    if (isImage && file.size > maxImageSize) {
      throw new Error("Image size exceeds 10 MB limit");
    }

    if (isVideo && file.size > maxVideoSize) {
      throw new Error("Video size exceeds 100 MB limit");
    }
  }
}

// Usage Example
const uploader = new MediaUploader("https://api.example.com", userToken);

// With progress tracking
const fileInput = document.getElementById("file-input");
fileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  try {
    const media = await uploader.uploadMedia(
      file,
      exerciseId,
      assignedWorkoutId
    );
    console.log("Media uploaded:", media);
  } catch (error) {
    alert(`Upload failed: ${error.message}`);
  }
});
```

---

### React Component Example

```jsx
import React, { useState } from "react";

function MediaUploadComponent({ exerciseId, assignedWorkoutId, authToken }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [uploadedMedia, setUploadedMedia] = useState(null);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      const uploader = new MediaUploader("https://api.example.com", authToken);

      // Override uploadToS3 to track progress
      const originalUploadToS3 = uploader.uploadToS3.bind(uploader);
      uploader.uploadToS3 = (file, presignedData) => {
        return originalUploadToS3(file, presignedData, setProgress);
      };

      const media = await uploader.uploadMedia(
        file,
        exerciseId,
        assignedWorkoutId
      );

      setUploadedMedia(media);
      setProgress(100);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        accept="video/*,image/*"
        onChange={handleFileSelect}
        disabled={uploading}
      />

      {uploading && (
        <div>
          <p>Uploading... {Math.round(progress)}%</p>
          <progress value={progress} max="100" />
        </div>
      )}

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {uploadedMedia && (
        <div>
          <p>Upload successful!</p>
          <video src={uploadedMedia.media_url} controls />
        </div>
      )}
    </div>
  );
}
```

---

### Error Handling Best Practices

```javascript
async function uploadWithRetry(
  file,
  exerciseId,
  assignedWorkoutId,
  maxRetries = 3
) {
  const uploader = new MediaUploader(API_BASE_URL, authToken);

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await uploader.uploadMedia(file, exerciseId, assignedWorkoutId);
    } catch (error) {
      console.error(`Upload attempt ${attempt} failed:`, error);

      // Don't retry on validation errors (4xx)
      if (
        error.message.includes("Invalid file") ||
        error.message.includes("400") ||
        error.message.includes("403")
      ) {
        throw error;
      }

      // Retry on network/server errors (5xx)
      if (attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
        console.log(`Retrying in ${delay}ms...`);
        await new Promise((resolve) => setTimeout(resolve, delay));
      } else {
        throw new Error(`Upload failed after ${maxRetries} attempts`);
      }
    }
  }
}
```

---

### Common Frontend Issues & Solutions

| Issue                          | Cause                                   | Solution                                                         |
| ------------------------------ | --------------------------------------- | ---------------------------------------------------------------- |
| **403 Forbidden on S3 upload** | Wrong Content-Type or expired URL       | Use exact `content_type` from Step 1, request new URL if expired |
| **404 on confirm**             | File didn't upload to S3                | Check Step 2 response was 200, verify network connection         |
| **400 Invalid file type**      | Wrong file extension or too large       | Validate client-side before Step 1                               |
| **Upload hangs**               | Network issue or CORS problem           | Implement timeout, check S3 bucket CORS config                   |
| **Progress stuck at 0%**       | Using fetch() instead of XMLHttpRequest | Use XMLHttpRequest or libraries with progress support            |

---

## S3 File Organization

Files are automatically organized in S3 with this structure:

```
your-bucket/
├── videos/
│   └── {user_id}/
│       └── {exercise_id}/
│           ├── 20251203_143022_squat_form.mp4
│           ├── 20251203_150130_deadlift.mp4
│           └── ...
└── images/
    └── {user_id}/
        └── {exercise_id}/
            ├── 20251203_143022_progress_photo.jpg
            ├── 20251203_151245_form_check.png
            └── ...
```

**Benefits:**

- User isolation (privacy)
- Easy to find/delete user's content
- Prevents filename collisions
- Organized by exercise context

---

## Media Query Endpoints

### 1. Get My Media Uploads

**GET** `/feedback/media/my-uploads`

Get all media uploads for the authenticated client.

**Authentication:** Required (Client)

**Query Parameters:**

- `assigned_workout_id` (UUID, optional): Filter by assigned workout
- `exercise_id` (UUID, optional): Filter by exercise
- `include_pose_frames` (boolean, optional, default: `false`): Include full frame-by-frame pose data. When `false` (default), only a lightweight summary is returned to reduce payload size by ~85%.

**Example:** `/feedback/media/my-uploads?exercise_id=123e4567-e89b-12d3-a456-426614174000`

**Example with full pose data:** `/feedback/media/my-uploads?include_pose_frames=true`

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
      "pose_analysis_status": "completed",
      "created_at": "2025-11-12T10:00:00"
    }
  ],
  "message": "Media uploads retrieved successfully"
}
```
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
- `include_pose_frames` (boolean, optional, default: `false`): Include full frame-by-frame pose data. When `false` (default), only a lightweight summary is returned to reduce payload size by ~85%.

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
      "pose_analysis_status": "completed",
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

### 3. Get Pose Data for Media

**GET** `/feedback/media/{media_id}/pose-data`

Get pose detection data for a specific media upload. Use this endpoint to fetch pose data on-demand without loading the full media list.

**Authentication:** Required (Coach or Client)

**Path Parameters:**

- `media_id` (UUID): The ID of the media

**Query Parameters:**

- `include_frames` (boolean, optional, default: `true`): Include full frame-by-frame pose data. Set to `false` for a lightweight summary.

**Example:** `/feedback/media/123e4567-e89b-12d3-a456-426614174040/pose-data`

**Example (summary only):** `/feedback/media/123e4567-e89b-12d3-a456-426614174040/pose-data?include_frames=false`

**Response:**

```json
{
  "data": {
    "media_id": "123e4567-e89b-12d3-a456-426614174040",
    "media_type": "video",
    "pose_analysis_status": "completed",
    "pose_data": {
      "version": "1.0",
      "model": "movenet_lightning",
      "summary": {
        "average_confidence": 0.85,
        "total_frames": 40,
        "detection_rate": 0.95
      },
      "video_info": {
        "width": 1920,
        "height": 1080,
        "duration": 20.5
      },
      "frames": [...]
    }
  },
  "message": "Pose data retrieved (status: completed)"
}
```

**Status Codes:**

- `200 OK`: Pose data retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to access this media
- `404 Not Found`: Media not found
- `500 Internal Server Error`: Server error

**Notes:**

- Clients can access pose data for their own media
- Coaches can access pose data for their clients' media
- Check `pose_analysis_status` to verify if processing is complete

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

### 3. Update Media Annotations

**PATCH** `/feedback/media/{media_id}/annotations`

Update annotations for a media upload. Only the client who uploaded the media can update its annotations.

**Authentication:** Required (Client - Owner of the media)

**Path Parameters:**

- `media_id` (UUID): The ID of the media

**Request Body:**

```json
{
  "frames": [
    {
      "timestamp": 1.5,
      "markers": [
        {
          "x": 100,
          "y": 200,
          "label": "elbow",
          "color": "#FF5733"
        },
        {
          "x": 150,
          "y": 250,
          "label": "shoulder",
          "color": "#33FF57"
        }
      ]
    },
    {
      "timestamp": 3.2,
      "markers": [
        {
          "x": 110,
          "y": 210,
          "label": "elbow",
          "color": "#FF5733"
        }
      ]
    }
  ],
  "notes": "Form correction points - focus on elbow alignment",
  "version": "1.0"
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
    "presigned_url": "https://s3.amazonaws.com/bucket/video.mp4?signature=...",
    "media_type": "video",
    "status": "ready",
    "created_at": "2025-11-12T10:00:00",
    "annotations": {
      "frames": [
        {
          "timestamp": 1.5,
          "markers": [
            {
              "x": 100,
              "y": 200,
              "label": "elbow",
              "color": "#FF5733"
            }
          ]
        }
      ],
      "notes": "Form correction points - focus on elbow alignment",
      "version": "1.0"
    }
  },
  "message": "Annotations updated successfully"
}
```

**Status Codes:**

- `200 OK`: Annotations updated successfully
- `400 Bad Request`: Invalid JSON or missing annotations data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to update this media's annotations
- `404 Not Found`: Media not found
- `500 Internal Server Error`: Server error

**Notes:**

- Annotations are stored as JSONB and can contain any structured data
- Common use cases: timestamps, coordinates, markers, drawing paths, notes
- The entire annotations object is replaced with each update (not merged)
- Only the client who uploaded the media can update annotations
- Presigned URL for the video is included in the response (expires in 1 hour)

**Annotation Structure Guidelines:**

The annotations field is flexible JSON, but here are recommended structures:

```json
{
  "frames": [
    {
      "timestamp": 1.5,
      "markers": [{ "x": 100, "y": 200, "label": "point", "color": "#FF0000" }],
      "shapes": [
        {
          "type": "circle",
          "center": { "x": 150, "y": 150 },
          "radius": 20,
          "color": "#00FF00"
        }
      ],
      "paths": [
        {
          "points": [
            { "x": 10, "y": 10 },
            { "x": 20, "y": 20 }
          ],
          "color": "#0000FF",
          "thickness": 2
        }
      ]
    }
  ],
  "notes": "Overall feedback",
  "metadata": {
    "version": "1.0",
    "created_by": "mobile_app_v2.1"
  }
}
```

---

### 4. Get Media Annotations

**GET** `/feedback/media/{media_id}/annotations`

Retrieve annotations for a specific media upload.

**Authentication:** Required (Client - Owner or Coach)

**Path Parameters:**

- `media_id` (UUID): The ID of the media

**Response:**

```json
{
  "data": {
    "media_id": "123e4567-e89b-12d3-a456-426614174040",
    "annotations": {
      "frames": [
        {
          "timestamp": 1.5,
          "markers": [
            {
              "x": 100,
              "y": 200,
              "label": "elbow",
              "color": "#FF5733"
            }
          ]
        }
      ],
      "notes": "Form correction points",
      "version": "1.0"
    },
    "created_at": "2025-11-12T10:00:00"
  },
  "message": "Annotations retrieved successfully"
}
```

**Status Codes:**

- `200 OK`: Annotations retrieved successfully
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to view this media's annotations
- `404 Not Found`: Media not found
- `500 Internal Server Error`: Server error

**Notes:**

- Clients can view annotations on their own uploads
- Coaches can view annotations on their clients' uploads
- Returns an empty object `{}` if no annotations exist
- Requires active coach-client relationship for coaches

---

### 5. Generate Download URL

**POST** `/feedback/media/{media_id}/generate-download-url`

Generate a temporary download URL for a media file.

**Authentication:** Required (Client - Owner or Coach)

**Path Parameters:**

- `media_id` (UUID): The ID of the media

**Response:**

```json
{
  "data": {
    "download_url": "https://s3.amazonaws.com/bucket/video.mp4?signature=...",
    "expires_in_seconds": 3600
  },
  "message": "Download URL generated successfully"
}
```

**Status Codes:**

- `200 OK`: Download URL generated successfully
- `400 Bad Request`: Media file does not have an S3 key
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not authorized to access this media
- `404 Not Found`: Media not found
- `500 Internal Server Error`: Server error

**Notes:**

- Useful for private media files
- Returns a presigned URL that expires after 1 hour
- Clients can access their own media
- Coaches can access their clients' media

---

## Automatic Pose Detection

### Overview

Pose detection is **automatic and runs in the background** after video upload confirmation. This provides:
- **Instant upload responses** (<1 second)
- **Non-blocking processing** (8-12 seconds in background)
- **Status tracking** via `pose_analysis_status` field

### Processing Workflow

1. Client uploads video → Confirms upload
2. API returns immediately with `pose_analysis_status: "pending"`
3. Background task processes pose detection (8-12 seconds)
4. Status updates to `"completed"` when ready

### Pose Analysis Status Values

| Status | Description |
|--------|-------------|
| `pending` | Processing not yet started |
| `processing` | Currently analyzing video |
| `completed` | Pose data available |
| `failed` | Processing encountered an error |

### Payload Optimization

**Default responses are lightweight** (~5-20KB per video instead of ~150KB).

By default, `pose_data` returns only a summary without frame-by-frame keypoints. Use query parameters to control payload size:

| Endpoint | Parameter | Effect |
|----------|-----------|--------|
| `GET /feedback/media/my-uploads` | `include_pose_frames=true` | Returns full frame data |
| `GET /feedback/media/client/{id}` | `include_pose_frames=true` | Returns full frame data |
| `GET /feedback/media/{id}/pose-data` | `include_frames=true` | Returns full frame data |

**Lightweight Summary Response (default):**
```json
{
  "pose_data": {
    "version": "1.0",
    "model": "movenet_lightning",
    "summary": {
      "average_confidence": 0.85,
      "total_frames": 40,
      "detection_rate": 0.95
    },
    "video_info": {"width": 1920, "height": 1080, "duration": 20.5},
    "frame_count": 40,
    "note": "Full frames via include_pose_frames=true"
  }
}
```

**Full Frame Data Response (with `include_pose_frames=true`):**
```json
{
  "pose_data": {
    "...summary fields...",
    "frames": [
      {
        "timestamp": 0.0,
        "frame_number": 0,
        "keypoints": {
          "nose": {"x": 0.52, "y": 0.18, "confidence": 0.95},
          "left_shoulder": {"x": 0.42, "y": 0.35, "confidence": 0.91}
        },
        "confidence": 0.85
      }
    ]
  }
}
```

### Coordinate System

**All coordinates are NORMALIZED (0-1 range)** for easy frontend scaling:

```
x_pixel = x * video_width
y_pixel = y * video_height
```

This means the same pose data works at any video display size.

### Keypoints Detected (17 total)

- **Head**: nose, left_eye, right_eye, left_ear, right_ear
- **Upper Body**: left_shoulder, right_shoulder, left_elbow, right_elbow, left_wrist, right_wrist
- **Lower Body**: left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle

### Full Pose Data Structure

When you call `GET /feedback/media/my-uploads?include_pose_frames=true` or `GET /feedback/media/client/{client_id}?include_pose_frames=true`, video responses include:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174040",
  "media_type": "video",
  "presigned_url": "https://...",
  "pose_analysis_status": "completed",
  "pose_data": {
    "version": "1.0",
    "model": "movenet_lightning",
    "processed_at": "2026-01-14T10:00:00Z",
    "video_info": {
      "width": 1920,
      "height": 1080,
      "duration": 15.5
    },
    "settings": {
      "fps": 2,
      "frames_analyzed": 40,
      "coordinate_system": "normalized",
      "coordinate_note": "Multiply x by video width and y by video height to get pixel coordinates"
    },
    "keypoint_names": ["nose", "left_eye", "..."],
    "skeleton_connections": [["nose", "left_eye"], ["left_shoulder", "left_elbow"], "..."],
    "summary": {
      "average_confidence": 0.82,
      "total_frames": 40,
      "detection_rate": 1.0
    },
    "frames": [
      {
        "timestamp": 0.0,
        "frame_number": 0,
        "keypoints": {
          "nose": {"x": 0.52, "y": 0.18, "confidence": 0.95},
          "left_shoulder": {"x": 0.42, "y": 0.35, "confidence": 0.91},
          "right_shoulder": {"x": 0.62, "y": 0.34, "confidence": 0.89}
        },
        "confidence": 0.85
      },
      {
        "timestamp": 0.5,
        "frame_number": 1,
        "keypoints": {"..."}
      }
    ]
  }
}
```

### Best Practices for Frontend

1. **Check status first**: Always check `pose_analysis_status` before accessing `pose_data`
2. **Use lightweight responses**: Don't use `include_pose_frames=true` unless needed
3. **Load on-demand**: Use `/feedback/media/{id}/pose-data` to fetch detailed pose data only when viewing a specific video
4. **Poll for completion**: If status is `"processing"`, poll every 2-3 seconds until `"completed"`

### Frontend Integration Example

```javascript
// Draw pose overlay on canvas
function drawPose(ctx, poseData, videoElement) {
  const videoWidth = videoElement.videoWidth;
  const videoHeight = videoElement.videoHeight;
  const currentTime = videoElement.currentTime;

  // Find closest frame to current video time
  const frame = poseData.frames.reduce((closest, f) => {
    return Math.abs(f.timestamp - currentTime) <
      Math.abs(closest.timestamp - currentTime)
      ? f
      : closest;
  });

  // Draw keypoints (convert normalized to pixels)
  for (const [name, kp] of Object.entries(frame.keypoints)) {
    if (kp.confidence > 0.3) {
      const x = kp.x * videoWidth; // Normalized -> pixels
      const y = kp.y * videoHeight;
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, 2 * Math.PI);
      ctx.fillStyle = `rgba(255, 0, 0, ${kp.confidence})`;
      ctx.fill();
    }
  }

  // Draw skeleton lines
  for (const [start, end] of poseData.skeleton_connections) {
    const startKp = frame.keypoints[start];
    const endKp = frame.keypoints[end];
    if (
      startKp &&
      endKp &&
      startKp.confidence > 0.3 &&
      endKp.confidence > 0.3
    ) {
      ctx.beginPath();
      ctx.moveTo(startKp.x * videoWidth, startKp.y * videoHeight);
      ctx.lineTo(endKp.x * videoWidth, endKp.y * videoHeight);
      ctx.strokeStyle = "rgba(0, 255, 0, 0.8)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }
}
```

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
    "coordinates": { "x": 100, "y": 200 }
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
      "coordinates": { "x": 100, "y": 200 }
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
        "coordinates": { "x": 100, "y": 200 }
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
          "coordinates": { "x": 100, "y": 200 }
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
    "coordinates": { "x": 120, "y": 210 }
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
      "coordinates": { "x": 120, "y": 210 }
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

### Relationship Status Enum

- `pending`: Invitation/request sent, awaiting acceptance
- `active`: Relationship accepted, coach can assign workouts
- `paused`: Temporarily paused, can be reactivated
- `terminated`: Relationship ended, cannot be reactivated

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
