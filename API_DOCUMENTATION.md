# App Backend API Documentation

This guide is written for frontend engineers integrating with this backend. It reflects the endpoints currently registered in the codebase.

## 1. Base URL

- Local: http://localhost:8000
- Swagger UI: /docs
- ReDoc: /redoc

## 2. Authentication

Most endpoints require a bearer token.

Header format:

Authorization: Bearer <access_token>

Access token is returned from:

- POST /users/login
- POST /users/verify-otp

Token lifetime: 60 minutes.

### JWT payload fields used in this app

- user_id (UUID as string)
- email
- full_name
- role (coach | client | both)
- is_activated (bool)
- exp

Note: admin endpoints require is_admin=true in JWT payload.

## 3. Roles

- client
- coach
- both

For coach-only actions, users with role both are accepted as coach.

## 4. Standard response shapes

Success responses:

{
"data": {},
"message": "Short status message"
}

Error responses (FastAPI default):

{
"detail": "Error message"
}

## 5. Enum values

### Relationship status

- pending
- active
- paused
- terminated

### Assignment status

- assigned
- in_progress
- completed
- skipped

### Workout difficulty_level

- beginner
- intermediate
- advanced

## 6. Quick endpoint index

### Health

- GET /health

### Users

- POST /users/signup
- POST /users/login
- POST /users/verify-otp
- POST /users/forget-password
- POST /users/reset-password
- GET /users/me
- GET /users/getAllUsers (admin)
- GET /users/getUser/{user_id} (admin)

### Admin namespace (duplicate admin user endpoints)

- GET /admin/users/getAllUsers
- GET /admin/users/getUser/{user_id}

### Relationships

- POST /relationships
- GET /relationships
- GET /relationships/{relationship_id}
- PUT /relationships/{relationship_id}
- DELETE /relationships/{relationship_id}
- GET /relationships/coaches/available
- GET /relationships/clients/available
- GET /relationships/clients/assigned

### Exercise library

- POST /workouts/exercises
- GET /workouts/exercises
- GET /workouts/exercises/{exercise_id}

### Workouts

- POST /workouts/workouts
- GET /workouts/workouts
- GET /workouts/{workout_id}
- PUT /workouts/{workout_id}
- DELETE /workouts/{workout_id}

### Workout-exercise links

- POST /workouts/{workout_id}/exercises
- PUT /workouts/{workout_id}/exercises/{exercise_id}
- DELETE /workouts/{workout_id}/exercises/{exercise_id}

### Assignments

- POST /workouts/assignments
- GET /workouts/assignments/my-workouts
- GET /workouts/assignments/client/{client_id}
- PUT /workouts/assignments/{assignment_id}
- DELETE /workouts/assignments/{assignment_id}

## 7. Detailed endpoint docs

## 7.1 Health

### GET /health

Purpose: API liveness.

Auth: none.

Response:

{
"status": "ok"
}

Status codes:

- 200

## 7.2 User endpoints

### POST /users/signup

Purpose: register user and send OTP email.

Auth: none.

Request body:

{
"email": "new.user@example.com",
"password": "StrongPass123",
"full_name": "New User",
"role": "client"
}

Notes:

- role is optional (defaults to client)
- account starts with is_activated=false
- OTP validity is 10 minutes

Success response:

{
"data": {},
"message": "Verification OTP sent to email"
}

Status codes:

- 200
- 400 (email already registered)

### POST /users/login

Purpose: email/password login.

Auth: none.

Request body:

{
"email": "user@example.com",
"password": "StrongPass123"
}

Success response (activated account):

{
"data": {
"access_token": "<jwt>",
"user": {
"id": "uuid",
"email": "user@example.com",
"full_name": "User",
"role": "client"
}
},
"message": "Login successful"
}

Success response (not activated):

{
"data": {
"requires_activation": true
},
"message": "Account not activated. Verification OTP sent to email"
}

Status codes:

- 200
- 401 (invalid email/password)

### POST /users/verify-otp

