from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

app = FastAPI(title="Kyros Orchestrator", version="1.0.0")

# Event Sourcing Store (in-memory for initial scaffolding,
# migrate to Postgres later)
events = []


class JobStatus(Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobCreate(BaseModel):
    agent_id: str
    task: str


class Job(BaseModel):
    id: str
    status: JobStatus
    agent_id: str
    task: str
    created_at: datetime


# Dependency Injection example (FastAPI Depends)
def get_current_user():
    # Mock DI - integrate with auth service
    return {"user_id": "system"}


@app.post("/jobs", response_model=dict)
async def create_job(job: JobCreate, current_user=Depends(get_current_user)):
    # Contract validation via Pydantic
    job_instance = Job(
        id="generated_id",
        status=JobStatus.pending,
        agent_id=job.agent_id,
        task=job.task,
        created_at=datetime.utcnow()
    )

    # Event Sourcing: Append event
    event = {
        "type": "job_created",
        "payload": job_instance.dict(),
        "timestamp": datetime.utcnow()
    }
    events.append(event)

    return {"job_id": job_instance.id, "status": "accepted"}


@app.get("/jobs")
async def list_jobs():
    # Return recent events for job list
    return {
        "jobs": [
            e["payload"] for e in events if e["type"] == "job_created"
        ]
    }


@app.post("/events")
async def emit_event(event: dict):
    # Validate event contract (basic)
    if "type" not in event or "payload" not in event:
        raise HTTPException(status_code=400, detail="Invalid event structure")

    events.append(
        {
            "type": event["type"],
            "payload": event["payload"],
            "timestamp": datetime.utcnow()
        }
    )
    return {"status": "emitted"}


@app.get("/events")
async def stream_events():
    # SSE endpoint for event stream (basic implementation)
    return {"status": "sse_stream_started"}


# Health check for service registry
@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": "orchestrator"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
