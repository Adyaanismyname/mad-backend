# Quick Test Setup 
## PostgreSQL Test Database Required

This project uses **PostgreSQL-specific features** (ARRAY types) that are **not available in SQLite**.

Tests **will fail** if you try to use SQLite!

## Quick Setup (2 Minutes)

### Step 1: Create Test Database
```powershell
psql -U postgres
CREATE DATABASE gym_app_test;
\q
```

### Step 2: Set Environment Variable
Add to `.env`:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/gym_app
```

### Step 3: Run Tests

## Common Commands

```powershell
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific tests
uv run pytest -m workout          # Only workout tests
uv run pytest -m feedback         # Only feedback tests
uv run pytest -m unit             # Only unit tests

# Run one file
uv run pytest tests/test_workout_endpoints.py

# Interactive menu
.\run_tests.ps1
```

## Test Database is Separate

- **Development DB:** `gym_app`
- **Test DB:** `gym_app_test` (auto-cleaned)