Purpose: verify OTP, activate account, return token.

Auth: none.

Request body:

{
"email": "new.user@example.com",
"token": "123456"
}

Success response:

{
"data": {
"access_token": "<jwt>",
"user": {
"id": "uuid",
"email": "new.user@example.com",
"full_name": "New User",
"role": "client"
}
},
"message": "Account activated successfully"
}

Status codes:

- 200
- 400 (user not found, no OTP, invalid OTP, expired OTP)

### POST /users/forget-password

Purpose: send password reset OTP.

Auth: none.

Request body:

{
"email": "user@example.com"
}

Success response:

{
"data": {},
"message": "If an account with this email exists, a password reset code has been sent"
}

Status codes:

- 200
- 400 (account exists but not activated)

### POST /users/reset-password

Purpose: reset password with OTP.

Auth: none.

Request body:

{
"email": "user@example.com",
"otp": "123456",
"new_password": "NewStrongPass789"
}

Success response:

{
"data": {},
"message": "Password reset successfully. Please login with your new password"
}

Status codes:

- 200
- 400 (invalid email/OTP, expired OTP, no request, account not activated)

### GET /users/me

Purpose: fetch current authenticated user.

Auth: required.

Success response:

{
"data": {
"id": "uuid",
"email": "user@example.com",
"full_name": "User Name",
"role": "client"
},
"message": "User data retrieved successfully"
}

Status codes:

- 200
- 401
- 404

### GET /users/getAllUsers

Purpose: admin-only list users (legacy path).

Auth: admin token required.

Success response:

{
"data": [
{
"id": "uuid",
"email": "a@example.com",
"full_name": "A",
"role": "coach"
}
],
"message": "Users retrieved successfully"
}

Status codes:

- 200
- 401
- 403

### GET /users/getUser/{user_id}

Purpose: admin-only fetch one user (legacy path).

Auth: admin token required.

Path param:

- user_id (UUID)

Success response:

{
"data": {
"id": "uuid",
"email": "a@example.com",
"full_name": "A",
"role": "coach"
},
"message": "User retrieved successfully"
}

Status codes:

- 200
- 401
- 403
- 404

## 7.3 Admin namespace endpoints

These are duplicates of the admin user endpoints above.

### GET /admin/users/getAllUsers

Auth: admin token required.

### GET /admin/users/getUser/{user_id}

Auth: admin token required.

## 7.4 Relationship endpoints

### POST /relationships

Purpose: create coach-client relationship request.

Auth: required.

Body option A (coach invites client):

{
"client_user_id": "client-uuid"
}

Body option B (client requests coach):

{
"coach_user_id": "coach-uuid"
}

Rules:

- exactly one of coach_user_id/client_user_id
- relationship starts as pending
- duplicate pair returns conflict

Success response:

{
"data": {
"id": "relationship-uuid",
"coach_user_id": "coach-uuid",
"client_user_id": "client-uuid",
"status": "pending",
"created_at": "2026-04-15T10:00:00Z",
"updated_at": "2026-04-15T10:00:00Z"
},
"message": "Relationship request created successfully"
}

Status codes:

- 201
- 403
- 404
- 409
- 422

### GET /relationships

Purpose: list relationships for current user.

Auth: required.

Query params:

- status_filter=pending|active|paused|terminated

Example:

GET /relationships?status_filter=active

Success response:

{
"data": [
{
"id": "relationship-uuid",
"coach_user_id": "coach-uuid",
"coach_email": "coach@example.com",
"coach_name": "Coach One",
"client_user_id": "client-uuid",
"client_email": "client@example.com",
"client_name": "Client One",
"status": "active",
"created_at": "2026-04-15T10:00:00Z",
"updated_at": "2026-04-16T10:00:00Z"
}
],
"message": "Relationships retrieved successfully"
}

Status codes:

- 200
- 422 (invalid status_filter)

### GET /relationships/{relationship_id}

Purpose: fetch one relationship.

