from pydantic import BaseModel
from fastapi import FastAPI, Response

app = FastAPI()


class TaskCreate(BaseModel):
    title: str
    description: str = ""

@app.post("/collab/tasks")
async def create_task(task: TaskCreate):
    # Stub implementation
    task_id = "stub-task-1"
    response = {"id": task_id}
    response.headers["ETag"] = f"task-etag-{task_id}"
    return response


@app.get("/collab/state/{kind}")
async def get_state(kind: str):
    data = {"kind": kind, "state": "initial state"}
    response = Response(content=str(data), media_type="application/json")
    response.headers["ETag"] = "initial-etag"
    return response