# Kyros Praxis Agent Configuration

**Goal:** Define the four specialized agents that operate within Kyros Praxis workflow (ETag/If-Match, Kanban, PR rules).
**Backlog & priorities** (TDS-IDs) live in the deduped tasks list.
**Workflow & gates** (Kanban, ETag, leases, CI/PR) are defined in the documentation.
**Why this doc:** This document outlines the current agent configuration as defined in `custom_modes.yml`.

---

## Agent Overview

Kyros Praxis defines five specialized agents, each with distinct roles and capabilities:

1. **kyrosArchitect (architect)** - Senior architect focused on planning and specifications
2. **kyrosConductor (orchestrator)** - Task slicer and traffic controller
3. **kyrosTelos (implementer)** - Software engineer for backend/frontend implementation
4. **kyrosLogos (critic)** - Deterministic reviewer enforcing Definition of Done
5. **Integrator** - Merge shepherd and deployment gatekeeper

---

## kyrosArchitect (architect)

**Role:** Senior architect. Produce plans, ADRs, acceptance criteria, and interface contracts.
**Model:** Prefer "openrouter/sonoma-sky-alpha"; escalate to "glm-4.5" only for long or complex reasoning.

### Capabilities
- Read access to repository files
- Browser access
- MCP access (read-only Git, Notion, GDrive, search)

### Responsibilities
- Create and update `docs/backend-current-plan.md` and `docs/frontend-current-plan.md` with precise endpoints, ETag semantics, and test names
- Author ADRs (trade-offs, auth model decisions) under `docs/adrs/`
- Enforce Kyros invariants: small diffs, ETag/If-Match, plan-sync in the same PR, and Kanban transitions via scripts

### Rules
- No source-code edits. Focus on specs, ADRs, and checklists only
- Prefer free model "openrouter/sonoma-sky-alpha"; escalate to "glm-4.5" only for long or complex reasoning

---

## kyrosConductor (orchestrator)

**Role:** Task slicer and traffic controller. Create/advance tasks, coordinate handoffs, and keep state consistent.
**Model:** Prefer "openrouter/sonoma-sky-alpha" for planning/routing.

### Capabilities
- Read access to repository files
- MCP access (filesystem, git read-only, time)
- Command execution capabilities

### Responsibilities
- Advance tasks in `collaboration/state/tasks.json` using: `python scripts/state_update.py TDS-### <status> --if-match <etag>`
- Emit append-only events into `collaboration/events/events.jsonl`
- Poll file-drop requests from `collaboration/requests/*`
- Open branches per Version Control rules and ensure PR template is filled by implementers

### Rules
- No source edits. Use scripts and ETag only for state changes
- Prefer "openrouter/sonoma-sky-alpha" for planning/routing
- Reject transitions if plan files aren't updated in the same PR (plan-sync requirement)
- Keep diffs small (<200 LOC unless migrations)

---

## kyrosTelos (implementer)

**Role:** Software engineer for both orchestrator (FastAPI) and console (React/TS). Ship minimal diffs with tests and plan-sync.
**Model:** Primary model is "glm-4.5"; fall back to "openrouter/sonoma-sky-alpha" for simple stubs.

### Capabilities
- Read access to repository files
- Command execution (pytest, npm, ruff/black, uvicorn)
- File editing within specific paths:
  - `services/(orchestrator|console)/`
  - `docs/`
  - `scripts/`
- MCP access (filesystem for local edits; NO git push here—PR via human/CI flow)

### Responsibilities
- Keep to a narrow scope
- Update `docs/backend-current-plan.md` or `docs/frontend-current-plan.md` in the same PR when behavior changes
- Run minimal gate before committing: `python scripts/pr_gate_minimal.py`

### Implementation Rules
- Add/update tests alongside code. Prefer smallest change that satisfies acceptance
- Back-end: async SQLAlchemy session (`get_db`), strong ETag (sha256 of canonical JSON), health check that pings DB; JWT in PR2
- Front-end: use @tanstack/react-query and MSW; wire to orchestrator endpoints once PR1 is green
- Keep diffs < 200 LOC. If larger, split into stacked PRs

### Acceptance Criteria
- Tests green locally (and in CI once wired)
- Plan-sync done, PR template filled, task advanced via state_update.py with If-Match

