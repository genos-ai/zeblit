# Backend Tests

This directory contains all tests for the AI Development Platform backend.

## Structure

```
tests/
├── conftest.py          # Pytest configuration and shared fixtures
├── unit/                # Unit tests for individual components
│   ├── test_auth.py     # Authentication tests
│   ├── test_database.py # Database connection tests
│   └── test_projects.py # Project management tests
├── integration/         # Integration tests for API endpoints
│   └── test_websocket.py # WebSocket functionality tests
└── fixtures/            # Test data and fixtures
```

## Running Tests

### Prerequisites

1. **PostgreSQL** must be running
2. **Redis** must be running
3. **Test database** will be created automatically as `zeblit_test`

### Basic Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/backend --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run specific test file
pytest src/backend/tests/unit/test_auth.py

# Run tests matching pattern
pytest -k "test_login"

# Run with verbose output
pytest -vv
```

### Test Database

Tests use a separate database `zeblit_test` which is automatically:
- Created before each test
- Cleaned after each test
- Uses transactions for isolation

### Test Fixtures

Common fixtures available in `conftest.py`:

- `db_session`: Async database session
- `client`: HTTP test client
- `auth_client`: Authenticated HTTP client
- `test_user`: Regular test user
- `admin_user`: Admin test user
- `test_project`: Sample project
- `test_agents`: All agent types
- `test_factory`: Data factory for creating test objects

### Writing Tests

#### Unit Test Example

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user = User(email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
    
    assert user.id is not None
```

#### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_endpoint(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", ...)
    assert response.status_code == 200
```

### Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.auth` - Authentication-related tests

### Coverage

Generate coverage report:
```bash
pytest --cov=src/backend --cov-report=html
open htmlcov/index.html
```

Target: 80%+ coverage

### Environment Variables

Tests automatically use:
- `ENVIRONMENT=test`
- `DATABASE_URL` with `zeblit_test` database
- `REDIS_URL` with database 1

### Debugging Tests

```bash
# Run with Python debugger
pytest --pdb

# Stop on first failure
pytest -x

# Show local variables
pytest -l

# Show stdout/stderr
pytest -s
``` 