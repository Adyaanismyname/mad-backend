# Fit & Fuel Backend API Documentation

This document is written for frontend integration.
It describes every available endpoint, payload shape, auth requirements, and expected responses.

## 1. Base Information

- Base URL (local): `http://localhost:5000`
- API Prefix: `/api`
- Content-Type: `application/json`
- Auth Type: Bearer JWT

### Auth Header Format

```http
Authorization: Bearer <token>
```

### Health Check

#### GET /health
Used to verify backend is alive.

Success response (200):
```json
{
  "status": "ok",
  "service": "Fit & Fuel API"
}
```

## 2. Data Models (Frontend Reference)

### User
```json
{
  "_id": "6635d58f1ad8c4f2b6e2a101",
  "name": "Trainer One",
  "email": "trainer1@example.com",
  "role": "trainer",
  "profile": {
    "experienceYears": 5,
    "expertise": "Strength and Conditioning",
    "bio": "Certified coach"
  },
  "createdAt": "2026-05-03T10:00:00.000Z",
  "updatedAt": "2026-05-03T10:00:00.000Z"
}
```

Client profile fields:
- `age` (Number)
- `weight` (Number)
- `bmi` (Number)
- `bio` (String, optional)

Trainer profile fields:
- `experienceYears` (Number)
- `expertise` (String)
- `bio` (String, optional)

### Workout
```json
{
  "_id": "6635d7bb1ad8c4f2b6e2a10f",
  "title": "Upper Body Day",
  "description": "Push + pull session",
  "exercises": [
    {
      "name": "Push Up",
      "sets": 4,
      "reps": 12,
      "durationSec": 0,
      "restSec": 60,
      "notes": "Keep core tight"
    }
  ],
  "createdBy": "6635d58f1ad8c4f2b6e2a101",
  "creatorRole": "trainer",
  "createdAt": "2026-05-03T10:05:00.000Z",
  "updatedAt": "2026-05-03T10:05:00.000Z"
}
```

### Workout Assignment
```json
{
  "_id": "6635d8ca1ad8c4f2b6e2a120",
  "workout": "6635d7bb1ad8c4f2b6e2a10f",
  "trainer": "6635d58f1ad8c4f2b6e2a101",
  "client": "6635d60f1ad8c4f2b6e2a104",
  "notes": "Do this 3x this week",
  "startDate": "2026-05-03T00:00:00.000Z",
  "endDate": "2026-05-10T00:00:00.000Z",
  "status": "assigned",
  "createdAt": "2026-05-03T10:10:00.000Z",
  "updatedAt": "2026-05-03T10:10:00.000Z"
}
```

## 3. Authentication Endpoints

## POST /api/auth/signup
Register a new user as trainer or client.

Auth required: No

Request body:
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

Notes:
- `role` must be either `trainer` or `client`.
- If role = `client`, required profile fields: `age`, `weight`, `bmi`.
- If role = `trainer`, required profile fields: `experienceYears`, `expertise`.

