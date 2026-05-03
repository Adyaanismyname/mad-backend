# Fit & Fuel Backend (Express + MongoDB Atlas)

Backend API for Fit & Fuel with:

- Role-based authentication (trainer/client)
- Profile creation and updates
- Workout creation by trainers and clients
- Trainer-to-client workout assignment
- Client view of assigned workouts

Full frontend-facing API docs: `API_DOCUMENTATION.md`

## 1. Setup

```bash
npm install
cp .env.example .env
```

## 2. MongoDB Atlas URL (where to put it)

Put your Atlas connection string in `.env`:

```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/<dbName>?retryWrites=true&w=majority
```

This is the **exact place** to add your URL.

## 3. Run

```bash
npm run dev
```

or

```bash
npm start
```

Server starts at `http://localhost:5000` by default.

Uploaded videos are stored locally in `uploads/videos` and served from `/uploads/...` URLs.

## 4. API Endpoints

### Auth

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me` (Bearer token required)

Signup body example (client):

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

Signup body example (trainer):

```json
{
  "name": "Trainer One",
  "email": "trainer1@example.com",
  "password": "secret123",
  "role": "trainer",
  "profile": {
    "experienceYears": 5,
    "expertise": "Strength and Conditioning",
    "bio": "Certified Coach"
  }
}
```

### Users

- `GET /api/users?role=client|trainer` (Bearer token required)
- `PUT /api/users/profile` (Bearer token required)

### Workouts

- `POST /api/workouts/trainer` (trainer only)
- `POST /api/workouts/client` (client only)
- `POST /api/workouts/:id/assign` (trainer only)
- `GET /api/workouts/mine` (trainer or client)
- `GET /api/workouts/assigned/me` (client only)
- `GET /api/workouts/assigned/by-me` (trainer only)

### Videos

- `POST /api/videos/upload` (client only, multipart form-data with `video` file)
- `GET /api/videos/mine` (client only)
- `GET /api/videos/review` (trainer only, optional `clientId` query)
- `GET /api/videos/:videoId` (owner client or assigned trainer)
- `GET /api/videos/:videoId/comments` (owner client or assigned trainer)
- `POST /api/videos/:videoId/comments` (trainer only)
- `DELETE /api/videos/:videoId` (client owner only)

Video upload size is controlled by `MAX_VIDEO_SIZE_MB` in `.env` (default 100 MB).

Create workout body example:

```json
{
  "title": "Upper Body Day",
  "description": "Push and pull focus",
  "exercises": [
    { "name": "Push Up", "sets": 4, "reps": 12, "restSec": 60 },
    { "name": "Dumbbell Row", "sets": 4, "reps": 10, "restSec": 90 }
  ]
}
```

Assign workout body example:

```json
{
  "clientId": "<client_user_id>",
  "notes": "Do this plan 3 times this week",
  "startDate": "2026-05-03",
  "endDate": "2026-05-10"
}
```

## 5. Notes for your larger app roadmap

This backend already covers your requested features for authentication, roles, profiles, workout management, and video upload/feedback. For the full Fit & Fuel scope, you can extend it next with:

- Advanced video annotations (timestamp markers and overlay drawings)
- Progress logs (weight, body measurements over time)
- AI diet/workout suggestion endpoints
