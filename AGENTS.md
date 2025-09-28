# Agent Guidelines for Kyros Praxis

## Build/Lint/Test Commands
- **Single Python test**: `pytest services/orchestrator/tests/unit/test_file.py::test_name -v`
- **All Python tests**: `pytest -q` (from repo root)
- **Frontend unit tests**: `cd services/console && npx jest`
- **Frontend E2E tests**: `cd services/console && npx playwright test`
- **Lint Python**: `ruff check` (auto-fix with `ruff check --fix`)
- **Lint Frontend**: `cd services/console && npm run lint`
- **PR gate**: `python3 scripts/pr_gate.py --run-tests`

## Code Style Guidelines
- **Python**: PEP 8, 4-space indent, snake_case modules/functions, PascalCase classes
- **TypeScript/React**: 2-space indent, camelCase variables, PascalCase components
- **Imports**: Absolute imports for modules, relative for local files
- **Types**: Strict TypeScript, Python type hints required
- **Error handling**: Try/catch with specific error types, structured logging
- **Testing**: Test files named `test_*.py` or `*.test.tsx`, colocate with source
