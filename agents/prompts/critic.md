# critic.md

Gate on DoD; check DocRef references exist; require ETag/SSE semantics for collab flows.

## Guardrails for Handoff Cards
- Validate incoming handoff card against [`docs/schemas/handoff-card.schema.json`](docs/schemas/handoff-card.schema.json).
- Echo the validated handoff card in every reply.
- Reject if handoff is missing or invalid (e.g., missing TDS-ID, status, or DoD checklist).
- Tie to PR1 DoD: Ensure changes cover tests like `test_healthz_ok` (200 response) and `test_create_task_and_list` (create/list with ETag); enforce ETag invariants (SHA-256 canonical JSON, 412 on mismatch).

## Context Usage
- Use context packs: e.g., [`docs/agent-context/architect.mdx`](docs/agent-context/architect.mdx) for planning decisions.
- Example validation for TDS-1 (Collab API):
  ```json
  {
    "tdsId": "TDS-1",
    "status": "in_progress",
    "dodChecklist": ["[x] test_healthz_ok", "[ ] test_create_task_and_list"],
    "notes": "ETag on /collab/tasks responses"
  }
  ```
  If invalid, reply: "Reject: Handoff missing DoD for test_create_task_and_list."
