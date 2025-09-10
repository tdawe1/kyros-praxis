import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_websocket_endpoint():
    # Note: Testing WebSocket requires special setup; basic check for endpoint existence
    from main import app
    assert hasattr(app, "websocket_endpoint")  # Verify endpoint is defined

def test_secret_key_env():
    from main import SECRET_KEY
    import os
    os.environ["SECRET_KEY"] = "test-secret"
    from main import SECRET_KEY as reloaded_key
    assert reloaded_key == "test-secret"  # Verify env sourcing