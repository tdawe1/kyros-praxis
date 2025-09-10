# Testing Guide

## Prereqs
- Python 3.11, Node 20 (for tools).
- Services via docker-compose up.

## Local Testing
- Run: ./run-tests.sh (unit/contract in services/packages, coverage in coverage/).
- Phase 0 (no DB): docker compose up -d orchestrator service-registry, then pytest.
- Phase 1 (with DB): docker compose --profile db up -d, set DATABASE_URL, run pytest.
- Contract: Validates against running services with auth headers.
- Perf: locust -f tests/perf/load_test.py --host=http://localhost:8000 (nightly).

## CI/CD Integration
- .github/workflows/kyros-backend-tests.yml gates PRs on pytest (no DB), coverage >=80%.
- Nightly: Separate job for perf/chaos with DB profile.

## DoD for Tests
- PRs: pytest pass, coverage check, ruff lint.
- Coverage: >=80% core (jobs/events/registration); gaps in DEVIATIONS.md.
- Security: Auth headers in contract tests; @kyros/core schema validation.