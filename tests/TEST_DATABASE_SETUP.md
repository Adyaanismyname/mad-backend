# Test Database Setup Guide

## Why PostgreSQL for Tests?

The Gym App uses **PostgreSQL-specific features** that are not available in SQLite:

- **ARRAY types** - Used in models like `Exercise.muscle_group`, `CoachProfile.specializations`, etc.
- **Advanced PostgreSQL features** - Better compatibility with production database

Therefore, tests **must** use PostgreSQL, not an in-memory SQLite database.

## Quick Setup

### Step 1: Create Test Database

```powershell
# Connect to PostgreSQL
psql -U postgres

# Create test database
CREATE DATABASE gym_app_test;

# Exit psql
\q
```

### Step 2: Configure Environment

Add to your `.env` file:

```env
# Your main database
DATABASE_URL=postgresql://postgres:password@localhost:5432/gym_app

# Test database (optional - will auto-create from DATABASE_URL if not set)
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/gym_app_test
```

### Step 3: Run Tests

```powershell
pytest
```

The test suite will automatically:
- Create all tables in the test database
- Clean data between tests
- Drop tables after test session

## Detailed Setup Instructions

### For Local PostgreSQL

#### 1. Install PostgreSQL

**Windows:**
```powershell
# Download from https://www.postgresql.org/download/windows/
# Or use chocolatey
choco install postgresql
```

**Mac:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### 2. Create Test Database

```powershell
# Connect as postgres user
psql -U postgres

# In psql:
CREATE DATABASE gym_app_test;

# Grant permissions to your user (if needed)
GRANT ALL PRIVILEGES ON DATABASE gym_app_test TO your_username;

# Exit
\q
```

#### 3. Verify Connection

```powershell
# Test connection to test database
psql -U postgres -d gym_app_test -c "SELECT version();"
```

### For Docker PostgreSQL

If you're using Docker for PostgreSQL:

#### Option 1: Use Existing Docker Container

```powershell
# Connect to your running PostgreSQL container
docker exec -it your_postgres_container psql -U postgres

# Create test database
CREATE DATABASE gym_app_test;
\q
```

#### Option 2: Docker Compose

Add test database service (optional):

```yaml
# docker-compose.yml
services:
  postgres_test:
    image: postgres:15
    environment:
      POSTGRES_DB: gym_app_test
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5433:5432"  # Use different port to avoid conflict
    volumes:
      - postgres_test_data:/var/lib/postgresql/data

volumes:
  postgres_test_data:
```

Then use:
```env
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5433/gym_app_test
```

### For Remote PostgreSQL (Render, AWS RDS, etc.)

#### Create Test Database

```powershell
# Connect to remote PostgreSQL
psql "postgresql://user:password@host:port/postgres"

# Create test database
CREATE DATABASE gym_app_test;
\q
```

#### Set Environment Variable

```env
TEST_DATABASE_URL=postgresql://user:password@host:port/gym_app_test
```

