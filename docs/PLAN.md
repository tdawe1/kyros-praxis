# Changelog

- v1.1 (2024-09-10): Merged baks, aligned stacks, fixed dates.

## 0) Goals & Non‑Negotiables

**What “v1” must ship:**

- **Collab API** with **ETag + atomic writes**, **lease-based execution**, and **append‑only events** exposed via SSE/long‑poll tail.
- **Jobs vertical slice** (auth → create job → stub variant → accept → export → list).
- **Console UI**: pages for **Agents**, **Tasks (Kanban)**, **Leases**, **Events (live tail)**, plus **Jobs / Studio / Scheduler / Settings** wired to APIs.
- **Worker**: Celery+Redis with at least one safe executor (e.g., lint/format) that **acquires leases**, **emits events**, handles **retry/backoff**.
- **Quality gates**: pre‑commit, unit tests (FE/BE), Playwright E2E, secret scan, `.env.example`, basic rate limits and JWT, `/readyz` deep checks.&#x20;

**Stretch (nice‑to‑have):**

- **Omnichannel** “Command Center” surfaces (WebSocket/Email/API/Slack/Webhook) + Remote Control UI.
- **LangGraph** runner mounted in worker for structured agent flows.
- Fast UI skin using **TeleportHQ/Plasmic** if design time is tight.

---

## 1) Architecture Blueprint

**Monorepo** (ports FE:3000, BE:8000):

```
frontend/            Next.js 14.2.5 + React 18 + TS + Carbon UI (dark-first)
backend/             FastAPI + SQLAlchemy + Alembic + Celery + Redis + Postgres
collaboration/       state/*.json (tasks|locks|agents), events/events.jsonl, logs/log.md
mcp/                 kyros_collab_server stub (stdio JSON-RPC)
scripts/             start/run/seed/test scripts
docs/                ARCHITECTURE, DEPLOYMENT, TESTING, RUNBOOKS, ADRs, BUILD_NOTES
```

See [ADR 0005](adr/0005-frontend-stack.md) for details on the frontend stack decision.

- **Collab store** is the source of truth for agent workflow objects; **ETag** encodes file digest + version; writes are **atomic replace** guarded by `If‑Match`.
- **Events** are append‑only `JSONL` with SSE tail for live UI.
- **Leases not locks**: entries with `ttl_seconds` + `heartbeat_at`; stale reclaim emits events.
- **Jobs** persisted in Postgres; variants editable/acceptable and exportable via API.&#x20;

**Optional:** LangGraph runner inside Celery process; orchestrates tool calls but still acquires **leases** and emits **events** for observability.

---

## 2) Milestones & Work Breakdown (in order)

### Phase 0 — Repo Scaffolding & Context Hygiene

- Fork your **Full‑Stack FastAPI Template** baseline (or equivalent).
- Create monorepo folders + **ports** + **env files**.
- Add **pre‑commit**, linters/formatters (black/isort/ruff, eslint/biome), secret scan.
- Seed `collaboration/state/*.json` and `events.jsonl`.
- Add **scripts**: `start-frontend.sh`, `start-backend.sh`, `run-tests.sh`, `seed-dev.sh`.
- CI skeleton: build, backend tests, frontend tests, e2e, security scan, PR checks summary.&#x20;

### Phase 1 — Collab API (ETag + Atomic) & Events Tail

**Backend routes** (FastAPI):

- `GET /collab/state/{kind}` → `{data|text, etag}`.
- `POST /collab/tasks` (create) / `PATCH /collab/tasks/{id}` with `If‑Match` ETag.
- Transitions: `POST /collab/tasks/{id}/transition`.
- Leases: `POST /collab/leases/acquire` / `POST /collab/leases/{lock_id}/release`.
- Events: `POST /collab/events` (append JSONL), `GET /collab/events/tail` (SSE).
- Health: `/healthz`, `/readyz` (DB/Redis/queue checks).
  **Tests:** ETag mismatch, atomic write rollback, stale lease reclaim, SSE tail.
  **Observability:** structured logs, Sentry hooks (env‑driven).&#x20;

### Phase 2 — Console (Collab Pages)

**Frontend pages** with TanStack Query + SSE:

