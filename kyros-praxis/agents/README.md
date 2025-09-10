# Read the external @/../.kilocode/rules/README.md file (not accessible within the workspace) and all the files in .kilocode/rules (including subdirectories) to fully understand the project goals and workflow. For local access, refer to the provided rules in custom_instructions or copy relevant files to docs/rules/ if needed.

---

## 1) Product Overview

**Kyros Dashboard** is an AI‑powered content repurposing & scheduling platform for SMEs. It ingests a source (URL, transcript, file, or pasted text) and generates channel‑specific variants (LinkedIn, X/Twitter, newsletter, blog). Users can edit, accept, export, and schedule posts. A jobs system tracks request → generation → review → export.

**Primary goals of the rebuild**

* Clean architecture, testability, and strong CI/CD from day one.
* Keep feature scope similar to the current app, but with clearer boundaries and lower coupling.
* Ship a high‑signal developer experience (DX): fast local dev, one‑command test suite, reliable E2E.

---

## 2) Non‑functional Requirements (must‑have)

* **Security:** JWT auth, RBAC, rate limits, input validation, HTML sanitization, secrets via env. No secrets committed.
* **Reliability:** Idempotent job processing, retries with backoff, circuit‑breakers for external APIs, graceful shutdown.
* **Observability:** Structured logs, metrics, traces; Sentry hooks; health/readiness endpoints.
* **Performance:** Async I/O on backend, cache common reads, queue long‑running tasks.
* **Maintainability:** Clear module boundaries, high cohesion, low coupling; ADRs for major decisions.
* **Test coverage:** Unit + integration + E2E. Deterministic seeds and mocks. Visual sanity optional.

---

## 0) For Agents (Kilocode)

This section is a compact contract for autonomous agents.

- **Objective:** Implement backlog tasks while keeping the repo green and idempotent.
- **Owned paths:**
  - Backend: `services/orchestrator/**`
  - Frontend: `services/console/**` (generated API and job form)
  - Tests/Docs/Collab: `services/**/tests/**`, `docs/**`, `collaboration/**`
- **Allowed actions:** Edit files in owned paths; run specified commands; create migrations; update tests/docs.
- **Forbidden:** Commit secrets; touch files outside owned paths; run destructive DB ops without migration; push network calls beyond localhost and whitelisted services.
- **Stop conditions:** `pytest` red, migration conflicts, schema drift vs models, auth failures.
- **Success gates:**
  - Backend unit/contract tests ≥ 80% coverage: `pytest services/orchestrator/tests/unit -v --cov=services/orchestrator`
  - Alembic at head with useful indexes applied; upgrade/downgrade clean
  - API smoke healthy: `GET /health` → 200; `POST /jobs` accepts `{name}` and returns 201 + Location
- **Escalate:** Append to `collaboration/logs/log.md` and add an event to `collaboration/events/events.jsonl` when blocked.

### Deterministic Entrypoints

| Purpose | Command | Expectation |
|---|---|---|
| Bootstrap BE | `cd services/orchestrator && pip install -r requirements.txt` | Deps installed |
| Collect tests | `pytest --collect-only` | No ImportError |
| Generate migration | `alembic revision --autogenerate -m "<msg>"` | New version file |
| Apply migration | `alembic upgrade head` | Head applied |
| Run unit tests | `pytest services/orchestrator/tests/unit -v` | All green |
| FE codegen | `npm --prefix services/console run codegen` | Types updated |
| FE tests | `npm --prefix services/console test -w` | Green |

### Owned Areas Map

- Backend Orchestrator: models/migrations, routers, repositories, pytest.
- Frontend Console: generated API, job form, error states.
- QA/Docs: tests, coverage gates, READMEs, ADRs.

### Checkpoints & Git

- Repo root: `kyros-praxis/` (project .git inside).
- Branch naming: `agents/<task-id>-<slug>` (e.g., `agents/T-101-jobs-form`).
- PRs must reference a task ID and link to created GitHub issues when enabled.

## 3) Target Architecture

### Monorepo structure

```
kyros/
├─ frontend/                # React 18 + Vite + TS + Tailwind + TanStack Query
├─ backend/                 # FastAPI + SQLAlchemy + Alembic + Celery + Redis
├─ integrations/            # External integrations (GitHub linking scripts, webhooks)
├─ collaboration/           # Agent collaboration state/events scaffolding
├─ scripts/                 # Dev and CI helpers (bash + python)
├─ docs/                    # Architecture, ADRs, runbooks, deployment
├─ .github/workflows/       # CI pipelines (see CI section)
└─ docker/                  # Dockerfiles + docker-compose for local dev
```

