import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from fastapi.testclient import TestClient
client = TestClient(app)


def test_healthz_ok():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_create_task_and_list():
    # Test creating a task
    task_data = {"title": "Test Task", "description": "Test Description"}
    response = client.post("/collab/tasks", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test Task"
    assert "version" in data
    assert "ETag" in response.headers

    # Test listing tasks
    list_response = client.get("/collab/state/tasks")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert "kind" in list_data
    assert list_data["kind"] == "tasks"
    assert "items" in list_data
    assert len(list_data["items"]) > 0
    assert "version" in list_data["items"][0]
    assert "ETag" in list_response.headers

    # Verify the created task is in the list
    created_id = data["id"]
    found = any(task["id"] == created_id for task in list_data["items"])
    assert found