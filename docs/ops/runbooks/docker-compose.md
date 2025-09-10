# Docker Compose Profiles and Orchestration

## Profiles
- `db`: Starts Postgres for DB operations (default).
  - Command: `docker compose up --profile db`
- `perf`: Starts Redis for performance/load testing.
  - Command: `docker compose up --profile perf`
- `all`: Starts full stack (Console, Orchestrator, Service-Registry, DB, Redis).
  - Command: `docker compose up --profile all`

## Root Scripts
- Build all: `bin/build-all.sh` (sequential: core, terminal-daemon, console).
- Test all: `bin/test-all.sh` (pytest backends, npm test frontends/core).

## Health Checks
- `/readyz` endpoints on Orchestrator (localhost:8000/readyz) and Service-Registry (localhost:8002/readyz).
  - Returns 200 if DB/Redis healthy, 503 otherwise.
  - Use: `curl http://localhost:8000/readyz`