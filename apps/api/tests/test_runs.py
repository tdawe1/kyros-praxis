import asyncio
import json

import pytest

import app.main as main
from app import storage
from app.models import RunStatus

@pytest.mark.asyncio
async def test_create_run_succeeds(monkeypatch, api_client, db_cleanup):
    async def fake_run(run_id: str, crew_id: str, payload: dict) -> None:
        await storage.store.update_status(run_id, RunStatus.running)
        await storage.store.add_event(run_id, {"type": "log", "message": "fake run started"})
        await storage.store.update_status(run_id, RunStatus.succeeded, {"tasks": []})

    monkeypatch.setattr(main, "run_crew", fake_run)

    response = await api_client.post(
        "/crews/runs",
        json={"crew_id": "spec_to_tasks", "input": {"prompt": "Build a dashboard"}},
    )
    assert response.status_code == 200
    run_id = response.json()["id"]

    await asyncio.sleep(0)

    status_resp = await api_client.get(f"/crews/runs/{run_id}")
    assert status_resp.status_code == 200
    payload = status_resp.json()
    assert payload["status"] == RunStatus.succeeded.value
    assert payload["result"] == {"tasks": []}

    events_resp = await api_client.get(f"/crews/runs/{run_id}/events")
    data_lines = [line for line in events_resp.text.strip().split("\n") if line.startswith("data: ")]
    messages = [json.loads(line.replace("data: ", "")) for line in data_lines]
    statuses = [m.get("status") for m in messages if "status" in m]
    assert RunStatus.queued.value in statuses
    assert RunStatus.running.value in statuses
    assert RunStatus.succeeded.value in statuses


@pytest.mark.asyncio
async def test_cancel_run(monkeypatch, api_client, db_cleanup):
    async def fake_run(run_id: str, crew_id: str, payload: dict) -> None:
        await storage.store.update_status(run_id, RunStatus.running)

    monkeypatch.setattr(main, "run_crew", fake_run)

    response = await api_client.post(
        "/crews/runs",
        json={"crew_id": "spec_to_tasks", "input": {"prompt": "Build a dashboard"}},
    )
    run_id = response.json()["id"]

    await asyncio.sleep(0)

    cancel_resp = await api_client.post(f"/crews/runs/{run_id}/cancel", json={"reason": "test"})
    assert cancel_resp.status_code == 200

    await asyncio.sleep(0)

    status_resp = await api_client.get(f"/crews/runs/{run_id}")
    payload = status_resp.json()
    assert payload["status"] == RunStatus.canceled.value
