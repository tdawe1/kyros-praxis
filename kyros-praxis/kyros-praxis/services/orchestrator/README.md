# Kyros Orchestrator Service

## API Specs
- OpenAPI/Swagger: http://localhost:8000/docs (auto-generated).
- Key Endpoints:
  - POST /jobs: Create job, returns 200 {job_id, status:'accepted'}. Body: {"agent_id": str, "task": str}. Auth: Bearer JWT.
  - GET /jobs: List jobs, returns 200 {jobs: [...]}. Auth: Bearer.
  - POST /events: Emit event, returns 200 {status: "emitted"}. Body: {"type": str, "payload": dict}. Auth: Bearer.
  - GET /events: Placeholder, returns 200 {status: "sse_stream_started"}. Auth: Bearer.
  - GET /health: Returns 200 {status: "healthy", "services": "orchestrator"}. No auth.

## Setup and Run Instructions
- Prerequisites: Python 3.11, pip install -r requirements.txt.
- Copy .env.example to .env, set SECRET_KEY=strong_random_key (generate with python -c "import secrets; print(secrets.token_urlsafe(32))"), ALLOWED_ORIGINS=http://localhost:3000.
- Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000.
- Test: curl -X POST http://localhost:8000/jobs -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSJ9.signature" -d '{"agent_id":"test","task":"test"}' (expect 200 {job_id: "generated_id", status: "accepted"}).

## Error Handling Guide
- 401 Unauthorized: Invalid/missing token - Ensure HS256 decode succeeds with SECRET_KEY.
- 400 Bad Request: Pydantic fail on JobCreate - Validate against model.
- 500 Internal: Event append error - Check logs for details, add retry in client.
- Logs: Middleware logs requests; future structured with events.

## Migration Notes
- Current: In-memory events (non-durable). Phase 1: SQLAlchemy to Postgres; add models.py with Base = declarative_base(), Job model, create_engine from DATABASE_URL.
- When DB added: Run python -m alembic upgrade head (install alembic).
- Backup: API export for events; future pg_dump.