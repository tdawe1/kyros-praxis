import pytest
from fastapi.testclient import TestClient

from services.orchestrator.auth import pwd_context
from services.orchestrator.database import get_db
from services.orchestrator.main import app
from services.orchestrator.models import User


@pytest.fixture
def client(db_session):
    """Create a test client with test database."""
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_append_event_ok(client, db_session):
    # seed user and login
    if not db_session.query(User).filter(User.username == "eventsuser").first():
        user = User(
            username="eventsuser", email="events@example.com", password_hash=pwd_context.hash("password")
        )
        db_session.add(user)
        db_session.commit()

    login = client.post(
        "/auth/login", json={"username": "eventsuser", "password": "password"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    resp = client.post(
        "/api/v1/events",
        json={"event": "test", "target": "x", "details": {"k": "v"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True


def test_events_tail_stream_delivers_backlog(client, db_session):
    # seed user and login
    if not db_session.query(User).filter(User.username == "eventsuser2").first():
        user = User(
            username="eventsuser2", email="events2@example.com", password_hash=pwd_context.hash("password")
        )
        db_session.add(user)
        db_session.commit()

    login = client.post(
        "/auth/login", json={"username": "eventsuser2", "password": "password"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # append one event
    client.post(
        "/api/v1/events",
        json={"event": "stream-test", "target": "y", "details": {"n": 1}},
        headers={"Authorization": f"Bearer {token}"},
    )

    # stream and read first non-comment line
    with client.stream(
        "GET",
        "/api/v1/events/tail?once=1",
        headers={"Authorization": f"Bearer {token}"},
    ) as r:
        assert r.status_code == 200
        found = False
        import json as _json
        for chunk in r.iter_lines():
            if not chunk or not chunk.startswith("data: "):
                continue
            payload = chunk[len("data: "):]
            obj = _json.loads(payload)
            if obj.get("event") in ("test", "stream-test") or obj.get("event_type") in (
                "test",
                "stream-test",
            ):
                found = True
                break
        assert found is True
