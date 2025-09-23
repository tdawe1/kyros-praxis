import importlib

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
    from starlette.routing import WebSocketRoute

    has_ws = any(
        isinstance(route, WebSocketRoute) and getattr(route, "path", None) == "/ws"
        for route in the_app.router.routes
    )
    assert has_ws


def test_secret_key_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    import services.orchestrator.main as main_mod

    importlib.reload(main_mod)
    assert main_mod.SECRET_KEY == "test-secret"