### Frontend (requirements)

* **Stack:** React 18, TypeScript, Vite (dev on port **3001**), Tailwind, React Router, TanStack Query.
* **UI:** Modern dashboard (dark‑first), layout with sidebar/topbar, responsive.
* **Core pages:** Dashboard (KPIs), Studio (generation workspace), Jobs (monitor/history), Scheduler, Settings (presets, tokens), Auth (login/register).
* **API access:** `.env` support for `VITE_API_BASE_URL` (default `http://localhost:8000`).
* **Testing:** Vitest + RTL for units; Playwright for E2E. Use `data-testid` selectors.

### Backend (requirements)

* **Stack:** FastAPI (Python 3.12), SQLAlchemy 2.x, Alembic, Pydantic, Celery, Redis, PostgreSQL.
* **Auth:** JWT (access/refresh), password hashing (Passlib/argon2/bcrypt), RBAC roles: `user`, `admin`.
* **Core domains:** Users, Presets, Jobs, Variants, Scheduler (cron/rrule), Tools registry, Quotas/Rate limiting, Audit events.
* **Background jobs:** Celery workers for generation/export/scheduling.
* **Validation & security:** Input schemas, optional HTML sanitization (e.g., bleach) with graceful fallback.
* **Docs:** OpenAPI at `/docs` with tagged endpoints.

### Data model (minimum viable)

* **User**(id, email unique, password\_hash, role, created\_at)
* **Preset**(id, owner\_id, name, channels\[], tone, params json, created\_at)
* **Job**(id, owner\_id, source\_type, source\_payload json, status \[queued|running|needs\_review|done|failed], cost\_estimate, created\_at, updated\_at)
* **Variant**(id, job\_id, channel, content, accepted bool, created\_at)
* **Schedule**(id, owner\_id, variant\_id, run\_at ts, recurrence rrule/null, status)
* **Tool**(id, key unique, config json, enabled bool)
* **AuditEvent**(id, actor\_id, kind, payload json, ts)

Provide SQLAlchemy models + Alembic migrations.

### API surface (initial)