- **Agents** (role/skills/status/last_seen; toggle availability).
- **Tasks** Kanban: `queued → claimed → in_progress → review → approved → merging → done`, dependency badges & DoD checklist; transitions via Collab API.
- **Leases** (TTL countdown, reclaim stale).
- **Events**: live tail + filters + “Generate human log”.
- UX: toasts, skeletons, `data-testid`.
  **Feature flags**: `config/flags.json` demoMode on/off.&#x20;

### Phase 3 — Jobs Vertical Slice

**API:**

- Day‑1 scope (implemented): `POST /jobs` (payload `{title, description?}`), `GET /jobs`, `GET /jobs/{id}`. All routes require JWT and API key; responses include `ETag` (job id for Day‑1).
- Day‑2 scope: `GET/PUT /variants/{id}`, `POST /export/{variant_id}`, `POST/GET /schedule`.
  **Models & Alembic:** User, Preset, Job, Variant, Schedule, Tool, AuditEvent.
  **Auth:** JWT (access/refresh), rate limits, input validation.
  **FE:** Jobs list → Job detail → Variant accept → Export flow.&#x20;

### Phase 4 — Runner & Safe Executor (+ Optional LangGraph)

- Celery worker acquires **lease**, runs **safe executor** (e.g., format Markdown, run linter), emits events, retries with backoff, releases lease.
- Optional: mount **LangGraph** agent flow inside worker for structured tools; surface run status via events.&#x20;

### Phase 5 — Omnichannel Command Center (MVP)

- **Unified Communication Hub** (WS/Email/API/Slack/Webhook) + channel adapters.
- **Remote Control UI**: Real‑time, Scheduled, Triggers; interactive terminal; activity feed.
- **Email Commander** (IMAP/SMTP) to parse commands (pattern/JSON/NL) and reply.
- **Slack**: slash commands + status links.
- **Security**: per‑channel rate limits + API‑key/JWT checks + audit trail.

> Scope this as a demo‑grade layer in v1; wire through the **Jobs** and **Collab** APIs so commands translate into task/job mutations.

### Phase 6 — E2E & CI Hardening

- **Playwright** happy‑path: Studio → Generate → Accept → Export; Collab flows; collect traces/video artifacts.
- GitHub Actions: `build-verification`, `frontend-tests`, `backend-tests`, `e2e-tests`, `security-scan`, `pr-checks-summary`; branch protection contexts.&#x20;

### Phase 7 — Docs & Runbooks

- `ARCHITECTURE.md`, `DEPLOYMENT.md`, `TESTING.md`, `RUNBOOKS.md`, `ADRS/adr-0001-template.md`, `DEVIATIONS.md`, `BUILD_NOTES.md`.
- **Commit/PR protocol** and **Context Reset** mini‑brief for sub‑tasks.&#x20;

---

## 3) Backlog with IDs (seed immediately)

Create these tasks in `collaboration/state/tasks.json` (you can reuse IDs):

- **T‑100**: Collab API with ETag + SSE (backend)
- **T‑101**: Console pages (Agents/Tasks/Leases/Events)
- **T‑102**: Celery runner + safe executor (backend)
- **T‑103**: Jobs vertical slice (auth→job→variant→accept→export)
- **T‑104**: Playwright flows (Collab + Jobs) + `data-testid`
- **T‑105**: Docs & Runbooks + ADR template
  Each task carries a DoD per Section 8 (**tests, pre‑commit, docs, critic review, events emitted**).&#x20;

Add Omnichannel tasks:

- **T‑200**: Omnichannel hub (WS/Email/API/Slack/Webhook) + audit log.
- **T‑201**: Remote Control UI tabs (Real‑Time/Scheduled/Triggers) + activity feed.
- **T‑202**: Email Commander + parsing + response loop.
- **T‑203**: Slack slash commands + deep link to tasks/jobs.
- **T‑204**: Channel rate limiting + API‑key validation middleware.

---

## 4) API Contracts (key details)

**Collab API**

- `GET /collab/state/{kind}` → `{data|text, etag}`
- `POST /collab/tasks` → `{id}`
- `PATCH /collab/tasks/{id}` with `If‑Match: <etag>` → `{ok, etag}`
- `POST /collab/tasks/{id}/transition` → `{old_status, new_status}`
- `POST /collab/leases/acquire` / `.../{lock_id}/release` → `{lock_id}` / `{ok}`
- `POST /collab/events` → `{ok}`
- `GET /collab/events/tail?since=<ts>` → SSE stream (newline‑delimited JSON).&#x20;