Success response (201):
```json
{
  "message": "Signup successful",
  "token": "<jwt_token>",
  "user": {
    "id": "6635d60f1ad8c4f2b6e2a104",
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

Error responses:
- `400` validation failure or missing role-specific profile fields
- `409` email already exists

## POST /api/auth/login
Authenticate existing user.

Auth required: No

Request body:
```json
{
  "email": "client1@example.com",
  "password": "secret123"
}
```

Success response (200):
```json
{
  "message": "Login successful",
  "token": "<jwt_token>",
  "user": {
    "id": "6635d60f1ad8c4f2b6e2a104",
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

Error responses:
- `400` validation failure
- `401` invalid credentials

## GET /api/auth/me
Get current logged-in user.

Auth required: Yes (Bearer token)

Success response (200):
```json
{
  "user": {
    "_id": "6635d60f1ad8c4f2b6e2a104",
    "name": "Client One",
    "email": "client1@example.com",
    "role": "client",
    "profile": {
      "age": 24,
      "weight": 70,
      "bmi": 22.9,
      "bio": "Beginner"
    },
    "createdAt": "2026-05-03T10:00:00.000Z",
    "updatedAt": "2026-05-03T10:00:00.000Z"
  }
}
```

Error responses:
- `401` token missing/invalid

## 4. User Endpoints

## GET /api/users?role=client|trainer
List users by role.
Useful for trainer UI to fetch clients before assigning workouts.

Auth required: Yes

Query params:
- `role` (required): `client` or `trainer`

Success response (200):
```json
{
  "users": [
    {
      "_id": "6635d60f1ad8c4f2b6e2a104",
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
  ]
}
```

Error responses:
- `400` invalid role query
- `401` token missing/invalid

## PUT /api/users/profile
Update own profile fields.

Auth required: Yes

Request body (client example):
```json
{
  "name": "Client One Updated",
  "profile": {
    "age": 25,
    "weight": 68,
    "bmi": 22.1,
    "bio": "Intermediate"
  }
}
```

Request body (trainer example):
```json
{
  "name": "Trainer One Updated",
  "profile": {
    "experienceYears": 6,
    "expertise": "Fat Loss",
    "bio": "ISSA Certified"
  }
}
```

Role behavior:
- Client can update only: `profile.age`, `profile.weight`, `profile.bmi`, `profile.bio`, `name`
- Trainer can update only: `profile.experienceYears`, `profile.expertise`, `profile.bio`, `name`

Success response (200):
```json
{
  "message": "Profile updated successfully",
  "user": {
    "_id": "6635d60f1ad8c4f2b6e2a104",
    "name": "Client One Updated",
    "email": "client1@example.com",
    "role": "client",
    "profile": {
      "age": 25,
      "weight": 68,
      "bmi": 22.1,
      "bio": "Intermediate"
    },
    "createdAt": "2026-05-03T10:00:00.000Z",
    "updatedAt": "2026-05-03T11:00:00.000Z"
  }
}
```

Error responses:
- `400` validation failure
- `401` token missing/invalid

## 5. Workout Endpoints

## POST /api/workouts/trainer
Create workout as trainer.

Auth required: Yes
Role required: `trainer`

Request body:
```json
{
  "title": "Upper Body Day",
  "description": "Push + pull focus",
  "exercises": [
    {
      "name": "Push Up",
      "sets": 4,
      "reps": 12,
      "durationSec": 0,
      "restSec": 60,
      "notes": "Keep core tight"
    },
    {
      "name": "Dumbbell Row",
      "sets": 4,
      "reps": 10,
      "restSec": 90,
      "notes": "Control eccentric"
    }
  ]
}
```

Success response (201):
```json
{
  "message": "Workout created successfully",
  "workout": {
    "_id": "6635d7bb1ad8c4f2b6e2a10f",
    "title": "Upper Body Day",
    "description": "Push + pull focus",
    "exercises": [
      {
        "name": "Push Up",
        "sets": 4,
        "reps": 12,
        "durationSec": 0,
        "restSec": 60,
        "notes": "Keep core tight"
      }
    ],
    "createdBy": "6635d58f1ad8c4f2b6e2a101",
    "creatorRole": "trainer",
    "createdAt": "2026-05-03T10:05:00.000Z",
    "updatedAt": "2026-05-03T10:05:00.000Z"
  }
}
```

Error responses:
- `400` validation failure
- `401` token missing/invalid
- `403` forbidden role

## POST /api/workouts/client
Create workout as client (self-custom workout).

Auth required: Yes
Role required: `client`

Request body: same as trainer workout creation.

Success response: same structure as trainer create workout.

Error responses:
- `400` validation failure
- `401` token missing/invalid
- `403` forbidden role

## POST /api/workouts/:id/assign
Assign trainer-created workout to a client.

Auth required: Yes
Role required: `trainer`

Path params:
- `id`: Workout ID

Request body:
```json
{
  "clientId": "6635d60f1ad8c4f2b6e2a104",
  "notes": "Do this 3x this week",
  "startDate": "2026-05-03",
  "endDate": "2026-05-10"
}
```

Business rules:
- Workout must exist.
- Trainer can assign only workouts created by themselves and where `creatorRole` is `trainer`.
- `clientId` must belong to a user with role `client`.
- Assignment is upserted by (`workout`, `client`) pair.

Success response (200):
```json
{
  "message": "Workout assigned successfully",
  "assignment": {
    "_id": "6635d8ca1ad8c4f2b6e2a120",
    "workout": {
      "_id": "6635d7bb1ad8c4f2b6e2a10f",
      "title": "Upper Body Day",
      "description": "Push + pull focus",
      "exercises": [
        {
          "name": "Push Up",
          "sets": 4,
          "reps": 12,
          "restSec": 60
        }
      ],
      "createdBy": "6635d58f1ad8c4f2b6e2a101",
      "creatorRole": "trainer"
    },
    "trainer": {
      "_id": "6635d58f1ad8c4f2b6e2a101",
      "name": "Trainer One",
      "email": "trainer1@example.com",
      "role": "trainer"
    },
    "client": {
      "_id": "6635d60f1ad8c4f2b6e2a104",
      "name": "Client One",
      "email": "client1@example.com",
      "role": "client"
    },
    "notes": "Do this 3x this week",
    "startDate": "2026-05-03T00:00:00.000Z",
    "endDate": "2026-05-10T00:00:00.000Z",
    "status": "assigned",
    "createdAt": "2026-05-03T10:10:00.000Z",
    "updatedAt": "2026-05-03T10:10:00.000Z"
  }
}
```

Error responses:
- `400` invalid workout id/client id/validation failure
- `401` token missing/invalid
- `403` cannot assign workouts not created by this trainer
- `404` workout not found

## GET /api/workouts/mine
Get workouts created by current user (trainer or client).

Auth required: Yes

Success response (200):
```json
{
  "workouts": [
    {
      "_id": "6635d7bb1ad8c4f2b6e2a10f",
      "title": "Upper Body Day",
      "description": "Push + pull focus",
      "exercises": [
        { "name": "Push Up", "sets": 4, "reps": 12, "restSec": 60 }
      ],
      "createdBy": "6635d58f1ad8c4f2b6e2a101",
      "creatorRole": "trainer",
      "createdAt": "2026-05-03T10:05:00.000Z",
      "updatedAt": "2026-05-03T10:05:00.000Z"
    }
  ]
}
```

Error responses:
- `401` token missing/invalid

## GET /api/workouts/assigned/me
Get workouts assigned to current client.

Auth required: Yes
Role required: `client`

Success response (200):
```json
{
  "assignments": [
    {
      "_id": "6635d8ca1ad8c4f2b6e2a120",
      "workout": {
        "_id": "6635d7bb1ad8c4f2b6e2a10f",
        "title": "Upper Body Day"
      },
      "trainer": {
        "_id": "6635d58f1ad8c4f2b6e2a101",
        "name": "Trainer One",
        "email": "trainer1@example.com",
        "profile": {
          "expertise": "Strength and Conditioning"
        }
      },
      "notes": "Do this 3x this week",
      "startDate": "2026-05-03T00:00:00.000Z",
      "endDate": "2026-05-10T00:00:00.000Z",
      "status": "assigned"
    }
  ]
}
```

Error responses:
- `401` token missing/invalid
- `403` forbidden role

## GET /api/workouts/assigned/by-me
Get assignments created by current trainer.

Auth required: Yes
Role required: `trainer`

Success response (200):
```json
{
  "assignments": [
    {
      "_id": "6635d8ca1ad8c4f2b6e2a120",
      "workout": {
        "_id": "6635d7bb1ad8c4f2b6e2a10f",
        "title": "Upper Body Day"
      },
      "client": {
        "_id": "6635d60f1ad8c4f2b6e2a104",
        "name": "Client One",
        "email": "client1@example.com",
        "profile": {
          "age": 24,
          "weight": 70,
          "bmi": 22.9
        }
      },
      "notes": "Do this 3x this week",
      "startDate": "2026-05-03T00:00:00.000Z",
      "endDate": "2026-05-10T00:00:00.000Z",
      "status": "assigned"
    }
  ]
}
```

Error responses:
- `401` token missing/invalid
- `403` forbidden role

## 6. Common Error Format

Most error responses follow:
```json
{
  "message": "Human readable error message"
}
```

Validation errors often include:
```json
{
  "message": "Validation failed",
  "errors": [
    {
      "type": "field",
      "msg": "title is required",
      "path": "title",
      "location": "body"
    }
  ]
}
```

## 7. Frontend Integration Notes

- Store token after signup/login and attach it in `Authorization` header for protected routes.
- Role-aware UI:
  - If `role = trainer`, show trainer create/assign flows.
  - If `role = client`, show assigned workouts and client custom workout creation.
- For assignment flow:
  1. Call `GET /api/users?role=client` to load dropdown/list of clients.
  2. Create trainer workout with `POST /api/workouts/trainer`.
  3. Assign via `POST /api/workouts/:id/assign`.

## 8. Quick cURL Examples

### Signup (trainer)
```bash
curl -X POST http://localhost:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Trainer One",
    "email": "trainer1@example.com",
    "password": "secret123",
    "role": "trainer",
    "profile": {
      "experienceYears": 5,
      "expertise": "Strength and Conditioning"
    }
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trainer1@example.com",
    "password": "secret123"
  }'
```

### Create trainer workout
```bash
curl -X POST http://localhost:5000/api/workouts/trainer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "title": "Upper Body Day",
    "description": "Push + pull focus",
    "exercises": [
      {"name": "Push Up", "sets": 4, "reps": 12, "restSec": 60}
    ]
  }'
```

### Assign workout
```bash
curl -X POST http://localhost:5000/api/workouts/<workoutId>/assign \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <trainer_token>" \
  -d '{
    "clientId": "<clientId>",
    "notes": "3x this week",
    "startDate": "2026-05-03",
    "endDate": "2026-05-10"
  }'
```

## 9. Environment Variables Reminder

In your `.env` file:

```env
PORT=5000
MONGODB_URI=<your_mongodb_atlas_url>
JWT_SECRET=<strong_secret>
JWT_EXPIRES_IN=7d
CORS_ORIGIN=*
```

MongoDB Atlas URL goes specifically in `MONGODB_URI`.