* `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
* `GET /me`
* `GET/POST/PUT/DELETE /presets`
* `POST /jobs` (start generation), `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/retry`
* `GET/PUT /variants/{id}` (accept/edit)
* `POST /export/{variant_id}` (returns file or external push stub)
* `POST /schedule` `GET /schedule`
* `GET /kpis` (stubbed KPIs for dashboard)
* `GET /healthz` `GET /readyz`
* **Rate limit** middleware and **quota** accounting endpoints (`GET /usage`)

---

## 4) Developer Experience

* **Command set** (top‑level scripts):

  * `./scripts/start-frontend.sh` → vite on 3001
  * `./scripts/start-backend.sh` → poetry/uvicorn on 8000
  * `./scripts/run-tests.sh` → frontend + backend + E2E (+ JSON summaries)
  * `./scripts/seed-dev.sh` → create demo user, sample jobs/variants
* **Environment:** `.env.example` at root and per app; never commit real secrets. Provide sensible dev defaults.
* **Pre‑commit:** formatters/linters/secret scan. Conventional commits enforced via commitlint.

---

## 5) CI/CD & Quality Gates

* **GitHub Actions workflows**:

  1. **build-verification**: install, typecheck, lint, unit tests for FE/BE
  2. **frontend-tests**: vitest & Playwright (webServer uses port 3001 with `--strictPort --host`)
  3. **backend-tests**: pytest
  4. **e2e-tests**: end‑to‑end against ephemeral dev server
  5. **security-scan**: secret scan + basic SAST (bandit/semgrep light)
  6. **pr-checks-summary**: comment summarizing gates
* **Branch protection (develop/main)**: require all checks to pass, at least 1 review.
* **Artifacts:** store Playwright traces/video on failure; upload coverage summaries (no hard threshold, but display).

---

## 6) Observability & Ops

* **Sentry** wiring (DSN via env), **PostHog** analytics (frontend), basic **OpenTelemetry** stubs.
* **Health checks:** `/healthz` (shallow), `/readyz` (deep: DB/Redis, queue ping).
* **Runbooks:** `docs/RUNBOOKS.md` (restart worker, rotate keys, env checklist).

---

## 7) Collaboration & Agents

* Provide minimal `collaboration/` scaffolding:

  * `state/tasks.json`, `state/locks.json`, `state/agents.json`
  * `events/events.jsonl`, `logs/log.md`
  * Lease‑based locking (TTL fields) and example CLI `scripts/collab_cli.py` that does ETag‑checked atomic writes.
* Use `collaboration/state/*.json` and `events/events.jsonl` as the source of truth; update via APIs or local scripts.
* Include **agents.md** guide with roles: Planner, Implementer, Critic, Integrator, Watchdog, and DoD checklist.

---

## 8) UX Requirements

* Clean, minimal dashboard layout. Use `data-testid` attributes for critical controls.
* Studio flow: paste/input source → choose channels → generate → variants list/cards → edit/accept → export/schedule.
* Global toasts, loading states, and empty states.
* Accessibility: keyboard nav, focus rings, aria labels.

---

## 9) Failure‑route Design

* Network/API failure → show human‑readable error; retry/backoff; log to Sentry; preserve work.
* Background task failure → Job moves to `failed` with a reason; allow `retry` endpoint; ensure idempotency.
* Quota exceeded → 429 with reset hints; UI surfaces friendly message.

---

## 10) Configuration & Secrets

Create `.env.example` at repo root with placeholders:

```
VITE_API_BASE_URL=http://localhost:8000
OPENAI_API_KEY=sk-... (placeholder)
DATABASE_URL=postgresql://username:password@localhost:5432/kyros
REDIS_URL=redis://localhost:6379
JWT_SECRET=change-me
SENTRY_DSN=
POSTHOG_API_KEY=
POSTHOG_HOST=https://app.posthog.com
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10
```

---

## 11) Phase‑based Builder Checklist

Before coding, perform:

* **Phase 0 — Context Discovery (5 min)**

  * Generate dependency graph, integration points, and expected‑files check (docker‑compose, Makefile, etc.).
* **Phase 1 — Scaffolding**: repo tree, package manifests, lint/config files, Dockerfiles, compose.
* **Phase 2 — Core vertical slice**: Auth → Create Job → Generate stubs → Accept Variant → Export stub.
* **Phase 3 — Scheduling & KPIs**
* **Phase 4 — E2E stabilization**: add `data-testid`, Playwright flows, API mocks where needed.
* **Phase 5 — Docs & Runbooks**.

For each phase, produce a short note in `docs/BUILD_NOTES.md` with decisions and any deviations.

---

## 12) Deliverables (exact)

* Working monorepo with the structure above.
* **Docs:** `README.md`, `docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`, `docs/TESTING.md`, `docs/RUNBOOKS.md`, `docs/ADRS/adr-0001-template.md`, `docs/DEVIATIONS.md`.
* **CI:** GitHub Actions workflows matching Section 5.
* **Docker:** Backend & worker Dockerfiles; `docker-compose.yml` for local (Postgres, Redis, API, worker, frontend).
* **Tests:**

  * Backend unit tests covering models, services, and API routes.
  * Frontend unit tests for key components; Playwright E2E for the Studio and Jobs happy‑paths.
* **Seed data** script creating demo users and example jobs/variants.

---

## 13) Acceptance Criteria (gates to consider the build “done”)

* `./scripts/start-frontend.sh` serves React on **[http://localhost:3001](http://localhost:3001)**.
* `./scripts/start-backend.sh` serves FastAPI on **[http://localhost:8000](http://localhost:8000)**.
* `./scripts/run-tests.sh` runs FE+BE units and E2E; all pass locally.
* Playwright tests use `data-testid` selectors and a `webServer` that starts Vite on port 3001 with `--strictPort --host`.
* OpenAPI docs available at `/docs`; basic auth/register/login works.
* Jobs can be created; variants are generated via stub; variant can be accepted and exported as text/JSON.
* Security scan (secret scan + basic SAST) shows no critical issues.
* `.env.example` present; no secrets committed.
* CI green on PR with branch protection enforcing checks and one approving review.

---

## 14) Stretch (nice‑to‑have if time allows)

* OpenTelemetry traces for one end‑to‑end flow (Studio → API → Celery task → DB).
* Visual regression baseline for 2–3 critical pages.
* Basic multi‑tenant support placeholder (org\_id on core tables, no hard isolation yet).

---

## 15) Handoff Instructions to Human/Agents

* After generation, produce **`SUMMARY.md`** listing what exists, what’s stubbed, and any TODOs.
* Include a short **onboarding script** in `scripts/` that checks dev prerequisites, installs deps, and prints next steps.
* Open a PR checklist in `.github/PULL_REQUEST_TEMPLATE.md` mirroring the Acceptance Criteria.

---

**Important:** If any constraint conflicts, prefer **testability, security, and clarity** over complexity. Keep diffs small and files focused.
