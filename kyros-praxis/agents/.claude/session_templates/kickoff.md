# Claude Max Kickoff (paste as first message)
Role: architect.claude — Deep work session

Goal: <one decisive outcome, e.g., "Implement Collab API with ETag + SSE and passing tests">

Repo summary (short): <key dirs/files>
Context pack (paths): collaboration/state/*, backend/routers/collab.py, docs/ARCHITECTURE.md#collab-api
Constraints:
- Small, reviewable diffs; add/adjust tests
- ETag + atomic write semantics; SSE live tail
- No secrets; .env.example only

Deliverables this session:
- Code + tests + docs/BUILD_NOTES.md delta
- PR description with risk notes and next-step
