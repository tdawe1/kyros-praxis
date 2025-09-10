import pytest
from httpx import AsyncClient

from services.orchestrator.main import app


@pytest.mark.asyncio
async def test_healthz_ok():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_task_and_list():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # create
        payload = {"title": "Test Task", "description": "Test Description"}
        resp = await ac.post("/collab/tasks", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Test Task"
        assert "id" in body and body["id"]
        assert "ETag" in resp.headers

        # list
        list_resp = await ac.get("/collab/state/tasks")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["kind"] == "tasks"
        assert any(item["id"] == body["id"] for item in data["items"]) is True
        assert "ETag" in list_resp.headers

