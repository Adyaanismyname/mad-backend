# Fit & Fuel Backend API Documentation

Last updated: 2026-05-05
Audience: Frontend team (web/mobile)

This document is implementation-accurate for the current Express backend, including auth, profile, workouts, local video upload, trainer feedback, and video annotations.

## 1. API Basics

- Local base URL: http://localhost:8000
- API prefix: /api
- Health endpoint: GET /health
- Request content type for JSON endpoints: application/json
- Upload content type: multipart/form-data
- Auth strategy: JWT Bearer token

### 1.1 Auth Header

Use this header for protected routes:

```http
Authorization: Bearer <jwt_token>
```

### 1.2 Response Conventions

- Success responses generally return one of:
  - message + payload object
  - payload object list
- Error responses generally return:

```json
{
  "message": "Human readable error"
}
```

Validation errors usually return:

```json
{
  "message": "Validation failed",
  "errors": [
    {
      "type": "field",
      "value": "...",
      "msg": "...",
      "path": "...",
      "location": "body"
    }
  ]
}
```

## 2. Role-Based Access Matrix

| Endpoint                                                  | Client         | Trainer                     |
| --------------------------------------------------------- | -------------- | --------------------------- |
| POST /api/auth/signup                                     | Yes            | Yes                         |
| POST /api/auth/login                                      | Yes            | Yes                         |
| GET /api/auth/me                                          | Yes            | Yes                         |
| GET /api/users?role=client\|trainer                       | Yes            | Yes                         |
| PUT /api/users/profile                                    | Yes            | Yes                         |
| POST /api/workouts/client                                 | Yes            | No                          |
| POST /api/workouts/trainer                                | No             | Yes                         |
| POST /api/workouts/:id/assign                             | No             | Yes                         |
| GET /api/workouts/mine                                    | Yes            | Yes                         |
| GET /api/workouts/assigned/me                             | Yes            | No                          |
| GET /api/workouts/assigned/by-me                          | No             | Yes                         |
| POST /api/videos/upload                                   | Yes            | No                          |
| GET /api/videos/mine                                      | Yes            | No                          |
| GET /api/videos/review                                    | No             | Yes                         |
| GET /api/videos/:videoId                                  | Own video only | Assigned client videos only |
| GET /api/videos/:videoId/comments                         | Own video only | Assigned client videos only |
| POST /api/videos/:videoId/comments                        | No             | Assigned client videos only |
| DELETE /api/videos/:videoId                               | Own video only | No                          |
| GET /api/videos/:videoId/annotations                      | Own video only | Assigned client videos only |
| POST /api/videos/:videoId/annotations/strokes             | No             | Assigned client videos only |
| DELETE /api/videos/:videoId/annotations/strokes/:strokeId | No             | Assigned client videos only |
| DELETE /api/videos/:videoId/annotations                   | No             | Assigned client videos only |
| POST /api/relationships/request                           | Yes            | No                          |
| GET /api/relationships/my-requests                        | Yes            | No                          |
| GET /api/relationships/my-coach                           | Yes            | No                          |
| GET /api/relationships/incoming                           | No             | Yes                         |
| GET /api/relationships/my-clients                         | No             | Yes                         |
| PATCH /api/relationships/:id/accept                       | No             | Yes                         |
| PATCH /api/relationships/:id/reject                       | No             | Yes                         |
| PATCH /api/relationships/:id/terminate                    | Yes            | Yes                         |
| POST /api/ai-plans/:clientId/diet                         | No             | Yes                         |
| POST /api/ai-plans/:clientId/workout                      | No             | Yes                         |
| GET /api/ai-plans/:clientId                               | Yes (own only) | Yes (active clients only)   |
| GET /api/ai-plans/mine                                    | Yes            | No                          |
| DELETE /api/ai-plans/:planId                              | No             | Yes (own plans only)        |

## 3. Domain Models

## 3.1 User

```json
{
  "_id": "string",
  "name": "string",
  "email": "string",
  "role": "trainer | client",
  "profile": {
    "age": "number (client)",
    "weight": "number (client)",
    "bmi": "number (client)",
    "experienceYears": "number (trainer)",
    "expertise": "string (trainer)",
    "bio": "string"
  },
  "createdAt": "ISO string",
  "updatedAt": "ISO string"
}
```

## 3.2 Workout