**Warning:** Be careful with remote databases:
- Tests will truncate tables (ensure it's a test-only database)
- Network latency may slow down tests
- Consider using a local PostgreSQL for faster test execution

## Environment Configuration

### Automatic Test Database

The test suite automatically creates a test database name by replacing your main database name with `_test` suffix:

```env
# Only set DATABASE_URL
DATABASE_URL=postgresql://postgres:password@localhost:5432/gym_app

# Tests will automatically use:
# postgresql://postgres:password@localhost:5432/gym_app_test
```

### Explicit Test Database

For more control, set both:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/gym_app
TEST_DATABASE_URL=postgresql://postgres:password@localhost:5432/my_custom_test_db
```

### CI/CD Environment

For GitHub Actions or other CI:

```yaml
# .github/workflows/test.yml
env:
  TEST_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db

services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_DB: test_db
      POSTGRES_PASSWORD: postgres
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

## Test Database Management

### Tables Are Auto-Created

You don't need to run migrations for the test database. The test suite automatically:

1. **Session Start:** Creates all tables using SQLAlchemy models
2. **Each Test:** Truncates all tables for clean state
3. **Session End:** Drops all tables (optional)

### Manual Database Reset

If you need to manually reset the test database:

```powershell
# Drop and recreate test database
psql -U postgres -c "DROP DATABASE IF EXISTS gym_app_test;"
psql -U postgres -c "CREATE DATABASE gym_app_test;"

# Or truncate all tables
pytest --co -q  # This will setup tables
```

### Inspect Test Database

```powershell
# Connect to test database
psql -U postgres -d gym_app_test

# List tables
\dt

# View table structure
\d users
\d workouts

# Query data (after a failed test, before cleanup)
SELECT * FROM users;
```

### Keep Data After Tests (For Debugging)

By default, the test suite drops tables after all tests. To keep data:

1. Edit `tests/conftest.py`:
```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    yield
    # Comment this out to keep data:
    # Base.metadata.drop_all(bind=engine)
```

2. Run tests
3. Inspect database:
```powershell
psql -U postgres -d gym_app_test
```

## Troubleshooting

### Error: "could not connect to server"

**Problem:** PostgreSQL is not running

**Solutions:**
```powershell
# Windows
pg_ctl start

# Mac
brew services start postgresql

# Linux
sudo systemctl start postgresql

# Docker
docker start postgres_container
```

### Error: "database gym_app_test does not exist"

**Problem:** Test database not created

**Solution:**
```powershell
psql -U postgres -c "CREATE DATABASE gym_app_test;"
```

### Error: "TEST_DATABASE_URL must be set"

**Problem:** No database URL configured

**Solution:** Add to `.env`:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/gym_app
```

### Error: "relation [table] does not exist"

**Problem:** Tables not created (rare)

**Solution:**
```powershell
# Re-run with verbose output
pytest -v

# Force table recreation
pytest --setup-show
```

### Error: "permission denied for database"

**Problem:** User doesn't have permissions

**Solution:**
```powershell
psql -U postgres
GRANT ALL PRIVILEGES ON DATABASE gym_app_test TO your_username;
GRANT ALL ON SCHEMA public TO your_username;
\q
```

### Tests Are Slow

**Problem:** Network latency to remote database

**Solutions:**
1. Use local PostgreSQL for testing
2. Use connection pooling (already configured)
3. Run tests in parallel: `pytest -n auto`

### Port Already in Use

**Problem:** PostgreSQL port 5432 is busy

**Solutions:**
```powershell
# Find process using port
netstat -ano | findstr :5432

# Use different port
psql -p 5433

# Update DATABASE_URL
DATABASE_URL=postgresql://postgres:password@localhost:5433/gym_app
```

## Performance Tips

### 1. Use Local PostgreSQL

Local databases are **much faster** than remote:
- Local: ~0.1s per test
- Remote: ~1-2s per test

### 2. Run Tests in Parallel

```powershell
pip install pytest-xdist
pytest -n auto
```

### 3. Run Subset of Tests

```powershell
# Only fast unit tests
pytest -m unit

# Only one file
pytest tests/test_workout_endpoints.py

# Only one test
pytest tests/test_workout_endpoints.py::TestCreateWorkout::test_create_workout_success
```

### 4. Skip Slow Tests (If Any)

```python
@pytest.mark.slow
def test_something_slow():
    pass
```

Then skip:
```powershell
pytest -m "not slow"
```

## Best Practices

### ✅ DO:
- Use a **separate test database** (don't use development database)
- Keep test database **local** for speed
- Run tests before committing code
- Use test markers to run relevant tests quickly

### ❌ DON'T:
- Don't use production database for tests
- Don't use SQLite (won't work with ARRAY types)
- Don't manually create/drop tables (let test suite handle it)
- Don't commit `.env` file with real credentials

## Summary

1. **Create test database:** `CREATE DATABASE gym_app_test;`
2. **Set environment:** Add `DATABASE_URL` to `.env`
3. **Run tests:** `pytest`

That's it! The test suite handles everything else automatically.