Auth: required and user must be one party.

Status codes:

- 200
- 403
- 404

### PUT /relationships/{relationship_id}

Purpose: update relationship status.

Auth: required and user must be one party.

Request body:

{
"status": "active"
}

Allowed transitions:

- pending -> active or terminated
- active -> paused or terminated
- paused -> active or terminated
- terminated -> no updates

Status codes:

- 200
- 403
- 404
- 422

### DELETE /relationships/{relationship_id}

Purpose: hard delete relationship.

Auth: required and user must be one party.

Rule:

- only pending or terminated can be deleted

Success response:

{
"data": {},
"message": "Relationship deleted successfully"
}

Status codes:

- 200
- 403
- 404
- 422

### GET /relationships/coaches/available

Purpose: list activated coaches not already linked to current user as client.

Auth: required.

Response item shape:

{
"id": "coach-uuid",
"email": "coach@example.com",
"full_name": "Coach One",
"role": "coach"
}

### GET /relationships/clients/available

Purpose: list users not connected to current coach.

Auth: required (coach/both only).

Response item shape:

{
"id": "client-uuid",
"email": "client@example.com",
"full_name": "Client One",
"role": "client"
}

### GET /relationships/clients/assigned

Purpose: list active clients for current coach.

Auth: required (coach/both only).

Response item shape:

{
"id": "client-uuid",
"email": "client@example.com",
"full_name": "Client One",
"role": "client",
"relationship_id": "relationship-uuid",
"relationship_status": "active"
}

## 7.5 Exercise library endpoints

All endpoints below are under /workouts.

### POST /workouts/exercises

Purpose: create exercise.

Auth: required (coach/both only).

Request body:

{
"name": "Push Up",
"description": "Bodyweight push movement",
"category": "strength",
"muscle_group": ["chest", "triceps"],
"instructions": "Keep core tight",
"demo_video_url": "https://example.com/pushup",
"difficulty": "beginner",
"equipment_needed": []
}

Status codes:

- 201
- 403

### GET /workouts/exercises

Purpose: list exercises.

Auth: required.

Query params:

- category (optional)
- difficulty (optional)

Example:

GET /workouts/exercises?category=strength&difficulty=beginner

### GET /workouts/exercises/{exercise_id}

Purpose: get one exercise.

Auth: required.

Status codes:

- 200
- 404

## 7.6 Workout endpoints

Important: create/list routes are /workouts/workouts in current implementation.

### POST /workouts/workouts

Purpose: create workout.

Auth: required (coach/both only).

Request body:

{
"name": "Upper Body Day",
"description": "Chest and triceps",
"difficulty_level": "intermediate",
"estimated_duration_minutes": 45,
"category": "strength",
"is_template": true,
"exercises": [
{
"exercise_id": "exercise-uuid",
"order_index": 1,
"sets": 4,
"reps": 10,
"duration_seconds": null,
"rest_seconds": 90,
"notes": "Controlled tempo"
}
]
}

Status codes:

- 201
- 403
- 422 (invalid exercise id/constraint)

### GET /workouts/workouts

Purpose: list workouts created by current coach.

Auth: required (coach/both only).

Query params:

- is_template=true|false
- category=<string>

### GET /workouts/{workout_id}

Purpose: get full workout details.

Auth: required.

Access rules:

- coach/both: only own workouts
- client: only assigned workouts

Status codes:

- 200
- 403
- 404

### PUT /workouts/{workout_id}

Purpose: update workout metadata.

Auth: required (owner coach only).

Request body (all optional):

{
"name": "Upper Body Day A",
"description": "Updated",
"difficulty_level": "advanced",
"estimated_duration_minutes": 50,
"category": "hypertrophy",
"is_template": false
}

### DELETE /workouts/{workout_id}

Purpose: delete workout.

Auth: required (owner coach only).

Behavior: cascades related workout-exercise links and assignments.

## 7.7 Workout exercise-management endpoints

### POST /workouts/{workout_id}/exercises