```json
{
  "_id": "string",
  "title": "string",
  "description": "string",
  "exercises": [
    {
      "name": "string",
      "sets": "number",
      "reps": "number",
      "durationSec": "number",
      "restSec": "number",
      "notes": "string"
    }
  ],
  "createdBy": "User._id",
  "creatorRole": "trainer | client",
  "createdAt": "ISO string",
  "updatedAt": "ISO string"
}
```

## 3.3 WorkoutAssignment

```json
{
  "_id": "string",
  "workout": "Workout._id",
  "trainer": "User._id",
  "client": "User._id",
  "notes": "string",
  "startDate": "ISO string",
  "endDate": "ISO string",
  "status": "assigned | in_progress | completed",
  "createdAt": "ISO string",
  "updatedAt": "ISO string"
}
```

## 3.4 Video

```json
{
  "_id": "string",
  "client": "User._id",
  "workout": "Workout._id | null",
  "workoutAssignment": "WorkoutAssignment._id | null",
  "title": "string",
  "description": "string",
  "fileName": "string",
  "originalName": "string",
  "filePath": "uploads/videos/<filename>",
  "mimeType": "video/*",
  "sizeBytes": "number",
  "status": "uploaded | reviewed",
  "uploadedAt": "ISO string",
  "createdAt": "ISO string",
  "updatedAt": "ISO string"
}
```

## 3.5 VideoComment

```json
{
  "_id": "string",
  "video": "Video._id",
  "trainer": "User._id",
  "comment": "string",
  "createdAt": "ISO string",
  "updatedAt": "ISO string"
}
```

## 3.6 VideoAnnotation

One document per video. Strokes are **global** — they apply to the entire video regardless of the current playback position. All `x`/`y` coordinates are **normalized** (0.0–1.0 relative to the video canvas dimensions), making them resolution-independent.

```json
{
  "_id": "string",
  "video": "Video._id",
  "trainer": "User._id",
  "strokes": [
    {
      "strokeId": "uuid-string",
      "type": "freehand | line | arrow | rect | circle | text",
      "color": "#FF0000",
      "strokeWidth": 2,
      "points": [
        { "x": 0.25, "y": 0.4 },
        { "x": 0.3, "y": 0.45 }
      ],
      "label": "string | null"
    }
  ],
  "createdAt": "ISO string",
  "updatedAt": "ISO string"
}
```

### Stroke field reference

| Field         | Type           | Required                 | Notes                                                             |
| ------------- | -------------- | ------------------------ | ----------------------------------------------------------------- |
| `strokeId`    | string (UUID)  | server-generated         | Use this to target DELETE operations                              |
| `type`        | enum           | No (default: `freehand`) | `freehand`, `line`, `arrow`, `rect`, `circle`, `text`             |
| `color`       | hex string     | No (default: `#FF0000`)  | e.g. `#00FF00`, `#1A2B3CFF` (with alpha)                          |
| `strokeWidth` | number 1–50    | No (default: `2`)        | Pixel width before normalization                                  |
| `points`      | `{x,y}[]`      | No                       | Normalized 0–1 coords. For `text` use a single point for position |
| `label`       | string \| null | No                       | Text content when `type` is `text`                                |

## 4. Health

## GET /health

Checks if server is alive.

Success 200:

```json
{
  "status": "ok",
  "service": "Fit & Fuel API"
}
```

## 5. Auth Endpoints

## POST /api/auth/signup

Registers a new user.

### Body

```json
{
  "name": "Client One",
  "email": "client1@example.com",
  "password": "secret123",
  "role": "client",
  "profile": {
    "age": 24,
    "weight": 70,
    "bmi": 22.9,
    "bio": "Beginner"
  }
}
```

### Validation

- name: required string
- email: required valid email
- password: required min length 6
- role: required, one of trainer/client
- If role=client, profile.age + profile.weight + profile.bmi are required
- If role=trainer, profile.experienceYears + profile.expertise are required

### Success 201

```json
{
  "message": "Signup successful",
  "token": "<jwt>",
  "user": {
    "id": "...",
    "name": "Client One",
    "email": "client1@example.com",
    "role": "client",
    "profile": {
      "age": 24,
      "weight": 70,
      "bmi": 22.9,
      "bio": "Beginner"
    }
  }
}
```

### Errors

- 400 validation failure
- 409 email already exists

## POST /api/auth/login

Authenticates existing user.

### Body

```json
{
  "email": "client1@example.com",
  "password": "secret123"
}
```

### Success 200

Returns token and user object.

### Errors

- 400 validation failure
- 401 invalid credentials

## GET /api/auth/me

Returns currently authenticated user.

Auth required: Yes

### Success 200

