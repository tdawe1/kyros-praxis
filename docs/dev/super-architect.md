# Super Architect: Dev Notes

Environment toggles:

- Server (super/delegate):
  - `SUPER_AUTH_USER` / `SUPER_AUTH_PASS` enable Basic auth (defaults dev-friendly: disabled).
- Orchestrators:
  - `ORCH_AUTH_USER` / `ORCH_AUTH_PASS` enable Basic auth.
  - `ORCH_AUTH_ONLY_RUNS=1` protects only `/v1/runs/*`.
  - `ORCH_AUTH_PROTECT_SYSTEM={0|1}` toggles `/system/*` scope.

UI banners and tooltips:

- The `/super` page should show a banner if `SUPER_AUTH_USER` is unset (dev mode). Auth tooltips can be added to orchestrator status badges when available.

Logs and data files (repo-root `.devlogs/`):

- `super-history.json`: last 50 packets for quick replay.
- `super-audit.json`: append-only audit entries per send/escalate/retry.

API routes (Next.js app):

- `GET /api/super/history?limit=` – recent packets
- `POST /api/super/history` – append entry `{target, mode, packet}`
- `DELETE /api/super/history?id=` – remove entry
- `GET /api/super/audit?limit=&mode=&from=&to=` – audit entries
- `POST /api/super/audit/export` – download JSON
- `POST /api/super/task` – send packet and log
- `POST /api/super/task/escalate` – send+escalate and log

SSE (future):

- `/api/sse/super/events` and `/api/sse/super/run` can stream structured events. The UI segmented bar is ready for richer labels.

