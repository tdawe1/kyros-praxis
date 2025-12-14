# Repository Guidelines

## Project Structure & Module Organization
Kyros Praxis is a polyglot monorepo with **two backend architectures**:

### Current Architecture (CrewAI-Ready)
- **New Console**: `apps/console` - Next.js 14 app for CrewAI run management
- **CrewAI API**: `apps/api` - FastAPI service with CrewAI integration (port 8001)
- **Database**: PostgreSQL for crew runs and events

### Legacy Architecture (Being Phased Out)
- **Legacy Console**: `services/console` (symlinked to `kyros-praxis/services/console`)
- **Legacy Orchestrator**: `kyros-praxis/services/orchestrator` - Traditional job/task API (port 8000)
- **Terminal Daemon**: `kyros-praxis/services/terminal-daemon` - WebSocket terminal service
- **Service Registry**: `kyros-praxis/packages/service-registry` - Shared backend utilities

**Migration Status**: The new CrewAI API is functional and recommended for new development. The legacy orchestrator remains active for backward compatibility. Automation scripts live in `bin/` and `scripts/`, while CI assertions are under `tests/ci`. Keep the living plans (`frontend-current-plan.md`, `backend-current-plan.md`) updated alongside code changes.

## Build, Test, and Development Commands

### CrewAI Stack (Recommended)
- **Console**: `npm install && npm run dev --prefix apps/console` — start the console on http://localhost:3000
- **API**: `cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001` — serve CrewAI API on port 8001
- **Database**: `cd apps/api && docker compose up -d db` — start PostgreSQL for crew runs
- **Migrations**: `cd apps/api && alembic upgrade head` — apply database schema
- **Tests**: `cd apps/api && pytest` — run API test suite

### Legacy Stack (Maintenance Mode)
- **Legacy Console**: `npm install && npm run dev --prefix services/console` — old console on http://localhost:3000
- **Orchestrator**: `cd kyros-praxis/services/orchestrator && uvicorn main:app --reload --port 8000` — legacy API; requires `.env` with `SECRET_KEY`, `ALLOWED_ORIGINS`
- **Terminal Daemon**: `npm install && npm run dev --prefix kyros-praxis/services/terminal-daemon`
- **Builds**: `npm run build --prefix services/console` and `npm run build --prefix kyros-praxis/services/terminal-daemon`
- **All Tests**: `bin/test-all.sh` — orchestrates cross-service test runs

## Coding Style & Naming Conventions
Python modules use 4-space indents, snake_case functions, and PascalCase Pydantic models; place new routers, schemas, and database helpers under `kyros-praxis/services/orchestrator/app`. TypeScript and React files rely on 2-space indents, ES modules, and PascalCase components, with hooks kept in `src/lib` and OpenAPI-derived types in `contracts/`. Run `npm run lint --prefix services/console` before submitting UI work, and ensure `tsc` passes for Node services. Keep environment-specific constants in `.env` not inline literals.

## Testing Guidelines
Run `pytest -c kyros-praxis/services/orchestrator/pytest.ini -q` for backend coverage; align fixtures with the layout in `kyros-praxis/services/orchestrator/tests`. Service Registry tests live under `kyros-praxis/packages/service-registry/tests`. Frontend Testing Library specs belong in `services/console/__tests__`; execute targeted suites with `npx jest` from that directory until the `npm test` alias is restored. The terminal daemon bundles `tests/smoke.test.js` for connectivity—start the daemon, then call `node tests/smoke.test.js` to verify WebSocket health. Document gaps when introducing new modules.

## Commit & Pull Request Guidelines
Follow Conventional Commit prefixes (`feat`, `fix`, `chore`, etc.) as modeled in `kyros-praxis/COMMIT-MESSAGE.md`—for example, `feat(orchestrator): add job lease expiry checks`. Keep commits focused and include schema or contract updates in the same change. Pull requests should summarize behavior, list verification commands, link any plan updates, and attach screenshots for console UI tweaks. Note configuration or secret handling changes explicitly.

## Configuration & Security Tips
Copy `.env.example` files before local runs and never commit real secrets. Rotate `SECRET_KEY` values per the guidance in `services/orchestrator/README.md`, and prefer Docker Compose files for shared environments. Perform dependency hygiene (`npm audit`, `pip list --outdated`) during maintenance windows. Logs under `logs/` can include sensitive payloads—scrub them before sharing outside the team.