```json
{
  "user": {
    "_id": "...",
    "name": "...",
    "email": "...",
    "role": "client",
    "profile": {},
    "createdAt": "...",
    "updatedAt": "..."
  }
}
```

### Errors

- 401 token missing/invalid

## 6. User Endpoints

## GET /api/users?role=client|trainer

Lists users by role.

Auth required: Yes

### Query params

- role: required, trainer or client

### Success 200

```json
{
  "users": [
    {
      "_id": "...",
      "name": "...",
      "email": "...",
      "role": "client",
      "profile": {}
    }
  ]
}
```

### Errors

- 400 invalid role query
- 401 token missing/invalid

## PUT /api/users/profile

Updates current user profile.

Auth required: Yes

### Body (client example)

```json
{
  "name": "Client One Updated",
  "profile": {
    "age": 26,
    "weight": 69,
    "bmi": 22.3,
    "bio": "Consistency focus"
  }
}
```

### Body (trainer example)

```json
{
  "name": "Trainer One Updated",
  "profile": {
    "experienceYears": 7,
    "expertise": "Strength",
    "bio": "Certified trainer"
  }
}
```

### Role-specific update behavior

- Client can update: name, profile.age, profile.weight, profile.bmi, profile.bio
- Trainer can update: name, profile.experienceYears, profile.expertise, profile.bio

### Success 200

```json
{
  "message": "Profile updated successfully",
  "user": {
    "_id": "...",
    "name": "...",
    "email": "...",
    "role": "...",
    "profile": {}
  }
}
```

### Errors

- 400 validation failure
- 401 token missing/invalid

## 7. Workout Endpoints

## POST /api/workouts/trainer

Creates workout as trainer.

Auth required: Yes
Role required: trainer

### Body

```json
{
  "title": "Upper Body Day",
  "description": "Push and pull focus",
  "exercises": [
    {
      "name": "Push Up",
      "sets": 4,
      "reps": 12,
      "restSec": 60,
      "notes": "Control form"
    }
  ]
}
```

### Validation

- title: required non-empty string
- exercises: required non-empty array
- exercises.\*.name: required
- numeric fields (sets/reps/durationSec/restSec): numeric if provided

### Success 201

Returns created workout object.

### Errors

- 400 validation failure
- 401 token missing/invalid
- 403 forbidden role

## POST /api/workouts/client

Creates workout as client.

Auth required: Yes
Role required: client

Validation and response same as trainer creation.

## POST /api/workouts/:id/assign

Assigns trainer workout to a client.

Auth required: Yes
Role required: trainer

### Path params

- id: required Mongo ObjectId for workout

### Body

```json
{
  "clientId": "<client_user_id>",
  "notes": "Do this plan 3 times this week",
  "startDate": "2026-05-03",
  "endDate": "2026-05-10"
}
```

### Business rules

- Workout must exist.
- Workout must be trainer-created by current trainer.
- clientId must belong to a user with role=client.
- Upsert behavior: assignment is unique for (workout, client).

### Success 200

```json
{
  "message": "Workout assigned successfully",
  "assignment": {
    "_id": "...",
    "workout": {},
    "trainer": {},
    "client": {},
    "notes": "...",
    "startDate": "...",
    "endDate": "...",
    "status": "assigned"
  }
}
```

### Errors

- 400 validation failure or invalid clientId
- 401 token missing/invalid
- 403 assigning workout not created by current trainer
- 404 workout not found

## GET /api/workouts/mine

Gets workouts created by current user.

Auth required: Yes

### Success 200

```json
{
  "workouts": [
    {
      "_id": "...",
      "title": "..."
    }
  ]
}
```

## GET /api/workouts/assigned/me

Gets assignments for current client.

Auth required: Yes
Role required: client

### Success 200

```json
{
  "assignments": [
    {
      "_id": "...",
      "workout": {},
      "trainer": {},
      "status": "assigned"
    }
  ]
}
```

## GET /api/workouts/assigned/by-me

Gets assignments created by current trainer.

Auth required: Yes
Role required: trainer

### Success 200

```json
{
  "assignments": [
    {
      "_id": "...",
      "workout": {},
      "client": {},
      "status": "assigned"
    }
  ]
}
```

## 8. Video Upload and Feedback Endpoints

Video files are stored locally under uploads/videos and are served via /uploads/videos/<fileName>.

## POST /api/videos/upload

Uploads a video for current client.

Auth required: Yes
Role required: client
Content type: multipart/form-data

### Form fields

