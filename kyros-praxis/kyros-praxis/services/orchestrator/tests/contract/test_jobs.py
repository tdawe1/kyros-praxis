import pytest

from httpx import AsyncClient

from services.orchestrator.main import app


@pytest.mark.asyncio
async def test_create_job_contract():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/jobs",
            json={"agent_id": "test", "task": "test"},
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSJ9.signature"}  # Dummy token
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "accepted"


@pytest.mark.asyncio
async def test_list_jobs_contract():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            "/jobs",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSJ9.signature"}
        )
        assert response.status_code == 200
        assert "jobs" in response.json()