# Testing Guide for Gym App FastAPI Backend

## Test Structure

```
tests/
├── conftest.py                      # Shared fixtures and test configuration
├── test_workout_endpoints.py        # Workout CRUD and exercise management tests
├── test_assignment_endpoints.py     # Workout assignment and client access tests
└── test_feedback_endpoints.py       # Media upload and feedback tests
```

## Setup

### 1. Install Test Dependencies

Required packages:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage
- `pytest-mock` - Mocking utilities
- `httpx` - HTTP client for testing
- `faker` - Test data generation

### 2. Configure Test Database

**Important:** Tests use a **PostgreSQL test database** (not SQLite) because the models use PostgreSQL-specific features like ARRAY types.

#### Option 1: Automatic Test Database (Recommended)

Set your main `DATABASE_URL` in `.env`. The test suite will automatically create a test database by replacing the database name with `_test` suffix:

```env
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/gym_app
# Tests will use: postgresql://user:password@localhost:5432/gym_app_test
```

#### Option 2: Explicit Test Database URL

Set a separate test database URL:

```env
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/gym_app
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/gym_app_test
```

#### Create the Test Database

```powershell
# Connect to PostgreSQL
psql -U your_username -d postgres

# Create test database
CREATE DATABASE gym_app_test;

# Exit
\q
```


### 3. Verify Setup

```powershell
# Run a simple test to verify database connection
pytest tests/test_workout_endpoints.py::TestCreateWorkout::test_create_workout_success -v
```

## Running Tests

### Run All Tests

```powershell
pytest
```

### Run Specific Test File

```powershell
# Test workout endpoints only
pytest tests/test_workout_endpoints.py

# Test assignment endpoints only
pytest tests/test_assignment_endpoints.py

# Test feedback endpoints only
pytest tests/test_feedback_endpoints.py
```

### Run Tests by Marker

```powershell
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only workout-related tests
pytest -m workout

# Run only feedback-related tests
pytest -m feedback

# Run only media upload tests
pytest -m media
```

### Run Specific Test Class

```powershell
# Run specific test class
pytest tests/test_workout_endpoints.py::TestCreateWorkout

# Run specific test method
pytest tests/test_workout_endpoints.py::TestCreateWorkout::test_create_workout_success
```

### Run with Verbose Output

```powershell
pytest -v
```

### Run with Coverage Report

```powershell
# Generate coverage report
pytest --cov

# Generate HTML coverage report
pytest --cov --cov-report=html

# Open coverage report (in browser)
# Navigate to htmlcov/index.html
```

### Run Failed Tests Only

```powershell
# Re-run only failed tests from last run
pytest --lf

# Re-run failed tests first, then all others
pytest --ff
```

### Run Tests in Parallel (Faster)

```powershell
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual endpoint functionality
- Isolated from external dependencies
- Fast execution
- **Count:** ~80 test cases

### Integration Tests (`@pytest.mark.integration`)
- Test complete workflows
- Multiple endpoints working together
- Real database operations
- **Count:** ~5 test cases

### Test by Feature

#### Workout Tests (`@pytest.mark.workout`)
- Create, read, update, delete workouts
- Add/update/remove exercises
- Authorization and permissions
- **Files:** `test_workout_endpoints.py`, `test_assignment_endpoints.py`

#### Feedback Tests (`@pytest.mark.feedback`)
- Media upload operations
- Feedback creation and management
- Hierarchical feedback structure
- Coach-client interactions
- **Files:** `test_feedback_endpoints.py`

#### Media Tests (`@pytest.mark.media`)
- Video/image uploads
- Media access control
- Media deletion
- **Files:** `test_feedback_endpoints.py`

## Test Coverage
### View Coverage Report

```powershell
pytest --cov --cov-report=term-missing
```

This shows which lines are not covered by tests.

## Test Fixtures

### Available Fixtures (from conftest.py)

### Database Fixtures
- `setup_test_database` - Creates tables once per test session (automatic)
- `db_session` - Fresh database session with clean data for each test
- `client` - FastAPI TestClient with DB override

#### User Fixtures
- `coach_user` - Coach role user
- `client_user` - Client role user
- `another_client_user` - Second client for authorization tests
- `another_coach_user` - Second coach for authorization tests

#### Authentication Fixtures
- `coach_token` - JWT token for coach
- `client_token` - JWT token for client
- `auth_headers` - Headers with coach token
- `client_auth_headers` - Headers with client token

#### Relationship Fixtures
- `coach_client_relationship` - Active coach-client relationship

#### Data Fixtures
- `sample_exercise` - Pre-created exercise
- `another_exercise` - Second exercise for multi-exercise tests
- `sample_workout` - Pre-created workout with exercise
- `workout_template` - Workout template
- `assigned_workout` - Pre-created workout assignment
- `sample_media` - Pre-created media upload
- `sample_feedback` - Pre-created feedback

## Writing New Tests

### Test Structure Template

```python
import pytest
from fastapi import status
from uuid import uuid4