- video: required file, mime type must start with video/
- title: optional string, 2-120 chars
- description: optional string, max 1000 chars
- exerciseName: optional string, max 100 chars — the name of the exercise this video demonstrates (e.g. "Push Up", "Squat")
- workoutId: optional Mongo ObjectId
- workoutAssignmentId: optional Mongo ObjectId

### Business rules

If workoutId is provided:

- workout must exist
- workout must be either:
  - created by current client, or
  - assigned to current client via WorkoutAssignment

If workoutAssignmentId is provided:

- assignment must exist
- assignment.client must match current client

### Success 201

```json
{
  "message": "Video uploaded successfully",
  "video": {
    "_id": "...",
    "client": "...",
    "workout": "...",
    "workoutAssignment": "...",
    "title": "Squat Form Check",
    "description": "Please review",
    "exerciseName": "Squat",
    "fileName": "1777795738103-squat-test.mp4",
    "originalName": "squat-test.mp4",
    "filePath": "uploads/videos/1777795738103-squat-test.mp4",
    "mimeType": "video/mp4",
    "sizeBytes": 12345,
    "status": "uploaded",
    "uploadedAt": "..."
  },
  "playbackUrl": "/uploads/videos/1777795738103-squat-test.mp4"
}
```

### Errors

- 400 missing file, invalid payload, non-video file, file too large
- 401 token missing/invalid
- 403 forbidden role or invalid ownership/linking rule
- 404 workout or assignment not found

## GET /api/videos/mine

Returns videos uploaded by current client.

Auth required: Yes
Role required: client

### Success 200

```json
{
  "videos": [
    {
      "_id": "...",
      "title": "...",
      "exerciseName": "Push Up",
      "status": "uploaded | reviewed",
      "workout": {
        "_id": "...",
        "title": "..."
      },
      "workoutAssignment": {
        "_id": "...",
        "status": "assigned",
        "startDate": "...",
        "endDate": "..."
      }
    }
  ]
}
```

## GET /api/videos/review

Returns videos for trainer review (assigned clients only).

Auth required: Yes
Role required: trainer

### Query params

- clientId: optional Mongo ObjectId filter

### Access behavior

- Without clientId: returns videos for all clients assigned to this trainer
- With clientId: allowed only if trainer has at least one assignment with that client

### Success 200

```json
{
  "videos": [
    {
      "_id": "...",
      "client": {
        "_id": "...",
        "name": "...",
        "email": "..."
      },
      "title": "...",
      "exerciseName": "Squat",
      "status": "uploaded | reviewed"
    }
  ]
}
```

### Errors

- 400 invalid clientId format
- 401 token missing/invalid
- 403 trainer not allowed for target client

## GET /api/videos/:videoId

Gets a single video.

Auth required: Yes

### Access behavior

- Client can read own video only
- Trainer can read video only if assigned to that client

### Success 200

```json
{
  "video": {
    "_id": "...",
    "client": {
      "_id": "...",
      "name": "...",
      "email": "..."
    },
    "workout": {
      "_id": "...",
      "title": "..."
    },
    "workoutAssignment": {
      "_id": "...",
      "status": "assigned"
    },
    "title": "...",
    "description": "...",
    "filePath": "uploads/videos/...",
    "mimeType": "video/mp4",
    "sizeBytes": 12345,
    "status": "uploaded | reviewed"
  }
}
```

### Errors

- 400 invalid videoId format
- 401 token missing/invalid
- 403 not allowed
- 404 video not found

## GET /api/videos/:videoId/comments

Gets all comments for a video.

Auth required: Yes

### Access behavior

- Client: own video only
- Trainer: assigned client video only

### Success 200

```json
{
  "comments": [
    {
      "_id": "...",
      "video": "...",
      "trainer": {
        "_id": "...",
        "name": "...",
        "email": "...",
        "role": "trainer",
        "profile": {
          "expertise": "..."
        }
      },
      "comment": "Keep chest up and knees out.",
      "createdAt": "..."
    }
  ]
}
```

## POST /api/videos/:videoId/comments

Adds trainer feedback to video (general comment, no timestamp required).

Auth required: Yes
Role required: trainer

### Body

```json
{
  "comment": "Good control. Keep your core tighter during descent."
}
```

### Validation

- comment required
- comment length: 2 to 2000

### Side effect

- Video status is updated to reviewed after adding comment.

### Success 201

```json
{
  "message": "Feedback added successfully",
  "comment": {
    "_id": "...",
    "video": "...",
    "trainer": {
      "_id": "...",
      "name": "...",
      "email": "..."
    },
    "comment": "...",
    "createdAt": "..."
  }
}
```

