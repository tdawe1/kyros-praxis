# ADR 0002: Add Agent Model and Endpoints for Frontend Integration

## Status
Proposed

## Context
The original PLAN.md specifies an Agents page showing role, skills, status, last_seen, and toggle availability via Collab API. Current backend plan focuses on tasks; this ADR adds minimal Agent support to align with frontend for local demo.

## Decision
- Add `Agent` model to SQLAlchemy with fields: id, role, skills (JSON), status (enum: available, unavailable), last_seen, version.
- Add endpoints: GET /collab/state/agents (list with ETag), POST /collab/agents/{id}/toggle (update status with ETag).
- Integrate into steel thread: Auth → List Agents → Toggle → Tasks.
- Auth alignment: Backend uses JWT; frontend Next-Auth OIDC proxies to obtain JWT for API calls. No major architecture change, but adds to collab store pattern.
- Events: Agent toggles emit events for real-time updates via SSE.

## Consequences
- Minimal addition to models/endpoints, keeps steel thread focused.
- Enables frontend Agents page demo without delaying tasks.
- Future: Extend for full agent lifecycle (e.g., assign to tasks).

## References
- Original PLAN.md: Section 2 Phase 2 (Console pages).
- Backend-current-plan.md updates in this revision.