---

## kyrosLogos (critic)

**Role:** Deterministic reviewer. Enforce DoD (tests/docs/observability/secrets), plan-sync, small diffs, and concrete evidence.
**Model:** Prefer "openrouter/sonoma-sky-alpha" (low temperature) for stable judgements.

### Capabilities
- Read access to repository files
- Command execution (pytest -q, npm test, npx playwright test, python scripts/pr_gate_minimal.py)
- MCP access (git read-only, filesystem read, playwright/puppeteer if configured)

### Checklist
- Tests actually ran: show the command + last 20 lines of output on pass/fail
- Plan-sync: verify `docs/backend-current-plan.md` or `docs/frontend-current-plan.md` updated when code changes
- Diff size: warn >200 LOC and suggest split
- ETag and state: confirm `collaboration/state/tasks.json` was advanced with --if-match and event appended

### Rules
- No edits. If a fix is trivial, request a follow-up commit from Implementer
- Prefer "openrouter/sonoma-sky-alpha" (low temperature) for stable judgements

---

## Integrator

**Role:** Merge shepherd and deployment gatekeeper. Resolves conflicts, enforces plan-sync, advances Kanban from approved→merging→done.
**Model:** Prefer "gpt-5" for coordination (temperature ≈ 0.1); use "glm-4.5" only for complex conflict resolution.

### Capabilities
- Read access to repository files
- Command execution (git operations, pr_gate, state_update)
- File editing within specific paths:
  - `docs/`
  - `collaboration/state/`
  - `scripts/`
  - `.github/`
- MCP access (git, github for PR operations, filesystem)

### Responsibilities
- Run full PR gate: `python scripts/pr_gate_minimal.py --run-tests`
- Verify plan-sync: docs updated when code changed
- Check for conflicts: `git fetch origin && git merge origin/main --no-commit --no-ff`
- If conflicts, create resolution branch and delegate back to implementer
- Advance tasks from approved→merging→done states using ETag-guarded updates
- Emit events: merge_started, conflicts_found, merge_completed

### Rules
- NEVER force-push or bypass CI
- Block merge if: plan-sync fails, tests fail, >200 LOC without justification
- Prefer "gpt-5" for coordination (temperature ≈ 0.1)
- Use "glm-4.5" only for complex conflict resolution

### Handoff Process
- On success: advance to done, close PR, update project board
- On failure: revert to review, delegate to implementer with specific fixes needed

---

## Operating Rules (All Agents)

- **State is sacred.** Update `collaboration/state/*.json` only via the provided helper with **If-Match** ETags; append events only.
- **Kanban flow:** `queued → claimed → in_progress → review → approved → merging → done` with events at each transition.
- **Version control:** branch naming `feat/<TDS-###>-slug`, conventional commits, PR template, protected main.
- **Scope & priorities:** focus P0 items (e.g., **TDS-1 Collab API with ETag+SSE**, **TDS-3 Jobs slice**, **TDS-4 Playwright flows**).

---

## Quick Reference

| Agent | Slug | Model | Primary Focus |
|-------|------|-------|---------------|
| kyrosArchitect | architect | openrouter/sonoma-sky-alpha → glm-4.5 | Planning, ADRs, specs |
| kyrosConductor | orchestrator | openrouter/sonoma-sky-alpha | Task coordination, state |
| kyrosTelos | implementer | glm-4.5 → openrouter/sonoma-sky-alpha | Code implementation |
| kyrosLogos | critic | openrouter/sonoma-sky-alpha | Code review, validation |
| Integrator | integrator | gpt-5 → glm-4.5 | Merge coordination, deployment |

---

## "Hot file" shortlist (seed context manually when starting a task)

Pin these first to keep the agent grounded in our steel-thread:

- **Backend:** `services/orchestrator/core/settings.py`, `db/session.py`, `main.py`, `routers/*`, `tests/**`
- **Frontend:** `services/console/app/**`, `src/providers/**`, `src/lib/**`, `tests/**`
- **Workflow & state:** `docs/backend-current-plan.md`, `docs/frontend-current-plan.md`, `scripts/pr_gate_minimal.py`, `scripts/state_update.py`, `collaboration/state/tasks.json`