### Errors

- 400 validation failure or invalid videoId
- 401 token missing/invalid
- 403 not allowed to review this client's video
- 404 video not found

## DELETE /api/videos/:videoId

Deletes current client's own video.

Auth required: Yes
Role required: client

### Behavior

- Deletes video record
- Deletes related VideoComment records
- Deletes local file from disk if exists

### Success 200

```json
{
  "message": "Video deleted successfully"
}
```

### Errors

- 400 invalid videoId
- 401 token missing/invalid
- 403 not owner
- 404 video not found

---

## 8.1 Video Annotation Endpoints

Annotations store a list of **global strokes** on a video. Global means they are not tied to a specific timestamp or frame — they appear overlaid on the entire video. Coordinates are normalized (0.0–1.0) relative to the video canvas, so the frontend should multiply by the actual render dimensions before drawing.

There is one annotation document per video. It is created automatically on the first `POST .../strokes` call.

### GET /api/videos/:videoId/annotations

Fetch all strokes for a video.

Auth required: Yes

#### Access behavior

- Client: own video only
- Trainer: assigned client video only

#### Success 200

```json
{
  "strokes": [
    {
      "strokeId": "e3b0c442-98fc-1c14-9afb-f3c3d48a03b5",
      "type": "freehand",
      "color": "#FF0000",
      "strokeWidth": 2,
      "points": [
        { "x": 0.1, "y": 0.25 },
        { "x": 0.12, "y": 0.28 }
      ],
      "label": null
    }
  ]
}
```

Returns `{ "strokes": [] }` if no annotations exist yet.

#### Errors

- 400 invalid videoId
- 401 token missing/invalid
- 403 not allowed
- 404 video not found

---

### POST /api/videos/:videoId/annotations/strokes

Add a single stroke to the video's annotation layer.

Auth required: Yes
Role required: trainer

The server generates a unique `strokeId` (UUID v4) for each stroke. **Store the returned `strokeId`** to support undo / targeted deletion.

#### Body

```json
{
  "type": "freehand",
  "color": "#FF0000",
  "strokeWidth": 3,
  "points": [
    { "x": 0.1, "y": 0.25 },
    { "x": 0.15, "y": 0.3 },
    { "x": 0.2, "y": 0.28 }
  ],
  "label": null
}
```

For a `text` stroke pass a single point (position) and set `label`:

```json
{
  "type": "text",
  "color": "#FFFF00",
  "strokeWidth": 2,
  "points": [{ "x": 0.5, "y": 0.2 }],
  "label": "Keep knees aligned"
}
```

For `rect` and `circle` pass two points (top-left + bottom-right / center + edge):

```json
{
  "type": "rect",
  "color": "#00FF00",
  "strokeWidth": 2,
  "points": [
    { "x": 0.3, "y": 0.4 },
    { "x": 0.6, "y": 0.7 }
  ]
}
```

#### Validation

| Field         | Rule                                                                   |
| ------------- | ---------------------------------------------------------------------- |
| `type`        | optional; one of `freehand`, `line`, `arrow`, `rect`, `circle`, `text` |
| `color`       | optional; valid hex string `#RGB`, `#RRGGBB`, or `#RRGGBBAA`           |
| `strokeWidth` | optional; number 1–50                                                  |
| `points`      | optional; array of `{x, y}` each 0.0–1.0                               |
| `label`       | optional; string max 500 chars                                         |

#### Success 201

```json
{
  "message": "Stroke added successfully",
  "stroke": {
    "strokeId": "e3b0c442-98fc-1c14-9afb-f3c3d48a03b5",
    "type": "freehand",
    "color": "#FF0000",
    "strokeWidth": 3,
    "points": [{ "x": 0.1, "y": 0.25 }],
    "label": null
  },
  "strokes": [
    /* full updated strokes array */
  ]
}
```

#### Errors

- 400 validation failure or invalid videoId
- 401 token missing/invalid
- 403 not a trainer or client not assigned to you
- 404 video not found

---

### DELETE /api/videos/:videoId/annotations/strokes/:strokeId

Remove a specific stroke by its `strokeId`.

Auth required: Yes
Role required: trainer

#### Path params

- `videoId`: Mongo ObjectId
- `strokeId`: UUID string returned by the POST endpoint

#### Success 200

```json
{
  "message": "Stroke deleted successfully",
  "strokes": [
    /* remaining strokes */
  ]
}
```

#### Errors

