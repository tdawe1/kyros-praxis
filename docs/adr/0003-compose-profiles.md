# 0003: Add Docker Compose Profiles

Status: Proposed

## Context
Current docker-compose.yml starts all services by default, lacking flexibility for development (e.g., DB only) or performance testing (Redis optional).

## Decision
Add profiles to docker-compose.yml:
- `db`: Postgres (default for DB ops)
- `perf`: Redis (optional for load tools)
- `all`: Full stack (Console, Orchestrator, Service-Registry + DB + Redis)

Postgres is default; Redis optional. This aligns with stack (FastAPI/React/Vite/TS, Postgres/Redis) without deviations.

## Consequences
- Enables `docker compose up --profile db` for quick DB starts
- Reduces startup time for non-full-stack workflows
- Maintains backward compatibility (no profile = all services)
- No impact on collab invariants (ETags, events)