# ADR: FastAPI Full-Stack Template Integration

## Date
2025-09-13

## Status
In Progress

## Context
Kyros Praxis needs to accelerate development by incorporating proven patterns and utilities from the FastAPI Full-Stack Template while maintaining our existing technology choices and architecture.

## Current Stack (Must Preserve)
- **Frontend**: Next.js (TypeScript, Carbon Design System)
- **Backend**: FastAPI (Python 3.11, SQLAlchemy/Alembic) 
- **Services**: 
  - Console (Next.js at port 3001)
  - Orchestrator (FastAPI at port 8000)
  - Service Registry (FastAPI at port 9000)
  - Terminal Daemon (Node.js 20 with Express/ws/node-pty)
- **Data**: PostgreSQL + Qdrant vector DB
- **Shared**: TypeScript core packages (Zod, Inversify)
- **Auth**: JWT/JWKS
- **Observability**: OpenTelemetry-ready
- **Infrastructure**: Docker, Terraform, GitHub Actions

## Decision
We will selectively integrate the following accelerators from the FastAPI template without replacing our core technology choices:

### What We're Adopting
1. **Docker & Environment Management**
   - Top-level `.env` pattern with `.env.example`
   - Docker Compose healthchecks
   - Optional Adminer for DB debugging (gated)
   - Traefik for production routing
   - Docker Compose watch for development

2. **Backend Platform Utilities**
   - Pydantic Settings for centralized config
   - Health check endpoints
   - Prestart scripts for migrations
   - Optional local password auth (dev only, gated)
   - Seed data initialization (gated)

3. **Frontend Enablement**
   - Auto-generated TypeScript API client
   - CORS configuration alignment

4. **Testing & CI/CD**
   - Pytest scaffolding improvements
   - Playwright E2E patterns (adapted for Next.js)
   - GitHub Actions optimizations

### What We're NOT Adopting
- SQLModel (keeping SQLAlchemy)
- React/Chakra UI (keeping Next.js/Carbon)
- Template's frontend application
- Any authentication that conflicts with our JWKS setup

## Mapping Table

| Template Element | Kyros Location/Plan | Status |
|-----------------|-------------------|---------|
| `docker-compose.yml` | Merge healthchecks into existing | Adapt |
| `docker-compose.traefik.yml` | New file for production | Port |
| `backend/app/core/config.py` | `services/*/app/core/config.py` | Port |
| `backend/app/core/security.py` | Adapt for optional local auth | Adapt |
| `backend/scripts/prestart.sh` | `scripts/prestart.sh` | Port |
| Health check endpoint | `/api/v1/utils/health-check` | Port |
| `.env` pattern | Top-level with example | Port |
| Adminer service | Optional in compose | Port |
| OpenAPI client generation | `packages/api-client/` | Port |
| Pytest structure | Enhance existing tests | Adapt |
| Playwright setup | Adapt for Next.js | Adapt |
| GitHub Actions | Merge optimizations | Adapt |
| SQLModel | N/A | Ignore |
| React frontend | N/A | Ignore |
| Chakra UI | N/A | Ignore |

## Implementation Approach

### Phase 1: Foundation (Docker & Environment)
- Setup unified `.env` management
- Add healthchecks to all services
- Create Traefik overlay for production
- Add optional Adminer service

### Phase 2: Backend Platform
- Implement Pydantic Settings config
- Add health check endpoints
- Create prestart script for migrations
- Optional local password auth (dev only)

### Phase 3: Frontend Integration
- Setup OpenAPI TypeScript client generation
- Wire into Next.js application
- Add demo usage

### Phase 4: Testing & CI
- Enhance pytest structure
- Add Playwright E2E for Next.js
- Optimize GitHub Actions

## Rollback Plan
All changes are additive and gated behind environment flags where appropriate:
- `ENABLE_ADMINER=false` - Controls Adminer service
- `ENABLE_LOCAL_PASSWORD_AUTH=false` - Controls dev password auth
- `ENABLE_SEED=false` - Controls seed data loading

To rollback:
1. Revert to previous branch
2. Remove any new database tables created (if password auth was enabled)
3. Delete generated TypeScript client code
4. Remove new docker-compose overlay files

## Consequences

### Positive
- Faster development with proven patterns
- Better local development experience
- Improved testing infrastructure
- Production-ready routing with Traefik
- Auto-generated TypeScript clients reduce manual work

### Negative
- Increased complexity in configuration
- Need to maintain compatibility between two patterns
- Additional documentation required
- Team needs to learn new patterns

### Neutral
- More environment variables to manage
- Additional Docker services (optional)

## References
- [FastAPI Full-Stack Template](https://github.com/fastapi/full-stack-fastapi-template)
- [Kyros Praxis Repository](https://github.com/tdawe1/kyros-praxis)