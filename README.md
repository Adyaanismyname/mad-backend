
# Gym-App Backend

This repository contains the backend for the Gym-App project. This README documents how the API expects requests and responds, the standard response shape, examples, and simple testing steps.

## API response rules

All API endpoints in this project follow a consistent response format. This makes it easy for clients to parse responses and handle errors uniformly.

- Successful response:

	{
		"data": { /* payload object, may be empty {} */ },
		"message": "A short success message",
	}

- Error response:

	{
		"data": {},
		"message": "A concise error message explaining what went wrong",
	}

Notes:
- `data` must always be present and be an object (use an empty object `{}` when there's no payload).
- `message` should be a short human-readable string describing the result or error.
- HTTP status codes are provided in the response header. The response body intentionally does not include `status` or `code` fields — use the HTTP status code from the header to determine success or failure.

## Request rules

- All request payloads must be valid JSON.
- The main payload object should be provided in the request body. When the server returns a response, the returned `data` key will contain the payload returned by the server.
- For POST/PUT requests, include the body as:

	{
		"data": { /* request payload */ }
	}

- For GET requests, prefer query parameters for filtering and pagination. If your client sends a GET with a body (discouraged), the server may ignore it.
- Content-Type header: `application/json` for requests with bodies.
- Authentication: include authorization headers as required by the endpoint (e.g., `Authorization: Bearer <token>`). See `auth.py` for backend behavior.

## Example request/response flows

- Create a new user (POST /users)

	Request body:

	{
		"data": {
			"username": "jane",
			"email": "jane@example.com",
			"password": "strongpassword"
		}
	}

	Successful response (201):

	{
		"data": {
			"id": 123,
			"username": "jane",
			"email": "jane@example.com"
		},
		"message": "User created successfully"
	}

	Error response (400):

	{
		"data": {},
		"message": "Email already in use"
	}

- Example: Update an entity (PUT /entities/:id)

	Request body:

	{
		"data": {
			"name": "Updated name",
			"value": 42
		}
	}

	Response (200):

	{
		"data": {
			"id": 42,
			"name": "Updated name",
			"value": 42
		},
		"message": "Entity updated"
	}

## Error handling best practices

- Use clear, actionable `message` strings. Avoid internal stack traces or raw exceptions in `message`.
- Put any machine-readable error details inside `data`. For example:

	{
		"data": { "field_errors": { "email": "invalid format" } },
		"message": "Validation failed"
	}

- Use appropriate HTTP status codes: 200/201 for success, 400 for bad requests, 401 for unauthorized, 403 for forbidden, 404 for not found, 422 for validation errors, 500 for server errors.

## Curl examples (quick testing)

- POST with JSON payload

```bash
curl -X POST http://localhost:8000/users \
	-H "Content-Type: application/json" \
	-d '{"data": {"username":"jane","email":"jane@example.com","password":"pw"}}'
```

- GET example

```bash
curl -X GET 'http://localhost:8000/entities?limit=10&page=1'
```

## Database Migrations with Alembic

This project uses Alembic for database schema migrations. Alembic tracks changes to your models and applies them to your database.

### Understanding Alembic Commands

**Step 1: `alembic revision --autogenerate -m "message"`**

Purpose: Create a new migration file based on changes to your SQLAlchemy models.

What happens:
- Alembic compares your current models with the database schema
- It generates a migration script describing the differences
- The script is saved in `alembic/versions/` with a unique revision ID
- Nothing is applied to the database yet

🧠 Think of it as "creating a plan" for database changes.

**Step 2: `alembic upgrade head`**

Purpose: Actually apply all new migrations to your database.

What happens:
- Alembic runs all unapplied migration scripts in order
- It updates your database schema
- It records the last migration ID in the `alembic_version` table

🧠 Think of it as "executing the plan".

### Full Workflow Example

When you change your models (like adding a new column):

```bash
# 1. Create the migration file
python -m alembic revision --autogenerate -m "Added new column to User"

# 2. Apply the migration to the database
python -m alembic upgrade head
```

Alembic will:
1. Create a new migration file describing the change
2. Apply it to your actual Postgres database

### Common Alembic Commands

```bash
# Check current database version
python -m alembic current

# View migration history
python -m alembic history

# Downgrade to previous version
python -m alembic downgrade -1

# Downgrade to specific revision
python -m alembic downgrade <revision_id>
```

## Running and testing locally

- Start the backend (example — adapt to your project's entrypoint):

```bash
python main.py
```

- Then use the curl examples above or Postman/Insomnia to call endpoints.

## Contributing

- Keep responses consistent with the shape described above.
- When adding new endpoints, update this README with the endpoint path, expected `data` fields, and example responses.

## License

This project license is not specified in this README. Add a `LICENSE` file if needed.
