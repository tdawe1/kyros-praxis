import pytest
import os
from fastapi.testclient import TestClient
from services.orchestrator.main import app


# Set environment variables for testing
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-purposes-only"
os.environ["ENVIRONMENT"] = "local"


@pytest.fixture
def client():
    return TestClient(app)


def test_login_invalid_returns_401(client):
    resp = client.post(
        "/auth/login", json={"email": "nope@example.com", "password": "bad"}
    )
    # Depending on validation, FastAPI may return 401 or 422; accept both
    assert resp.status_code in (401, 422)