**Jobs API**

- `POST /jobs` → `{id, status:"queued"}`; `GET /jobs` and `/jobs/{id}`
- `GET/PUT /variants/{id}`
- `POST /export/{variant_id}` (download or JSON)
- `POST/GET /schedule` (cron or ISO schedule).&#x20;

**Auth/Security**

- JWT (access/refresh), basic **rate limits**, **input validation**, and **audit events**. Note: Frontend uses OIDC via Next-Auth; implement JWT/OIDC bridge for compatibility.&#x20;

**Examples (using curl for local dev at http://localhost:8000)**

- List tasks with ETag caching: `curl -H "If-None-Match: etag-val" http://localhost:8000/collab/state/tasks` → 304 if unchanged, else 200 with body and new ETag.
- Create job with auth: `curl -X POST -H "Authorization: Bearer jwt-token" -H "Content-Type: application/json" -d '{"name":"test-job"}' http://localhost:8000/jobs` → `{id, status: "queued"}`.
- Generate Swagger docs: Use contracts/api.yaml in FastAPI app; access interactive docs at http://localhost:8000/docs.

---

## 5) Concurrency & Data Integrity

**ETag**

- Compute ETag as strong hash of canonicalized JSON + monotonic version.
- **PATCH** requires `If‑Match`; server verifies ETag and writes via **atomic replace** (temp file + fsync + rename).
- On mismatch → `412 Precondition Failed`; client retries with jitter and latest ETag.
  **Events**
- Always append `{ts, event, actor, target, details}` to `events.jsonl`; never mutate historical lines.
- SSE tail: keep‑alive + `Last-Event-ID` support to resume.
  **Leases**
- Structure: `{lock_id, resource, holder, acquired_at, ttl_seconds, heartbeat_at}`.
- Reclaim if `now > heartbeat_at + ttl`; emit `lease_reclaimed`.&#x20;

---

## 6) Worker & Executors

- Celery app connects to Redis; tasks acquire **lease**, run safe executor(s):

  - `docs/format` (Prettier/MD formatter), `lint` (ruff/flake8), or `docs/changelog` generator.

- Emit events: `task_claimed`, `executor_started`, `executor_succeeded|failed`, `lease_released`.
- **Backoff**: exponential with jitter on transient errors.
- **Optional LangGraph**: define a small graph (fetch → transform → write) to showcase structured flows and tool calls; still report via events.&#x20;

---

## 7) Frontend Details

- **Data layer**: TanStack Query; mutation invalidation + optimistic updates for Kanban moves.
- **Events page**: SSE tail with filters (by task/agent/event type) + “Generate human log” (server summarizes selected events).
- **Leases page**: TTL countdown per lease; “Reclaim stale” action.
- **Jobs**: list/detail/variant/accept/export; toasts on success/error.
- **Studio**: minimal shell to kick off a Job or Variant from a preset.
- **Settings**: presets CRUD.
- **Omnichannel UI**:

  - Channel overview cards (status, metrics).
  - **Remote Control**: tabs (Real‑Time / Scheduled / Triggers), terminal area, response pane.
  - **Channels** page: per‑channel controls & live command flow visualization.

- **Feature flags**: `demoMode` + `schedulerEnabled` in `config/flags.json`.&#x20;

> If you want a polished shell quickly, generate a layout with **TeleportHQ/Plasmic** and drop into `frontend/`, then wire the components to our hooks.

---

## 8) CI, Testing, and DoD

**Unit**

- Backend: ETag/atomic write tests; leases; events tail; Jobs CRUD.
- Frontend: components/hooks with Vitest; MSW fixtures for demo mode.

**E2E**

- Playwright flows:

  1. Studio → Generate Job → Variant Accept → Export (artifact check).
  2. Collab: create task → claim (lease) → transition → events visible.

  - Upload traces/video artifacts on failure.

**Pipelines**

- Actions: build‑verification, frontend-tests, backend-tests, e2e-tests, security-scan, pr-checks-summary; branch protection.

**Definition of Done (per task)**

- Tests updated, pre‑commit passing (format/lint/type/secrets), docs updated, **critic review**, events emitted where relevant.&#x20;

---

## 9) Security & Ops

- **JWT** auth + refresh; **API key** for channel webhooks; per‑channel **rate limiting**.
- **/readyz** deep check: DB migration status, Redis ping, Celery queue roundtrip.
- **Sentry** optional via env; structured JSON logs; audit events into DB and/or events stream.
- `.env.example` at repo root; never commit real secrets.
- OAuth2 for JWT refresh using python-jose; rate limit /auth/login to 5/min via middleware.
- Celery scalability: Set `CELERY_WORKER_CONCURRENCY=4` env var; monitor queues with Flower (pip install flower; celery -A app flower).&#x20;

---

## 10) Data Model (Jobs slice)

**Tables (SQLAlchemy + Alembic):**

- `users`, `presets`, `jobs (id, status, created_by, created_at)`,
- `variants (id, job_id, status, payload, accepted_at)`,
- `schedules (id, cron|iso, next_run, active)`,
- `tools (id, name, config)`,
- `audit_events (id, ts, actor, action, payload)`.&#x20;

---

## 11) Dev UX & PR Protocol

- Branch naming: `feat/<task-id>-slug`.
- Commit template with rationale, touched files, tests, risks/mitigations.
- PR body: scope, acceptance criteria verified, failing tests (if any) explain why, and UI screenshots.
- **Context Reset** mini‑brief between subtasks to keep agents focused.&#x20;

---

## 12) “Day‑1” Commands & Files to Create

**Repo**

```bash
# backend
uv venv && source .venv/bin/activate || python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn[standard] pydantic-settings sqlalchemy alembic psycopg2-binary \
            celery[redis] redis python-jose[cryptography] passlib[bcrypt] httpx sse-starlette

# frontend
npx create-next-app@latest frontend --ts --app --src-dir --tailwind no
cd frontend && npm i @tanstack/react-query next-auth @carbon/react
```

**Backbone files**

- `backend/main.py`: app + routers for `/collab/*`, `/jobs/*`, `/auth/*`, `/healthz`, `/readyz`.
- `backend/collab/` module: ETag utils, atomic write, SSE tail, lease manager.
- `backend/jobs/` module: models, CRUD, export service.
- `frontend/src/pages/` for Agents, Tasks, Leases, Events, Jobs, Studio, Scheduler, Settings, Auth.
- `collaboration/state/tasks.json|locks.json|agents.json`, `collaboration/events/events.jsonl`, `collaboration/logs/log.md`.
- `scripts/*.sh` and `.env.example`.&#x20;

---

## 13) Risk Register (with mitigations)

- **Race conditions on ETag** → server‑side atomic replace + `412` handling; client retry w/ jitter.
- **SSE scale** → fall back to long‑poll; server keep‑alives; filter at source.
- **Email polling latency** → cron‑like poll + idempotency keys; promote to webhook where possible.
- **Slack/Channel rate limits** → per‑channel throttling + backoff; capture 429s in audit.
- **Secrets sprawl** → `.env.example`, sealed secrets in CI, secret scan in pre‑commit and pipeline.&#x20;

---

## 14) Deliverables Checklist (what reviewers should see)

- **Backend:** endpoints live + OpenAPI `/docs`; JWT login in dev.
- **Frontend:** 8 pages wired; demoMode on; live Events tail; “reclaim stale lease” button works.
- **Worker:** Celery task demonstrates lease lifecycle & event emissions.
- **DB:** Alembic migrations applied; Jobs flow green.
- **CI:** all workflows green; Playwright artifacts on failure.
- **Docs:** architecture, deployment, testing, runbooks, ADR template, deviations, build notes.
- **SUMMARY.md** with endpoints/pages implemented + next steps.

## Tasks (Deduplicated)

- Collab API with ETag + SSE (TDS-1) — In Progress, P0, Due: Q4 2024
- Channel rate limiting + API-key validation middleware (TDS-9) — In Progress, P1, Due: Q4 2024
- Slack slash commands + deep link to tasks/jobs (TDS-8) — In Progress, P1, Due: Q4 2024
- Remote Control UI (Real-Time/Scheduled/Triggers) + activity feed (TDS-7) — Backlog, P1, Due: Q4 2024
- Omnichannel hub (WS/Email/API/Slack/Webhook) + audit log (TDS-6) — Backlog, P1, Due: Q4 2024
- Docs & Runbooks + ADR template (TDS-5) — Backlog, P0, Due: Q4 2024
- Playwright flows (Collab + Jobs) + data-testid (TDS-4) — Backlog, P0, Due: Q4 2024
- Jobs vertical slice (auth→job→variant→accept→export) (TDS-3) — Backlog, P0, Due: Q4 2024
- Console pages: Agents/Tasks/Leases/Events (TDS-12) — Backlog, P0, Due: Q4 2024
- Celery runner + safe executor (TDS-13) — Backlog, P0, Due: Q4 2024
- Email Commander + parsing + response loop (TDS-19) — Backlog, P1, Due: Q4 2024
- Design BYOK connection object & crypto (TDS-66) — Status N/A, P0, Due: N/A
- API: POST/GET/DELETE /v1/connections (TDS-67) — Status N/A, P0, Due: N/A
- API: POST /v1/connections/{id}/test (TDS-68) — Status N/A, P0, Due: N/A
- Policy engine (MVP) (TDS-69) — Status N/A, P0, Due: N/A
- Budget accounting (MVP) (TDS-70) — Status N/A, P0, Due: N/A
- Jobs model & enqueue (TDS-71) — Status N/A, P0, Due: N/A
- Events stream (SSE) (TDS-72) — Status N/A, P0, Due: N/A
- Worker skeleton (OpenAI) (TDS-73) — Status N/A, P0, Due: N/A
- Console: Settings/Connections (skeleton) (TDS-74) — Status N/A, P0, Due: N/A
- Console: Jobs list/detail (skeleton) (TDS-75) — Status N/A, P0, Due: N/A
- Mock provider toggle (TDS-76) — Status N/A, P0, Due: N/A
- Critic pass (Sprint 0) (TDS-77) — Status N/A, P0, Due: N/A
- Policy UI (TDS-78) — Status N/A, P1, Due: N/A
- Usage & Cost surfacing (TDS-79) — Status N/A, P1, Due: N/A
- Provider adapters (Anthropic/Gemini) (TDS-80) — Status N/A, P1, Due: N/A
- E2E: Jobs happy path (TDS-81) — Status N/A, P1, Due: N/A
- Settings polish & audit (TDS-82) — Status N/A, P1, Due: N/A
- Demo seed & toggle (TDS-83) — Status N/A, P2, Due: N/A
- Premium: Codex connector (alpha) (TDS-84) — Status N/A, P2, Due: N/A
- Critic pass (Sprint 1) (TDS-85) — Status N/A, P0, Due: N/A
- Docker Compose (PG, Redis, API, Worker, Web) (TDS-97) — Status N/A, P0, Due: N/A
- Alembic init & initial schema (TDS-98) — Status N/A, P0, Due: N/A
- Structured logging baseline (TDS-99) — Status N/A, P0, Due: N/A
- Crypto service (AES-GCM envelope) (TDS-100) — Status N/A, P0, Due: N/A
- Connections API CRUD + Test (TDS-101) — Status N/A, P0, Due: N/A
- Queue & Worker skeleton (NOOP + idempotency) (TDS-102) — Status N/A, P0, Due: N/A
- Jobs API accept + GET + idempotency (TDS-103) — Status N/A, P0, Due: N/A
- SSE stub with backpressure (TDS-104) — Status N/A, P0, Due: N/A
- UI skeleton: Connections & Jobs (wire only) (TDS-105) — Status N/A, P0, Due: N/A
- Aggregated /health endpoint (TDS-106) — Status N/A, P1, Due: N/A
- Job cancellation (stub) (TDS-107) — Status N/A, P1, Due: N/A
- SSE client reconnection policy (TDS-108) — Status N/A, P0, Due: N/A
- OpenAI adapter & usage metering (TDS-109) — Status N/A, P0, Due: N/A
- Policy engine (6 cases) + UI controls (TDS-110) — Status N/A, P0, Due: N/A
- Budget enforcement (TDS-111) — Status N/A, P0, Due: N/A
- SSE real streaming with backpressure (TDS-112) — Status N/A, P0, Due: N/A
- Circuit breaker around provider calls (TDS-113) — Status N/A, P1, Due: N/A
- UI polish: Jobs + Connections (TDS-114) — Status N/A, P1, Due: N/A
- E2E: happy & failure paths (Playwright) (TDS-115) — Status N/A, P1, Due: N/A
- 3 concurrent jobs load test (TDS-116) — Status N/A, P1, Due: N/A
