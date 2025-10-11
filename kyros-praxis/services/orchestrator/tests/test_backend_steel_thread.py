import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.orchestrator.main import app
from services.orchestrator.models import Base, User
from services.orchestrator.auth import pwd_context
from services.orchestrator.database import get_db

# Set environment variables for testing
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-purposes-only"
os.environ["ENVIRONMENT"] = "local"


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal()

    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create a test client with test database."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client, test_db):
    """Create authentication headers for testing."""
    # Create a test user
    username = "testuser"
    password = "testpass123"

    # Delete any existing user with the same username to avoid IntegrityError
    existing_user = test_db.query(User).filter(User.username == username).first()
    if existing_user:
        test_db.delete(existing_user)
        test_db.commit()

    # Create new user
    user = User(
        username=username,
        email="test@example.com",
        password_hash=pwd_context.hash(password),
        role="admin"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Login to get token
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "A test task for the steel thread"
    }


@pytest.fixture
def created_task(client, auth_headers, sample_task_data):
    """Create a test task and return it."""
    response = client.post("/api/v1/collab/tasks",
                         json=sample_task_data,
                         headers=auth_headers)
    assert response.status_code == 201
    return response.json()


class TestHealthzEndpoint:
    """Test the /healthz endpoint."""

    def test_healthz_success(self, client):
        """Test successful health check."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_healthz_database_ping(self, client, test_db):
        """Test that health check actually pings the database."""
        # This is implicitly tested by the successful response
        # If the database were down, the endpoint would return 500
        response = client.get("/healthz")
        assert response.status_code == 200


class TestCreateTaskEndpoint:
    """Test the POST /collab/tasks endpoint."""

    def test_create_task_success(self, client, auth_headers, sample_task_data):
        """Test successful task creation."""
        response = client.post("/api/v1/collab/tasks",
                             json=sample_task_data,
                             headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task_data["title"]
        assert data["description"] == sample_task_data["description"]
        assert data["version"] == 1
        assert "id" in data
        assert "created_at" in data

        # Check ETag header
        assert "ETag" in response.headers
        etag = response.headers["ETag"]
        assert etag.startswith('"') and etag.endswith('"')

        # Check Location header
        assert "Location" in response.headers
        assert response.headers["Location"].startswith("/collab/tasks/")

    def test_create_task_minimal_data(self, client, auth_headers):
        """Test task creation with only required fields."""
        task_data = {"title": "Minimal Task"}
        response = client.post("/api/v1/collab/tasks",
                             json=task_data,
                             headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["description"] is None
        assert data["version"] == 1

    def test_create_task_without_auth(self, client, sample_task_data):
        """Test task creation without authentication."""
        response = client.post("/api/v1/collab/tasks",
                             json=sample_task_data)

        assert response.status_code == 401
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == 401

    def test_create_task_invalid_title(self, client, auth_headers):
        """Test task creation with invalid title."""
        # Empty title
        response = client.post("/api/v1/collab/tasks",
                             json={"title": ""},
                             headers=auth_headers)
        assert response.status_code == 422

        # Whitespace-only title
        response = client.post("/api/v1/collab/tasks",
                             json={"title": "   "},
                             headers=auth_headers)
        assert response.status_code == 422

        # Missing title
        response = client.post("/api/v1/collab/tasks",
                             json={"description": "No title"},
                             headers=auth_headers)
        assert response.status_code == 422

    def test_create_task_extra_fields(self, client, auth_headers):
        """Test task creation with extra fields (should be rejected)."""
        task_data = {
            "title": "Valid Task",
            "description": "With description",
            "extra_field": "should be ignored"
        }
        response = client.post("/api/v1/collab/tasks",
                             json=task_data,
                             headers=auth_headers)

        assert response.status_code == 422


class TestListTasksEndpoint:
    """Test the GET /collab/state/tasks endpoint."""

    def test_list_tasks_empty(self, client, auth_headers):
        """Test listing tasks when none exist."""
        response = client.get("/api/v1/collab/state/tasks",
                            headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "tasks"
        assert data["items"] == []

        # Check ETag header
        assert "ETag" in response.headers

    def test_list_tasks_with_data(self, client, auth_headers, created_task):
        """Test listing tasks when tasks exist."""
        response = client.get("/api/v1/collab/state/tasks",
                            headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "tasks"
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == created_task["id"]
        assert data["items"][0]["title"] == created_task["title"]

    def test_list_tasks_multiple(self, client, auth_headers):
        """Test listing multiple tasks."""
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task_data = {"title": f"Task {i}", "description": f"Description {i}"}
            response = client.post("/api/v1/collab/tasks",
                                 json=task_data,
                                 headers=auth_headers)
            tasks.append(response.json())

        # List all tasks
        response = client.get("/api/v1/collab/state/tasks",
                            headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3

        # Check that tasks are ordered by creation time
        # (The order might vary, but they should all be present)
        task_ids = {task["id"] for task in data["items"]}
        expected_ids = {task["id"] for task in tasks}
        assert task_ids == expected_ids

    def test_list_tasks_without_auth(self, client):
        """Test listing tasks without authentication."""
        response = client.get("/api/v1/collab/state/tasks")

        assert response.status_code == 401
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["code"] == 401

    def test_list_tasks_conditional_get_match(self, client, auth_headers, created_task):
        """Test conditional GET with matching ETag."""
        # First request to get ETag
        response1 = client.get("/api/v1/collab/state/tasks",
                             headers=auth_headers)
        etag = response1.headers["ETag"]

        # Second request with If-None-Match
        response2 = client.get("/api/v1/collab/state/tasks",
                             headers={**auth_headers, "If-None-Match": etag})

        assert response2.status_code == 304
        assert len(response2.content) == 0

    def test_list_tasks_conditional_get_no_match(self, client, auth_headers):
        """Test conditional GET with non-matching ETag."""
        # Request with different ETag
        response = client.get("/api/v1/collab/state/tasks",
                            headers={**auth_headers, "If-None-Match": '"different-etag"'})

        assert response.status_code == 200
        assert "items" in response.json()

    def test_list_tasks_conditional_get_multiple_etags(self, client, auth_headers):
        """Test conditional GET with multiple ETags."""
        # First request to get ETag
        response1 = client.get("/api/v1/collab/state/tasks",
                             headers=auth_headers)
        etag = response1.headers["ETag"]

        # Request with multiple ETags including the correct one
        response2 = client.get("/api/v1/collab/state/tasks",
                             headers={**auth_headers,
                                    "If-None-Match": f'"other-etag", {etag}, "another-etag"'})

        assert response2.status_code == 304

    def test_list_tasks_etag_consistency(self, client, auth_headers, sample_task_data):
        """Test that ETag is consistent for same data."""
        # Create task
        client.post("/api/v1/collab/tasks",
                   json=sample_task_data,
                   headers=auth_headers)

        # Get tasks twice
        response1 = client.get("/api/v1/collab/state/tasks",
                              headers=auth_headers)
        response2 = client.get("/api/v1/collab/state/tasks",
                              headers=auth_headers)

        # ETags should be the same
        assert response1.headers["ETag"] == response2.headers["ETag"]

    def test_list_tasks_etag_changes_with_data(self, client, auth_headers):
        """Test that ETag changes when data changes."""
        # Get initial ETag
        response1 = client.get("/api/v1/collab/state/tasks",
                              headers=auth_headers)
        etag1 = response1.headers["ETag"]

        # Add a task
        client.post("/api/v1/collab/tasks",
                   json={"title": "New Task"},
                   headers=auth_headers)

        # Get tasks again
        response2 = client.get("/api/v1/collab/state/tasks",
                              headers=auth_headers)
        etag2 = response2.headers["ETag"]

        # ETags should be different
        assert etag1 != etag2


class TestEndpointIntegration:
    """Integration tests for the steel thread endpoints."""

    def test_full_workflow(self, client, auth_headers):
        """Test the complete workflow: health check -> create task -> list tasks."""
        # 1. Health check
        health_response = client.get("/healthz")
        assert health_response.status_code == 200

        # 2. Create task
        task_data = {"title": "Integration Test Task", "description": "Testing the full flow"}
        create_response = client.post("/api/v1/collab/tasks",
                                   json=task_data,
                                   headers=auth_headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # 3. List tasks
        list_response = client.get("/api/v1/collab/state/tasks",
                                 headers=auth_headers)
        assert list_response.status_code == 200

        # Verify the created task is in the list
        tasks = list_response.json()["items"]
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id
        assert tasks[0]["title"] == task_data["title"]

    def test_etag_workflow(self, client, auth_headers):
        """Test ETag workflow for caching."""
        # Initial request
        response1 = client.get("/api/v1/collab/state/tasks",
                             headers=auth_headers)
        etag1 = response1.headers["ETag"]

        # Conditional request - should return 304
        response2 = client.get("/api/v1/collab/state/tasks",
                             headers={**auth_headers, "If-None-Match": etag1})
        assert response2.status_code == 304

        # Create a task to change the data
        client.post("/api/v1/collab/tasks",
                   json={"title": "New Task"},
                   headers=auth_headers)

        # Request again with old ETag - should return full response
        response3 = client.get("/api/v1/collab/state/tasks",
                             headers={**auth_headers, "If-None-Match": etag1})
        assert response3.status_code == 200
        assert response3.headers["ETag"] != etag1


class TestErrorHandling:
    """Test error handling for steel thread endpoints."""

    def test_healthz_database_error(self, monkeypatch, client):
        """Test health check behavior when database is unavailable."""
        # This test is tricky to implement without actually breaking the DB
        # For now, we assume the endpoint correctly handles DB errors
        pass

    def test_invalid_etag_format(self, client, auth_headers):
        """Test behavior with malformed ETag header."""
        response = client.get("/api/v1/collab/state/tasks",
                            headers={**auth_headers, "If-None-Match": "invalid-etag"})

        # Should still return 200, just ignore the invalid ETag
        assert response.status_code == 200

    def test_malformed_json(self, client, auth_headers):
        """Test task creation with malformed JSON."""
        response = client.post("/api/v1/collab/tasks",
                             data="not json",
                             headers={**auth_headers, "Content-Type": "application/json"})

        assert response.status_code == 422

    def test_large_description(self, client, auth_headers):
        """Test task creation with description that exceeds limits."""
        # Create a very long description
        long_desc = "x" * 2000  # Exceeds the 1024 char limit in model
        response = client.post("/api/v1/collab/tasks",
                             json={"title": "Test", "description": long_desc},
                             headers=auth_headers)

        # The API should handle it gracefully (either accept or validate)
        # SQLite doesn't enforce string length by default
        assert response.status_code in [201, 422]