@pytest.mark.workout  # Feature marker
@pytest.mark.unit     # Type marker
class TestYourFeature:
    """Test suite description."""
    
    def test_success_case(self, client, auth_headers, sample_workout):
        """Test successful operation."""
        # Arrange
        data = {"field": "value"}
        
        # Act
        response = client.post(
            "/endpoint",
            json=data,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["data"]["field"] == "value"
    
    def test_error_case(self, client, auth_headers):
        """Test error handling."""
        response = client.post(
            "/endpoint",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
```

### Best Practices

1. **Descriptive Names:** Use clear, descriptive test names
   ```python
   # Good
   def test_coach_can_create_workout()
   
   # Bad
   def test_1()
   ```

2. **AAA Pattern:** Arrange, Act, Assert
   ```python
   # Arrange - Set up test data
   workout_data = create_workout_data()
   
   # Act - Perform the action
   response = client.post("/workouts", json=workout_data)
   
   # Assert - Verify results
   assert response.status_code == 201
   ```

3. **Test One Thing:** Each test should verify one behavior
   ```python
   # Good - Tests one authorization rule
   def test_client_cannot_create_workout()
   
   # Bad - Tests multiple things
   def test_workout_operations()
   ```

4. **Use Fixtures:** Leverage shared fixtures
   ```python
   def test_with_fixture(self, client, auth_headers, sample_workout):
       # sample_workout is already created
       response = client.get(f"/workouts/{sample_workout.id}")
   ```

5. **Test Edge Cases:** Include boundary conditions
   ```python
   def test_create_workout_with_zero_duration()
   def test_create_workout_with_max_duration()
   def test_create_workout_with_empty_name()
   ```

## Common Test Scenarios

### Testing Authorization

```python
def test_unauthorized_access(self, client):
    """Test without token."""
    response = client.get("/protected-endpoint")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_forbidden_access(self, client, client_auth_headers):
    """Test wrong role."""
    response = client.post(
        "/coach-only-endpoint",
        headers=client_auth_headers
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
```

### Testing CRUD Operations

```python
def test_create_read_update_delete(self, client, auth_headers):
    # Create
    create_response = client.post("/items", json=data)
    item_id = create_response.json()["data"]["id"]
    
    # Read
    read_response = client.get(f"/items/{item_id}")
    assert read_response.status_code == 200
    
    # Update
    update_response = client.put(f"/items/{item_id}", json=update_data)
    assert update_response.status_code == 200
    
    # Delete
    delete_response = client.delete(f"/items/{item_id}")
    assert delete_response.status_code == 200
```

### Testing Relationships

```python
def test_with_relationship(
    self, client, coach_user, client_user, coach_client_relationship
):
    """Test requires active relationship."""
    # Relationship already exists from fixtures
    response = client.post("/assign-workout", json=data)
    assert response.status_code == 201

def test_without_relationship(
    self, client, coach_user, another_client_user
):
    """Test fails without relationship."""
    # No relationship between these users
    response = client.post("/assign-workout", json=data)
    assert response.status_code == 403
```

## Debugging Failed Tests

### Show Print Statements

```powershell
pytest -s
```

### Show Local Variables on Failure

```powershell
pytest -l
```

### Enter Debugger on Failure

```powershell
pytest --pdb
```

### Stop at First Failure

```powershell
pytest -x
```

### Show Full Diff on Assertion Errors

```powershell
pytest -vv
```


## Performance Testing

```powershell
# Show slowest tests
pytest --durations=10

# Benchmark tests
pip install pytest-benchmark
```

## Test Maintenance

### Update Fixtures

When models change, update fixtures in `conftest.py`:

```python
@pytest.fixture
def new_fixture(db_session):
    """Add new fixture."""
    entity = NewModel(
        field="value"
    )
    db_session.add(entity)
    db_session.commit()
    return entity
```

### Add New Test Markers

Update `pytest.ini`:

```ini
markers =
    new_feature: Tests for new feature
```

## Troubleshooting

### Import Errors

```powershell
# Ensure you're in the project root
cd d:\Codes\gym_app\Gym-App


```


### Async Errors

If async tests fail:
```powershell
uv run install pytest-asyncio
```
