import pytest
from fastapi.testclient import TestClient
from services.orchestrator.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_websocket_endpoint():
    from services.orchestrator.main import app as the_app
    from services.orchestrator.main import websocket_endpoint

    # Check if the websocket endpoint is registered in the app routes
    websocket_routes = [route for route in the_app.routes if route.path == "/ws"]
    assert len(websocket_routes) == 1
    assert websocket_routes[0].endpoint == websocket_endpoint
