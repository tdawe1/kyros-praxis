import pytest
from httpx import AsyncClient
from services.orchestrator.main import app
from conftest import async_override_get_db_session


@pytest.mark.asyncio


async def test_create_job_contract(monkeypatch):
    monkeypatch.setattr(
        'services.orchestrator.database',
        'get_db_session',
        async_override_get_db_session
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/jobs",
            json={
                "agent_id": "test",
                "task": "test"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "status" in data


@pytest.mark.asyncio


async def test_list_jobs_contract(monkeypatch):
    monkeypatch.setattr(
        'services.orchestrator.database',
        'get_db_session',
        async_override_get_db_session
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/jobs")
        assert response.status_code == 200
        assert "jobs" in response.json()


@pytest.mark.asyncio


async def test_create_job_invalid_payload(monkeypatch):
    monkeypatch.setattr(
        'services.orchestrator.database',
        'get_db_session',
        async_override_get_db_session
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/jobs",
            json={
                "agent_id": "test",
                "task": "test"
            }
        )
        assert response.status_code == 422


@pytest.mark.asyncio


async def test_create_job_unauthorized(monkeypatch):
    monkeypatch.setattr(
        'services.orchestrator.database',
        'get_db_session',
        async_override_get_db_session
    )
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/jobs",
            json={
                "agent_id": "test",
                "task": "test"
            }
        )
        assert response.status_code == 401
