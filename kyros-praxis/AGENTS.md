# Repository Guidelines

## Project Structure & Module Organization
- Monorepo core lives in `kyros-praxis/`; `services/` and `packages/` are symlinked to it for convenience.
- Backend: `kyros-praxis/services/orchestrator` (FastAPI, Alembic, pytest).
- Frontend: `kyros-praxis/services/console` (Next.js 14, Jest/Testing Library, Playwright).
- Shared: `scripts/` (CI/gates), `docs/` (plans/docs), `tests/ci/` (repo checks), `packages/` (e.g., `service-registry`).

## Build, Test, and Development Commands
- Setup deps/envs: `bash scripts/setup.sh`.
- Run stack (DB, Redis, services): `docker-compose up -d`.
- Backend dev: `cd services/orchestrator && source .venv/bin/activate && uvicorn main:app --reload`.
- Frontend dev: `cd services/console && npm run dev`.
- Python tests: `pytest -q` (from repo root or service dir).
- Frontend tests: `cd services/console && npx jest` (unit) and `npx playwright test` (e2e).
- PR gate (plan-sync, tests, diff size): `python3 scripts/pr_gate.py --run-tests` or `bash scripts/check.sh`.

## Coding Style & Naming Conventions
- `.editorconfig`: LF, final newline, 2-space indent (Python uses 4), tabs in `Makefile`.
- Python: prefer PEP 8; lint/format with Ruff (see `kyros-praxis/.pre-commit-config.yaml`). Optional: `pre-commit install` then commit.
- JS/TS (console): run `npm run lint`. Components in `PascalCase.tsx`; files/vars in `camelCase`; tests in `__tests__/`.
- Python naming: modules `snake_case.py`; tests `test_*.py` under `services/orchestrator/tests`.

## Testing Guidelines
- Add/update tests with any code change (PR gate enforces DoD).
- Python: write unit tests near code or under `services/orchestrator/tests`; run `pytest -q`.
- Frontend: colocate tests in `__tests__/` and use Testing Library; snapshot only for stable UI.
- E2E: `npx playwright test` from `services/console` for critical flows.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat(scope): ...`, `fix(scope): ...`, `docs: ...`, `chore: ...` (see `git log`).
- Keep changes focused; link issues (e.g., `#123`).
- PRs must include: clear description (what/why), linked issues, screenshots for UI, test notes, and docs updates (e.g., `docs/PLAN.md`).
- Before pushing: run `python3 scripts/pr_gate.py --run-tests`. If intentionally skipping plan-sync, use `--skip-plan-sync` and explain in the PR.

## Security & Configuration Tips
- Do not commit secrets. Copy `.env.example` to `.env` in each service.
- Local defaults: Postgres/Redis via `docker-compose.yml`. Key vars: `SECRET_KEY`, `DB_*`, `REDIS_*`.

## OpenCode Terminal Interface (NEW)
- **Terminal-First Development**: Use `opencode` command in this directory for AI agent interaction
- **File References**: Use `@filename` to include file content in conversations
- **Shell Commands**: Use `!command` to run shell commands and include output
- **Available Commands**: `/models`, `/sessions`, `/init`, `/help` for managing agent workflows
- **MCP Integration**: kyros-mcp and zen-mcp servers provide agent coordination tools
- **Configuration**: See `opencode.json` for provider and MCP server settings

