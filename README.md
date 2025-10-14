
# Gym-App Backend

This repository contains the backend for the Gym-App project. This README documents how the API expects requests and responds, the standard response shape, examples, and simple testing steps.

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (via Docker)

## Installation & Setup

### 1. Install Dependencies

Install all required Python packages from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

**Key dependencies for this project:**
- `fastapi` - Modern web framework for building APIs
- `uvicorn` - ASGI server for running FastAPI
- `sqlalchemy` - SQL toolkit and ORM
- `psycopg2-binary` - PostgreSQL adapter
- `alembic` - Database migration tool
- `pydantic` & `pydantic-settings` - Data validation and settings management
- `email-validator` - Email validation for Pydantic
- `python-dotenv` - Environment variable management

### 2. Start PostgreSQL Database (Docker)

Start the PostgreSQL container using Docker Compose:

```bash
# Start the database in detached mode
docker-compose up -d

# View logs
docker-compose logs -f db

# Stop the database
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

The database will be available at:
- Host: `localhost`
- Port: `5432`
- Database: `mydb`
- Username: `admin`
- Password: `admin123`

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg2://admin:admin123@localhost:5432/mydb
```

### 4. Run Database Migrations

```bash
# Create initial migration
python -m alembic revision --autogenerate -m "Initial database schema"

# Apply migrations to database
python -m alembic upgrade head
```

### 5. Start the Backend Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000

# Custom host and port
uvicorn main:app --host 127.0.0.1 --port 8080 --reload
```

The API will be available at:
- API: `http://localhost:8000`

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

All endpoints follow a consistent error handling pattern using try-catch blocks with specific exception handling:

```python
try:
    # Main endpoint logic here
    return {"data": result, "message": "Success message"}
except OperationalError as e:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database connection failed"
    )
except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"An error occurred: {str(e)}"
    )
```

**Error Types:**
- **503 Service Unavailable**: Database connection issues (`OperationalError`)
- **500 Internal Server Error**: Unexpected errors with descriptive message
- **401 Unauthorized**: Invalid or missing authentication token
- **403 Forbidden**: Insufficient privileges (admin endpoints)
- **400 Bad Request**: Invalid request data or validation errors

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

## Depenedency Management with uv

Taken directly from https://docs.astral.sh/uv/guides/projects/#next-steps

uv supports managing Python projects, which define their dependencies in a `pyproject.toml` file.

### Creating a new project

You can create a new Python project using the `uv init` command:

```bash
uv init hello-world

cd hello-world
```

Alternatively, you can initialize a project in the working directory:

```bash
mkdir hello-world

cd hello-world

uv init
```

uv will create the following files:

```
├── .gitignore
├── .python-version
├── README.md
├── main.py
└── pyproject.toml
```

The `README.md` and `main.py` files are optional and can be removed if not needed.

### Project structure

A project consists of a few important parts that work together and allow uv to manage your project. In addition to the files created by `uv init`, uv will create a virtual environment and `uv.lock` file in the root of your project the first time you run a project command, i.e., `uv run`, `uv sync`, or `uv lock`.

A complete listing would look like:

```
.
├── .venv
│   ├── bin
│   ├── lib
│   └── pyvenv.cfg
├── .python-version
├── README.md
├── main.py
├── pyproject.toml
└── uv.lock
```

#### pyproject.toml

The `pyproject.toml` contains metadata about your project:

```toml
[project]
name = "hello-world"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
dependencies = []
```

You'll use this file to specify dependencies, as well as details about the project such as its description or license. You can edit this file manually, or use commands like `uv add` and `uv remove` to manage your project from the terminal.

```
Tip: See the official pyproject.toml guide for more details on getting started with the `pyproject.toml` format.
```
You'll also use this file to specify uv configuration options in a `[tool.uv]` section.

#### .python-version

The `.python-version` file contains the project's default Python version. This file tells uv which Python version to use when creating the project's virtual environment.

#### .venv

The `.venv` folder contains your project's virtual environment, a Python environment that is isolated from the rest of your system. This is where uv will install your project's dependencies.

See the project environment documentation for more details.

#### uv.lock

`uv.lock` is a cross-platform lockfile that contains exact information about your project's dependencies. Unlike the `pyproject.toml` which is used to specify the broad requirements of your project, the lockfile contains the exact resolved versions that are installed in the project environment. This file should be checked into version control, allowing for consistent and reproducible installations across machines.

`uv.lock` is a human-readable TOML file but is managed by uv and should not be edited manually.

See the lockfile documentation for more details.

### Managing dependencies

You can add dependencies to your `pyproject.toml` with the `uv add` command. This will also update the lockfile and project environment:

```bash
uv add requests
```

You can also specify version constraints or alternative sources:

```bash
# Specify a version constraint
uv add 'requests==2.31.0'

# Add a git dependency
uv add git+https://github.com/psf/requests
```

If you're migrating from a `requirements.txt` file, you can use `uv add` with the `-r` flag to add all dependencies from the file:

```bash
# Add all dependencies from `requirements.txt`.
uv add -r requirements.txt -c constraints.txt
```

To remove a package, you can use `uv remove`:

```bash
uv remove requests
```

To upgrade a package, run `uv lock` with the `--upgrade-package` flag:

```bash
uv lock --upgrade-package requests
```

The `--upgrade-package` flag will attempt to update the specified package to the latest compatible version, while keeping the rest of the lockfile intact.

See the documentation on managing dependencies for more details.

### Viewing your version

The `uv version` command can be used to read your package's version.

To get the version of your package, run:

```bash
uv version
```

To get the version without the package name, use the `--short` option:

```bash
uv version --short
```

To get version information in a JSON format, use the `--output-format json` option:

```bash
uv version --output-format json
```

See the publishing guide for details on updating your package version.

### Running commands

`uv run` can be used to run arbitrary scripts or commands in your project environment.

Prior to every `uv run` invocation, uv will verify that the lockfile is up-to-date with the `pyproject.toml`, and that the environment is up-to-date with the lockfile, keeping your project in-sync without the need for manual intervention. `uv run` guarantees that your command is run in a consistent, locked environment.

For example, to use flask:

```bash
uv add flask

uv run -- flask run -p 3000
```

Or, to run a script:

example.py
```python
# Require a project dependency
import flask

print("hello world")
```

```bash
uv run example.py
```

Alternatively, you can use `uv sync` to manually update the environment then activate it before executing a command:

macOS and Linux
```bash
uv sync
```

Windows
```powershell
.venv\Scripts\activate
```

```bash
flask run -p 3000

python example.py
```

Note: The virtual environment must be active to run scripts and commands in the project without `uv run`. Virtual environment activation differs per shell and platform.

See the documentation on running commands and scripts in projects for more details.

### Building distributions

`uv build` can be used to build source distributions and binary distributions (wheel) for your project.

By default, `uv build` will build the project in the current directory, and place the built artifacts in a `dist/` subdirectory:

```bash
uv build

ls dist/
```



See the documentation on building projects for more details.
## License

This project license is not specified in this README. Add a `LICENSE` file if needed.
