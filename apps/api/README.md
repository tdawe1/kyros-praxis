Kyros Praxis API (Greenfield)

This service provides a clean CrewAI-ready FastAPI surface.

Run locally

- Create a venv and install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Start a Postgres instance: `docker compose up -d db` (from this directory) or point `DATABASE_URL` to an existing Postgres database.
- Run migrations: `alembic upgrade head`
- Start API: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8001`

Key endpoints

- POST `/crews/runs` – Start a crew run from a manifest and input
- GET `/crews/runs/{id}` – Inspect run status/metadata
- POST `/crews/runs/{id}/cancel` – Cancel a running job
- GET `/crews/runs/{id}/events` – Stream Server-Sent Events (SSE)

Configuration

- Providers:
  - OpenRouter (recommended): set `OPENROUTER_API_KEY` and optional `OPENROUTER_BASE_URL` (defaults to `https://openrouter.ai/api/v1`).
    The runner maps these to OpenAI-compatible env vars (`OPENAI_API_KEY`, `OPENAI_BASE_URL`) so CrewAI can use them.
  - OpenAI: set `OPENAI_API_KEY`.
- Model selection: `MODEL_PROVIDER` (default `openrouter`) and `MODEL_NAME` (default `openrouter/openai/gpt-4o-mini`).
- Storage: `KYROS_STORAGE_DIR` path for artifacts (future).
- Manifests: `ai/crews/*.yaml`; prompts: `ai/prompts/*.md`.


Testing

- Ensure a Postgres instance is running (e.g., `docker compose -f docker-compose.yml up -d db`).
- Export `TEST_DATABASE_URL` (or `DATABASE_URL`) pointing to an isolated database, e.g. `postgresql+asyncpg://kyros:kyros@localhost:5432/kyros_test`.
- Apply migrations and run the test suite:
  ```bash
  cd api
  alembic upgrade head
  pytest
  ```
  The fixtures will truncate `crew_runs` and `crew_events` between tests. If `TEST_DATABASE_URL` contains `kyros_test`, the migrations are rolled back to `base` when tests finish.
