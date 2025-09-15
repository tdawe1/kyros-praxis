# Testing Guide

This guide covers testing strategies and commands for the Kyros Praxis multi-service architecture.

## Quick Start

### Backend (Orchestrator) Tests
```bash
# Run all orchestrator tests with in-memory SQLite
cd services/orchestrator && pytest -q

# Run with verbose output
cd services/orchestrator && pytest -v

# Run specific test categories
cd services/orchestrator && pytest tests/unit/        # Unit tests only
cd services/orchestrator && pytest tests/contract/     # Contract/API tests only
```

### Frontend (Console) Tests
```bash
# Run console app tests
cd services/console && npm test

# Run with coverage
cd services/console && npm run test:coverage

# Run specific test files
cd services/console && npm test -- auth.test.ts
```

### Package Testing (Opt-in)

The following packages require manual setup and are excluded from default test runs:

#### Service Registry Package
```bash
# Set up Python path and install dependencies
export PYTHONPATH="${PYTHONPATH}:$(pwd)/packages/service-registry"
cd packages/service-registry
pip install -e ".[dev]"

# Run tests
pytest
```

#### Zen MCP Server
```bash
# Install external dependencies first
# See packages/zen-mcp-server/README.md for requirements

export PYTHONPATH="${PYTHONPATH}:$(pwd)/packages/zen-mcp-server"
cd packages/zen-mcp-server
pip install -e ".[dev]"

# Run tests (requires external services)
pytest -m "not integration"  # Skip integration tests by default
```

## Test Architecture

### Backend Test Structure
```
services/orchestrator/tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests with mocked dependencies
│   ├── test_auth.py        # Authentication logic
│   ├── test_events.py      # Event handling
│   ├── test_models.py      # Database models
│   ├── test_repo.py        # Repository pattern
│   └── test_endpoints.py   # API endpoints
├── contract/               # Integration/contract tests
│   └── test_jobs.py        # Job API contracts
└── test_security.py        # Security-focused tests
```

### Key Test Features

#### Database Isolation
- Each test function gets a fresh in-memory SQLite database
- No shared state between tests
- Automatic cleanup after each test
- SQLAlchemy fixtures that mock `.scalars().all()` and `.first()` patterns

#### Mock Objects
Realistic SQLAlchemy mock objects:
```python
class MockResult:
    def __init__(self, data=None):
        self._data = data or []

    def scalars(self):
        return MockScalars(self._data)

    def first(self):
        return self._data[0] if self._data else None
```

#### Deterministic Tests
- No global environment variable overrides in test files
- Each test sets up its own dependencies
- Consistent test data seeding
- No reliance on test execution order

## Testing Utilities

### Running Individual Tests
```bash
# Single test file
cd services/orchestrator && pytest tests/unit/test_auth.py

# Single test function
cd services/orchestrator && pytest tests/unit/test_auth.py::test_login_invalid

# Tests with specific markers
cd services/orchestrator && pytest -m "unit"
cd services/orchestrator && pytest -m "contract"
```

### Debugging Tests
```bash
# Stop on first failure
cd services/orchestrator && pytest -x

# Run with verbose output and show print statements
cd services/orchestrator && pytest -v -s

# Drop into debugger on failure
cd services/orchestrator && pytest --pdb
```

### Coverage Reports
```bash
# Backend coverage
cd services/orchestrator && pytest --cov=. --cov-report=html

# Frontend coverage
cd services/console && npm run test:coverage
```

## Optional Smoke Tests

### Terminal Daemon WebSocket Test
```bash
# Skip by default if server not running
cd services/terminal-daemon && npm run test:smoke

# Manual WebSocket connectivity test
node tests/smoke/websocket-connectivity.test.js
```

This test will:
1. Check if the terminal daemon is running on port 8787
2. Attempt a WebSocket connection
3. Verify basic authentication handshake
4. Skip gracefully if service is unavailable

## Test Data Management

### Seeding Test Data
Tests use deterministic data seeding:
```python
def test_with_user_data(client, test_db):
    # Create user only if it doesn't exist
    if not test_db.query(User).filter(User.email == "test@example.com").first():
        user = User(email="test@example.com", password_hash=pwd_context.hash("password"))
        test_db.add(user)
        test_db.commit()
```

### Cleaning Up
- Database fixtures automatically clean up after each test
- No manual cleanup required in test functions
- Each test runs in isolation

## Continuous Integration

### Pre-commit Hooks
```bash
# Run all tests before committing
./scripts/test-all.sh

# Quick validation (unit tests only)
./scripts/test-quick.sh
```

### PR Gate Validation
```bash
# Run PR gate checks
python3 scripts/pr_gate.py --run-tests

# This will run:
# 1. Backend orchestrator tests
# 2. Frontend console tests
# 3. Linting and type checking
# 4. Security scanning
```

## Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Ensure proper Python path setup
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install dependencies
cd services/orchestrator && pip install -r requirements.txt
```

**Database Connection Issues:**
```bash
# Clean up any lingering test databases
rm -f services/orchestrator/*.db

# Ensure SQLite is available
sqlite3 --version
```

**WebSocket Test Failures:**
```bash
# Start terminal daemon first
cd services/terminal-daemon && npm run dev

# Run smoke test in another terminal
npm run test:smoke
```

### Environment Variables for Testing
Tests set their own environment variables. Avoid setting global ones that might interfere:

```bash
# These are automatically set by tests
export SECRET_KEY="test-secret-key-for-testing"
export DATABASE_URL="sqlite:///:memory:"
```

## Best Practices

1. **Isolate Tests:** Each test should be independent and not rely on other tests
2. **Use Mocks:** Mock external dependencies like databases, APIs, and services
3. **Clean Up:** Always clean up resources after tests (handled automatically by fixtures)
4. **Be Deterministic:** Tests should produce the same result every time
5. **Test Error Cases:** Test both success and failure scenarios
6. **Use Descriptive Names:** Test names should clearly indicate what they're testing

## Adding New Tests

1. **Unit Tests:** Place in `tests/unit/` with mocked dependencies
2. **Integration Tests:** Place in `tests/contract/` with real dependencies
3. **Security Tests:** Add to `test_security.py` or create new security-focused files
4. **Package Tests:** Add to respective package directories with setup instructions

For more information on specific testing patterns, see the individual service README files.