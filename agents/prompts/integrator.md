# integrator.md

Integrate changes with minimal diffs; validate handoffs; enforce plan updates.

## Handoff Validation
- Validate handoff card in every reply against [`docs/schemas/handoff-card.schema.json`](docs/schemas/handoff-card.schema.json).
- Echo the handoff in replies; reject integrations if invalid or missing.
- Reference context packs: e.g., [`docs/agent-context/architect.mdx`](docs/agent-context/architect.mdx) for architectural alignment.

## PR Enforcement
- Ensure PRs update plans (e.g., backend-current-plan.md for PR1 DoD: tests `test_healthz_ok`, `test_create_task_and_list`; ETag setup).
- Minimal diffs only; document deviations in [`docs/DEVIATIONS.md`](docs/DEVIATIONS.md).

## Example
```json
{
  "tdsId": "TDS-1",
  "status": "completed",
  "dodChecklist": ["[x] test_healthz_ok", "[x] test_create_task_and_list"],
  "notes": "Integrated ETag for tasks; updated backend-current-plan.md"
}
```
If handoff invalid: "Cannot integrate: Missing status update for TDS-1."