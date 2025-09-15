import pytest
import os
from fastapi.testclient import TestClient
from services.orchestrator.auth import pwd_context
from services.orchestrator.database import get_db
from services.orchestrator.main import app
from services.orchestrator.models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


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


def test_unauth_create(client):
    response = client.post(
        "/api/v1/collab/tasks",
        json={"title": "Test Task", "description": "Test Description"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "http_exception"
    assert data["error"]["code"] == 401
    assert "Could not validate credentials" in data["error"]["message"]


def test_login_invalid(client):
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": "wrong"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "http_exception"
    assert data["error"]["code"] == 401
    assert "Incorrect username or password" in data["error"]["message"]


def test_login_and_create(client, test_db):
    # First create a user
    # Delete any existing user with the same username to avoid IntegrityError
    existing_user = test_db.query(User).filter(User.username == "testuser").first()
    if existing_user:
        test_db.delete(existing_user)
        test_db.commit()

    user = User(username="testuser", email="test@example.com", password_hash=pwd_context.hash("password"))
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Login
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": "password"}
    )
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens["access_token"]

    # Use token to create task
    response = client.post(
        "/api/v1/collab/tasks",
        json={"title": "Test Task", "description": "Test Description"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201
    assert "id" in response.json()

    # Invalid payload
    response = client.post(
        "/api/v1/collab/tasks",
        json={"title": "", "description": "Test Description"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 422