- 400 invalid videoId
- 401 token missing/invalid
- 403 client not assigned to you
- 404 video not found or no annotations exist

---

### DELETE /api/videos/:videoId/annotations

Clear all strokes for a video (reset canvas).

Auth required: Yes
Role required: trainer

#### Success 200

```json
{
  "message": "All annotations cleared"
}
```

#### Errors

- 400 invalid videoId
- 401 token missing/invalid
- 403 client not assigned to you
- 404 video not found

---

## 9. Static Video Playback

Video URLs returned as playbackUrl are publicly served through:

- GET /uploads/videos/<fileName>

Current behavior:

- No JWT required at file-serving layer.

Frontend recommendation:

- Treat direct URL sharing as public unless backend is updated to signed/protected media URLs.

## 10. Coach-Client Relationships

All relationship state is stored server-side. The frontend must **not** use SharedPreferences or local storage for request/connection state.

### Relationship lifecycle

```
client sends request  →  status: pending
coach accepts         →  status: active
coach rejects         →  status: rejected
either terminates     →  status: terminated
```

A new request is only allowed when no `pending` or `active` record exists for the same coach+client pair.

---

### POST /api/relationships/request

Client sends a coaching request.

Auth required: Yes
Role required: client

#### Request body

```json
{
  "coachId": "<trainer_user_id>",
  "message": "Hi, I'd like you to coach me." // optional, max 500 chars
}
```

#### Success 201

```json
{
  "message": "Request sent successfully.",
  "relationship": {
    "_id": "...",
    "coach": "<trainer_id>",
    "client": "<client_id>",
    "status": "pending",
    "message": "Hi, I'd like you to coach me.",
    "requestedAt": "..."
  }
}
```

#### Errors

- 400 validation failed (invalid coachId)
- 404 coach not found or target is not a trainer
- 409 pending or active relationship already exists

---

### GET /api/relationships/my-requests

Client: list all requests they have sent (any status).

Auth required: Yes
Role required: client

#### Success 200

```json
{
  "relationships": [
    {
      "_id": "...",
      "coach": { "_id": "...", "name": "...", "email": "...", "profile": {} },
      "status": "pending | active | rejected | terminated",
      "requestedAt": "...",
      "resolvedAt": "..."
    }
  ]
}
```

---

### GET /api/relationships/my-coach

Client: get their currently active coach (if any).

Auth required: Yes
Role required: client

#### Success 200

```json
{
  "relationship": {
    "_id": "...",
    "coach": { "_id": "...", "name": "...", "email": "...", "profile": {} },
    "status": "active",
    "resolvedAt": "..."
  }
}
```

Returns `{ "relationship": null }` if the client has no active coach.

---

### GET /api/relationships/incoming

Trainer: list all pending requests received.

Auth required: Yes
Role required: trainer

#### Success 200

```json
{
  "relationships": [
    {
      "_id": "...",
      "client": { "_id": "...", "name": "...", "email": "...", "profile": {} },
      "status": "pending",
      "message": "...",
      "requestedAt": "..."
    }
  ]
}
```

---

### GET /api/relationships/my-clients

Trainer: list all active clients. **Use this instead of GET /api/users?role=client for the coach's client list.**

Auth required: Yes
Role required: trainer

#### Success 200

```json
{
  "relationships": [
    {
      "_id": "...",
      "client": { "_id": "...", "name": "...", "email": "...", "profile": {} },
      "status": "active",
      "resolvedAt": "..."
    }
  ]
}
```

---

### PATCH /api/relationships/:id/accept

Trainer: accept a pending request.

Auth required: Yes
Role required: trainer

#### Success 200

```json
{ "message": "Request accepted.", "relationship": { "status": "active", ... } }
```

#### Errors

- 404 pending request not found or not owned by this trainer

---

### PATCH /api/relationships/:id/reject

Trainer: reject a pending request.

Auth required: Yes
Role required: trainer

#### Success 200

```json
{ "message": "Request rejected.", "relationship": { "status": "rejected", ... } }
```

---

### PATCH /api/relationships/:id/terminate

Either party: end an active relationship.

Auth required: Yes
Role required: client or trainer

#### Success 200

```json
{ "message": "Relationship terminated.", "relationship": { "status": "terminated", ... } }
```

#### Errors

- 404 active relationship not found or caller is not a party

---

## 10.1 AI-Generated Plans (Gemini)

Trainers can generate personalized **diet** and **workout** plans for their active clients using Google Gemini. Plans are generated from the client's stored profile (age, weight, BMI, bio/goals) plus optional free-text coach notes. All generated plans are saved to the database so both trainers and clients can retrieve them later.

