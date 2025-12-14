Prompt:
  You are my Super Architect + Implementer operating
  headlessly on this repo. Execute the full TODO plan below,
  then perform a holistic project review and advise next
  steps. Work in small, safe diffs (≤200 LOC/PR unless
  necessary), keep logs, and update docs (plan‑sync) with
  every meaningful change.

  Objective

  - Implement every item in docs/todos/super-architect-
  todos.md (Now → Next → Later as feasible).
  - Thoroughly review the project after implementation and
  propose prioritized next steps.

  Operating Rules

  - Small diffs; clear commit messages; keep changes scoped.
  - Update docs/plan-sync (review-plan.md and related docs)
  when behavior changes.
  - Respect security: never commit secrets; keep auth toggles
  defaulting to dev-friendly but document prod hardening.
  - Add/extend tests when touching behavior; keep existing
  style.

  Environment assumptions

  - Dev scripts: scripts/dev/tmux-super-architect.sh (proxy +
  3 orchestrators + inspectors).
  - UI routes: /super, /feed, /settings, /health.
  - Server routes under server/routes.ts.
  - Orchestrators in apps/adk-orchestrator.
  - Logs at .devlogs/*.
  - LiteLLM config in configs/litellm.yaml.

  Implement the TODOs (Now)

  1. Copy cURL button for last packet on /super

  - Add a “Copy cURL” control that renders the cURL for
  either /api/super/task or /api/super/task/escalate using
  the last {target, mode, packet}.
  - Verify: copy to clipboard; manual paste succeeds.
  - Files: client/src/pages/super.tsx (UI); ensure last-sent
  packet is tracked and accessible.

  2. Persist last 50 packets with replay UI

  - Persist sent packets to .devlogs/super-history.json.
  - Add API:
      - GET /api/super/history (returns last 50)
      - POST /api/super/history (append entry)
      - DELETE /api/super/history?id=… (remove entry),
  optional clear.
  - UI on /super:
      - “Recent Packets” dropdown to select/replay; show
  mode/target; one-click Send, one-click Send + Escalate.
  - Verify: persists across reloads; replay updates events/
  timelines.

  3. Enhance SSE timelines per run

  - Add a third/segmented bar where possible (plan/implement/
  critic sections or packet→exec→done with finer segment
  labels).
  - Keep the existing normalized-width logic; label tooltips.
  - Verify: segmented bars render; no layout regressions.

  4. Audit log JSON + API + UI

  - Append high-level audit entries on every packet send/
  escalate/retry to .devlogs/super-audit.json: { ts,
  action, target(s), mode, summary, run_ids (if known),
  hash(payload) }.
  - API:
      - GET /api/super/audit?limit=&mode=&from=&to=
      - Optional: POST /api/super/audit/export (download
  JSON)
  - UI:
      - Add “Audit” tab/panel on /super listing most recent
  entries with filters.
  - Verify: entries appear; filters work; export works.

  5. Link review plan in UI

  - Add a link to docs/review-plan.md in the sidebar (“Review
  Plan”) and a quick link from the /super page header.
  - If rendering markdown is heavy, link to raw text view
  (simple fetch + <pre>) or to file path route if already
  served.
  - Verify: navigates and displays.

  Implement the TODOs (Next, if time permits)

  - Status pings with auth detection per orchestrator (badge
  tooltips show which auth toggles are active).
  - Recent packets: export/import alongside presets (mirror
  endpoints).
  - “Retry failed with packet from history” quick pick.
  - SSE: include packet payload hash in events for
  correlation.

  Implement the TODOs (Later, if feasible)

  - CI jobs for linters/types/tests for server/client/
  orchestrators.
  - Minimal RBAC token for super/delegate endpoints (in
  addition to Basic).
  - File watcher for SSE (reduce tail latency below polling).

  Security & Auth Toggles (document in docs/dev/super-
  architect.md)

  - Server (super/delegate):
      - SUPER_AUTH_USER/SUPER_AUTH_PASS to enable Basic auth
  (already implemented).
  - Orchestrators:
      - ORCH_AUTH_USER/ORCH_AUTH_PASS to enable Basic auth.
      - ORCH_AUTH_ONLY_RUNS=1 to protect only /v1/runs/*.
      - ORCH_AUTH_PROTECT_SYSTEM={0|1} for /system/* scope.
  - Show a banner on /super if SUPER_AUTH_USER is unset
  (already implemented).
  - Add tooltips on orchestrator badges when auth is enabled,
  if possible.

  Verification checklist (add to PR/test notes)

  - /super loads with status badges, presets, recent packets,
  cURL copy, audit tab, review plan link.
  - Sending a packet:
      - Appears in recent packets; audit log updated.
      - Events and timelines update; artifacts load; “Retry
  with last mode” works.
      - “Copy cURL” produces a working command for both Send
  and Send + Escalate.
  - Import/export of presets and (if implemented) recent
  packets.
  - Download logs endpoint works; files match .devlogs.
  - Structured SSE endpoints:
      - /api/sse/super/events (structured),
      - /api/sse/super/run (per-run),
      - (feed is raw tail): /api/sse/super/feed.
  - Auth banners and tooltips: appear/disappear based on env.

  Reporting (headless)

  - For each completed TODO item:
      - List changed files with short rationale.
      - Show example curl/UI steps used to verify.
      - Note risks/rollback and follow-ups.
  - Final holistic review:
      - Summarize current architecture and flows (proxy →
  orchestrators → UI).
      - Identify bottlenecks (latency, logs, auth gaps).
      - Recommend prioritized next steps with rough effort/
  impact:
          - Top 3 engineering tasks
          - Top 3 DX/observability tasks
          - Security hardening plan (production profile)
          - Testing/CI improvements
  - Attach a concise changelog and a “How to Operate” snippet
  (commands to run tmux, visit UI, auth envs).

  Constraints

  - Keep diffs scoped; avoid unrelated refactors.
  - Match existing code style and patterns.
  - Update docs/dev/super-architect.md and docs/review-
  plan.md where behavior meaningfully changes.

  Begin now.
