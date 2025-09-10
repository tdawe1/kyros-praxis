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

## Database Handling: Sync vs Async

### Current Implementation

The orchestrator service currently uses a split approach for database interactions with SQLAlchemy:

- **Synchronous Sessions (Primary Usage)**: Most endpoints and operations rely on synchronous `SessionLocal` from SQLAlchemy. This stems from the legacy FastAPI full-stack template, which defaults to sync sessions for simplicity. Sync sessions perform well for straightforward CRUD operations and avoid the overhead of async context switching in low-concurrency scenarios. For example, in `database.py`, the `get_db` dependency yields a sync `Session` bound to the engine created from `DATABASE_URL`.

  Example sync usage in an endpoint (e.g., in `routers/jobs.py`):

  ```python
  from sqlalchemy.orm import Session
  from .database import get_db

  @router.post("/jobs")
  def create_job(job: JobCreate, db: Session = Depends(get_db)):
      # Sync operations: db.add(), db.commit(), etc.
      new_job = Job(**job.dict())
      db.add(new_job)
      db.commit()
      db.refresh(new_job)
      return new_job
  ```

- **Async Sessions (Specific Cases)**: Async `AsyncSession` is used selectively, such as in CI/testing environments to align with async-capable `DATABASE_URL` (e.g., PostgreSQL async drivers). This ensures tests can run without blocking in async pytest fixtures. The `get_async_db_session` function in `database.py` provides this for async contexts.

This hybrid setup balances immediate development speed with future scalability but introduces minor inconsistencies in session management.

### Consistent Testing Steps

To ensure reliable and consistent testing across sync and async contexts, always use the async session in `conftest.py` for fixtures. This overrides the default sync behavior during tests, preventing connection pool mismatches.

1. **Update conftest.py**: Ensure the `override_get_db` fixture uses `get_async_db_session` for test isolation.

   ```python
   import pytest
   from sqlalchemy.ext.asyncio import AsyncSession
   from httpx import AsyncClient
   from main import app
   from database import get_async_db_session  # Async session provider

   @pytest.fixture
   def override_get_db():
       async def _get_db():
           async with get_async_db_session() as session:
               yield session
       app.dependency_overrides[get_db] = _get_db  # Override sync dep with async
       yield
       app.dependency_overrides.clear()

   @pytest.fixture
   async def async_client(override_get_db):
       async with AsyncClient(app=app, base_url="http://test") as client:
           yield client
   ```

2. **Run Tests**: Use `pytest` with async support (e.g., `pytest -v --asyncio-mode=auto`). For negative paths (e.g., 422 validation errors in `test_jobs.py`):

   ```bash
   cd services/orchestrator
   pytest tests/contract/test_jobs.py -v  # Covers 422/401 cases with >80% coverage
   ```

3. **Verify Coverage**: Run `pytest --cov=services/orchestrator --cov-report=html` to confirm async consistency; aim for >80% coverage on DB interactions.

This approach ensures tests mimic production async potential without altering runtime behavior.

### Future Recommendations

For scalability under high load (e.g., concurrent job processing), migrate fully to asynchronous database operations:

- **Adopt AsyncSession Everywhere**: Replace `SessionLocal` with `AsyncSession` in all endpoints. Use `async_engine = create_async_engine(DATABASE_URL)` and `async_sessionmaker(bind=async_engine)`.

  Example async endpoint refactor:

  ```python
  from sqlalchemy.ext.asyncio import AsyncSession
  from fastapi import Depends

  async def get_async_db() -> AsyncSession:
      async with async_session() as session:
          yield session

  @router.post("/jobs")
  async def create_job(job: JobCreate, db: AsyncSession = Depends(get_async_db)):
      new_job = Job(**job.dict())
      db.add(new_job)
      await db.commit()
      await db.refresh(new_job)
      return new_job
  ```

- **Benefits**: Enables non-blocking I/O, better concurrency with FastAPI's async workers, and alignment with modern async drivers (e.g., asyncpg for PostgreSQL).
- **Migration Steps**:
  1. Install `asyncpg` or equivalent async driver.
  2. Update `database.py` to default to async engine/session.
  3. Refactor routers to `async def` and use `await` on DB ops.
  4. Update tests to use async fixtures (as above).
  5. Document in an ADR (e.g., docs/adr/000X-async-db-migration.md) and test thoroughly for performance gains.

This full async migration is recommended post-MVP to handle agentic workflows efficiently, without immediate disruption to sync-heavy paths.