**Requires:** `GEMINI_API_KEY` in `.env`. The trainer must have an active coach-client relationship with the target client.

---

### POST /api/ai-plans/:clientId/diet

Generate a personalized 7-day meal plan for a client.

Auth required: Yes
Role required: trainer

#### Request body

```json
{
  "coachNotes": "Client is vegetarian and has a mild knee injury."
}
```

`coachNotes` is optional (max 1000 chars). If omitted, the plan is built purely from the client's stored profile.

#### Success 201

```json
{
  "message": "Diet plan generated successfully.",
  "plan": {
    "_id": "...",
    "client": "<client_id>",
    "generatedBy": "<trainer_id>",
    "type": "diet",
    "coachNotes": "Client is vegetarian...",
    "clientSnapshot": {
      "name": "Alex",
      "age": 24,
      "weight": 78,
      "bmi": 24.1,
      "bio": "Wants to lose 5kg and build core strength"
    },
    "content": "## Day 1\n### Breakfast\n...",
    "createdAt": "..."
  }
}
```

`content` is a full markdown-formatted 7-day meal plan including macro targets, daily caloric intake, per-meal ingredient lists, calorie counts, and preparation tips.

#### Errors

- 400 invalid clientId or coachNotes too long
- 403 no active relationship with this client
- 404 client not found

---

### POST /api/ai-plans/:clientId/workout

Generate a personalized weekly workout plan for a client.

Auth required: Yes
Role required: trainer

#### Request body

```json
{
  "coachNotes": "Client has bad knees — avoid high-impact exercises."
}
```

#### Success 201

```json
{
  "message": "Workout plan generated successfully.",
  "plan": {
    "_id": "...",
    "type": "workout",
    "content": "## Day 1 — Chest & Triceps\n### Warm-Up\n...",
    "createdAt": "..."
  }
}
```

`content` is a markdown-formatted weekly plan with training split rationale, daily warm-up, main exercises (sets × reps, rest period, coaching cue), cool-down, and a week-over-week progression note.

#### Errors

- 400 invalid clientId or coachNotes too long
- 403 no active relationship with this client
- 404 client not found

---

### GET /api/ai-plans/mine

Client: retrieve all AI-generated plans for themselves.

Auth required: Yes
Role required: client

#### Query params

- `type`: optional — `diet` or `workout` to filter by type

#### Success 200

```json
{
  "plans": [
    {
      "_id": "...",
      "type": "diet | workout",
      "generatedBy": { "_id": "...", "name": "Coach Sam", "email": "..." },
      "coachNotes": "...",
      "content": "...",
      "createdAt": "..."
    }
  ]
}
```

---

### GET /api/ai-plans/:clientId

Trainer or client: retrieve all AI plans for a specific client.

- **Client**: `clientId` must match their own `_id`.
- **Trainer**: must have an active relationship with the client.

Auth required: Yes

#### Query params

- `type`: optional — `diet` or `workout`

#### Success 200

Same shape as `GET /api/ai-plans/mine`.

---

### DELETE /api/ai-plans/:planId

Trainer: delete a plan they generated (e.g. to replace with a newer one).

Auth required: Yes
Role required: trainer

#### Success 200

```json
{ "message": "Plan deleted." }
```

#### Errors

- 404 plan not found or not owned by this trainer

---

## 11. Full Endpoint Catalog

