import os
import pytest

from httpx import AsyncClient

os.environ.setdefault("API_KEYS", "ci-key")

from services.orchestrator.main import app
from services.orchestrator.database import SessionLocal
from services.orchestrator.models import User
from services.orchestrator.auth import pwd_context

from services.orchestrator.utils.etag import generate_etag


@pytest.mark.asyncio
async def test_create_job_contract():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # seed user and login
        db = SessionLocal()
        try:
            if not db.query(User).filter(User.email == "jobs@example.com").first():
                user = User(email="jobs@example.com", password_hash=pwd_context.hash("password"))
                db.add(user)
                db.commit()
        finally:
            db.close()
        login = await ac.post("/auth/login", json={"email": "jobs@example.com", "password": "password"})
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = await ac.post(
            "/jobs",
            json={"title": "test"},
            headers={"Authorization": f"Bearer {token}", "X-API-Key": "ci-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "status" in data

        expected_etag = generate_etag(data)
        assert response.headers["ETag"] == expected_etag


@pytest.mark.asyncio
async def test_list_jobs_contract():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # login with same seeded user
        login = await ac.post("/auth/login", json={"email": "jobs@example.com", "password": "password"})
        assert login.status_code == 200
        token = login.json()["access_token"]

        response = await ac.get(
            "/jobs",
            headers={"Authorization": f"Bearer {token}", "X-API-Key": "ci-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data

        expected_etag = generate_etag(data["jobs"])
        assert response.headers["ETag"] == expected_etag
