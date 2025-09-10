from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import get_db
from models import Base, User
from auth import pwd_context

from auth import authenticate_user

engine = create_engine(
    "sqlite:///./test.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_unauth_create():
    response = client.post(
        "/collab/tasks",
        json={"title": "Test Task", "description": "Test Description", "version": 1}
    )
    assert response.status_code == 401
    assert response.json() == {"type": "unauthorized", "message": "Could not validate credentials"}


def test_login_invalid():
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"type": "unauthorized", "message": "Incorrect email or password"}


def test_login_and_create():
    # First create a user
    db = TestingSessionLocal()
    user = User(email="test@example.com", password_hash=pwd_context.hash("password"))
    db.add(user)
    db.commit()
    db.refresh(user)

    # Login
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password"}
    )
    assert response.status_code == 200
    tokens = response.json()
    access_token = tokens["access_token"]

    # Use token to create task
    response = client.post(
        "/collab/tasks",
        json={"title": "Test Task", "description": "Test Description", "version": 1},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert "id" in response.json()

    # Invalid payload
    response = client.post(
        "/collab/tasks",
        json={"title": "", "description": "Test Description", "version": 1},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert "type" in response.json()