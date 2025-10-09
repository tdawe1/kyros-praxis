import os
os.environ.setdefault("SECRET_KEY", "test-secret")

import pytest
from fastapi.testclient import TestClient
from services.orchestrator.auth import pwd_context
from services.orchestrator.database import SessionLocal, engine
from services.orchestrator.main import app
from services.orchestrator.models import Base, User


def test_healthz_ok():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_task_and_list():
    client = TestClient(app)
    # ensure tables exist
    Base.metadata.create_all(bind=engine)
    # seed user and login
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "testuser").first():
            user = User(
                username="testuser", email="test@example.com", password_hash=pwd_context.hash("pass123")
            )
            db.add(user)
            db.commit()
    finally:
        db.close()

    login = client.post(
        "/auth/login", json={"username": "testuser", "password": "pass123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # create (auth required)
    payload = {"title": "Test Task", "description": "Test Description"}
    resp = client.post(
        "/api/v1/collab/tasks", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["title"] == "Test Task"
    assert "id" in body and body["id"]
    assert "ETag" in resp.headers

    # list (requires auth)
    list_resp = client.get("/api/v1/collab/state/tasks", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["kind"] == "tasks"
    assert any(item["id"] == body["id"] for item in data["items"]) is True
    assert "ETag" in list_resp.headers


def test_list_conditional_get_returns_304():
    client = TestClient(app)
    # seed user and login
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "conduser").first():
            user = User(username="conduser", email="cond@example.com", password_hash=pwd_context.hash("password"))
            db.add(user)
            db.commit()
    finally:
        db.close()

    login = client.post(
        "/auth/login", json={"username": "conduser", "password": "password"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    # ensure at least one task exists
    payload = {"title": "Cond Task", "description": "For conditional"}
    client.post(
        "/api/v1/collab/tasks", json=payload, headers={"Authorization": f"Bearer {token}"}
    )

    # First list to get ETag
    r1 = client.get("/api/v1/collab/state/tasks", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200
    etag = r1.headers.get("ETag")
    assert etag

    # Conditional GET with same ETag should return 304
    r2 = client.get("/api/v1/collab/state/tasks", headers={"Authorization": f"Bearer {token}", "If-None-Match": etag})
    assert r2.status_code == 304