Purpose: add exercise to workout.

Auth: required (owner coach only).

Request body:

{
"exercise_id": "exercise-uuid",
"order_index": 2,
"sets": 3,
"reps": 12,
"duration_seconds": null,
"rest_seconds": 60,
"notes": "Squeeze at top"
}

Status codes:

- 201
- 403
- 404
- 422

### PUT /workouts/{workout_id}/exercises/{exercise_id}

Purpose: update workout-exercise config.

Auth: required (owner coach only).

Important: exercise_id here is the workout_exercises row id, not library exercise id.

Request body (all optional):

{
"order_index": 1,
"sets": 5,
"reps": 8,
"duration_seconds": null,
"rest_seconds": 120,
"notes": "Heavier loading"
}

### DELETE /workouts/{workout_id}/exercises/{exercise_id}

Purpose: remove exercise from workout.

Auth: required (owner coach only).

Important: exercise_id here is the workout_exercises row id.

## 7.8 Assignment endpoints

### POST /workouts/assignments

Purpose: assign workout to client.

Auth: required (coach/both only).

Preconditions:

- workout belongs to current coach
- active coach-client relationship exists

Request body:

{
"workout_id": "workout-uuid",
"client_user_id": "client-uuid",
"assigned_date": "2026-04-15",
"due_date": "2026-04-30",
"coach_notes": "Do this 3x/week"
}

Status codes:

- 201
- 403
- 404
- 422

### GET /workouts/assignments/my-workouts

Purpose: client list of own assignments.

Auth: required.

Query params:

- status_filter=assigned|in_progress|completed|skipped

Example:

GET /workouts/assignments/my-workouts?status_filter=in_progress

### GET /workouts/assignments/client/{client_id}

Purpose: coach list of one client assignments.

Auth: required (coach/both only).

Query params:

- status_filter=assigned|in_progress|completed|skipped

### PUT /workouts/assignments/{assignment_id}

Purpose: update assignment.

Auth: required.

Role behavior:

- coach owner: can update due_date, status, coach_notes, client_notes
- client assignee: can update status, client_notes only

Coach request body example:

{
"due_date": "2026-05-01",
"status": "in_progress",
"coach_notes": "Increase load",
"client_notes": "Felt strong"
}

Client request body example:

{
"status": "completed",
"client_notes": "Done"
}

### DELETE /workouts/assignments/{assignment_id}

Purpose: unassign workout.

Auth: required (coach owner only).

Status codes:

- 200
- 403
- 404

## 8. Frontend implementation flows

### Signup + activation

1. POST /users/signup
2. Show OTP input screen
3. POST /users/verify-otp
4. Store access_token

### Login

1. POST /users/login
2. If data.requires_activation=true, route to OTP flow
3. Else save token and user object

### Coach workflow

1. Build relationship to active
2. Create exercises if needed
3. Create workout
4. Assign workout

### Client workflow

1. GET /workouts/assignments/my-workouts
2. GET /workouts/{workout_id} for detail
3. PUT /workouts/assignments/{assignment_id} to update progress

## 9. Important notes for frontend

- Protected endpoints always require bearer token.
- Query param for relationship filtering is status_filter.
- Query param for assignment filtering is status_filter.
- Feedback routes are currently not implemented.
- Media upload routes are currently not registered in API router.
- There are two admin endpoint namespaces (/users/_ and /admin/users/_).

## 10. cURL starter examples

Login:

curl -X POST "http://localhost:8000/users/login" \
 -H "Content-Type: application/json" \
 -d '{"email":"user@example.com","password":"StrongPass123"}'

Get current user:

curl -X GET "http://localhost:8000/users/me" \
 -H "Authorization: Bearer <access_token>"

Create workout:

curl -X POST "http://localhost:8000/workouts/workouts" \
 -H "Authorization: Bearer <access_token>" \
 -H "Content-Type: application/json" \
 -d '{"name":"Upper Body Day","is_template":true,"exercises":[]}'
