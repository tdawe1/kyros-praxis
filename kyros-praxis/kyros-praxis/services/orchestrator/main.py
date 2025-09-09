import os
import logging
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from jose import JWTError, jwt
from passlib.context import CryptContext

app = FastAPI(title="Kyros Orchestrator", version="1.0.0")

# CORS
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Basic request id logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("orchestrator")

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    req_id = request.headers.get("x-request-id") or os.urandom(8).hex()
    response = await call_next(request)
    response.headers["x-request-id"] = req_id
    logger.info({"event": "http_request", "id": req_id, "path": request.url.path})
    return response

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

SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"user_id": user_id}


@app.post("/jobs", response_model=dict)
async def create_job(
    job: JobCreate, current_user: dict = Depends(get_current_user)
):
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
async def list_jobs(current_user: dict = Depends(get_current_user)):
    # Return recent events for job list
    return {
        "jobs": [
            e["payload"] for e in events if e["type"] == "job_created"
        ]
    }


@app.post("/events")
async def emit_event(event: dict, current_user: dict = Depends(get_current_user)):
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