| Method | Path                             | Auth | Role                    |
| ------ | -------------------------------- | ---- | ----------------------- |
| GET    | /health                          | No   | Any                     |
| POST   | /api/auth/signup                 | No   | Any                     |
| POST   | /api/auth/login                  | No   | Any                     |
| GET    | /api/auth/me                     | Yes  | Any                     |
| GET    | /api/users                       | Yes  | Any                     |
| PUT    | /api/users/profile               | Yes  | Any                     |
| POST   | /api/workouts/trainer            | Yes  | Trainer                 |
| POST   | /api/workouts/client             | Yes  | Client                  |
| POST   | /api/workouts/:id/assign         | Yes  | Trainer                 |
| GET    | /api/workouts/mine               | Yes  | Any                     |
| GET    | /api/workouts/assigned/me        | Yes  | Client                  |
| GET    | /api/workouts/assigned/by-me     | Yes  | Trainer                 |
| POST   | /api/videos/upload               | Yes  | Client                  |
| GET    | /api/videos/mine                 | Yes  | Client                  |
| GET    | /api/videos/review               | Yes  | Trainer                 |
| GET    | /api/videos/:videoId             | Yes  | Client/Trainer (scoped) |
| GET    | /api/videos/:videoId/comments    | Yes  | Client/Trainer (scoped) |
| POST   | /api/videos/:videoId/comments    | Yes  | Trainer (scoped)        |
| DELETE | /api/videos/:videoId             | Yes  | Client (owner)          |
| POST   | /api/relationships/request       | Yes  | Client                  |
| GET    | /api/relationships/my-requests   | Yes  | Client                  |
| GET    | /api/relationships/my-coach      | Yes  | Client                  |
| GET    | /api/relationships/incoming      | Yes  | Trainer                 |
| GET    | /api/relationships/my-clients    | Yes  | Trainer                 |
| PATCH  | /api/relationships/:id/accept    | Yes  | Trainer                 |
| PATCH  | /api/relationships/:id/reject    | Yes  | Trainer                 |
| PATCH  | /api/relationships/:id/terminate | Yes  | Client or Trainer       |
| POST   | /api/ai-plans/:clientId/diet     | Yes  | Trainer                 |
| POST   | /api/ai-plans/:clientId/workout  | Yes  | Trainer                 |
| GET    | /api/ai-plans/mine               | Yes  | Client                  |
| GET    | /api/ai-plans/:clientId          | Yes  | Client (own) / Trainer  |
| DELETE | /api/ai-plans/:planId            | Yes  | Trainer (owner)         |

## 12. Frontend Integration Checklist

1. Store JWT after signup/login and attach in Authorization header.
2. Build UI conditionally by role.
3. For client coach-browse flow:
   - GET /api/users?role=trainer — each trainer object includes `relationshipStatus: "none" | "pending" | "active" | "rejected" | "terminated"`
   - Use `relationshipStatus` to enable/disable the "Send Request" button (disable when `pending` or `active`)
   - POST /api/relationships/request to send a request
   - GET /api/relationships/my-coach to display the active coach on the home screen
4. For trainer client-management flow:
   - GET /api/relationships/incoming — pending requests
   - PATCH /api/relationships/:id/accept or /reject
   - GET /api/relationships/my-clients — active clients list (replaces GET /api/users?role=client)
5. For trainer assignment flow:
   - Use client IDs from GET /api/relationships/my-clients
   - POST /api/workouts/trainer
   - POST /api/workouts/:id/assign
6. For client video flow:
   - POST /api/videos/upload (multipart with field name video, include exerciseName)
   - GET /api/videos/mine
   - GET /api/videos/:videoId/comments
7. For trainer review flow:
   - GET /api/videos/review
   - GET /api/videos/:videoId
   - POST /api/videos/:videoId/comments
8. Use playbackUrl for in-app video player source.
9. **Do not store relationship state in SharedPreferences** — always derive status from the relationship endpoints above.
10. For trainer AI plan generation flow:
    - Use client IDs from GET /api/relationships/my-clients
    - POST /api/ai-plans/:clientId/diet — optionally include `coachNotes` for extra context
    - POST /api/ai-plans/:clientId/workout — optionally include `coachNotes`
    - GET /api/ai-plans/:clientId to browse all plans for a client
    - DELETE /api/ai-plans/:planId to remove an outdated plan
11. For client AI plan reading flow:
    - GET /api/ai-plans/mine (optionally ?type=diet or ?type=workout)
    - Render plan.content as markdown in the app
12. For trainer annotation flow:
    - GET /api/videos/:videoId/annotations — load existing strokes on canvas open
    - POST /api/videos/:videoId/annotations/strokes — persist each stroke the trainer draws; store the returned `strokeId` locally to support undo/delete
    - DELETE /api/videos/:videoId/annotations/strokes/:strokeId — remove a specific stroke (undo/erase)
    - DELETE /api/videos/:videoId/annotations — clear the entire canvas
13. For client annotation viewing flow:
    - GET /api/videos/:videoId/annotations — fetch strokes and render them on the video canvas; all strokes are global (visible on every frame)

## 13. Environment Variables

```env
PORT=8000
MONGODB_URI=<mongodb_atlas_url>
JWT_SECRET=<strong_secret>
JWT_EXPIRES_IN=7d
CORS_ORIGIN=*
MAX_VIDEO_SIZE_MB=100
GEMINI_API_KEY=<your_google_ai_studio_key>
```

Notes:

- If PORT is occupied (common on macOS with system services), set another port like 5055.
- MongoDB Atlas connection URL must be placed in MONGODB_URI.
