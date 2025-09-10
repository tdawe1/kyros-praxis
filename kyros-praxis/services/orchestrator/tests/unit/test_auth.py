# Test file for auth endpoints
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app  # Import the app to test endpoints

client = TestClient(app)

def test_login_success(monkeypatch):
    # Mock authenticate_user to return a mock user
    mock_user = Mock()
    mock_user.email = "test@example.com"
    monkeypatch.setattr("main.authenticate_user", lambda db, email, password: mock_user)
    
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_failure():
    # Mock authenticate_user to return None for invalid credentials
    monkeypatch.setattr("main.authenticate_user", lambda db, email, password: None)
    
    response = client.post(
        "/auth/login",
        json={"email": "invalid@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["type"] == "unauthorized"
    assert data["message"] == "Incorrect email or password"

@patch("main.get_current_user")
def test_protected_endpoint_success(mock_get_current_user, monkeypatch):
    # Mock get_current_user to return a mock user
    mock_user = Mock()
    mock_user.email = "test@example.com"
    monkeypatch.setattr("main.get_current_user", lambda db, token: mock_user)
    
    # Test a protected endpoint, e.g., list_tasks
    response = client.get(
        "/collab/state/tasks",
        headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == 200  # Assuming the endpoint exists and returns 200 when authenticated

@patch("main.get_current_user")
def test_protected_endpoint_failure(mock_get_current_user, monkeypatch):
    # Mock get_current_user to raise HTTPException for invalid token
    monkeypatch.setattr("main.get_current_user", lambda db, token: raise HTTPException(status_code=401, detail="Invalid token"))
    
    response = client.get(
        "/collab/state/tasks",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["type"] == "unauthorized"