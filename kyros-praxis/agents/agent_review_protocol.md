# Kyros — Agent Review Protocol (for AI Executors)

This protocol turns the project outline into a repeatable, auditable review workflow that multiple AI agents can run in parallel and hand off between.

---

## Output Contract (single artifact)
- Agents MUST emit one JSON file at `reports/review.json` that validates against `schemas/review_output.schema.json` (included below).
- All proposed code changes go into `recommended_prs` (with optional `patch_commands`).
- For architecture decisions, create Markdown ADRs under `docs/adrs/` using the template in this document.

---

## Phase 0 — Context Discovery (5 minutes, timeboxed)
Collect high-signal context before reviewing. Keep notes terse.

```yaml
phase0:
  dependency_graph: "apps → packages → external"
  integration_points:
    - "Console ↔ Orchestrator (/v1)"
    - "Orchestrator ↔ Terminal Daemon (WS)"
  data_flow:
    - "Console → Orchestrator → Daemon → artifacts/logs → Console"
  missing_expected_files:
    - docker-compose.yml
    - Makefile
    - ADRs
```

> Tip: If an expected file is missing, add a P2 finding and a `recommended_prs` entry that scaffolds it.

---

## Layered Review Architecture (parallelizable)
Explicit layers enable specialization and parallel execution.

```json
{
  "review_layers": {
    "L1_Infrastructure": ["CI/CD", "Build", "Deploy"],
    "L2_Platform": ["Auth", "Tenancy", "SDK"],
    "L3_Services": ["Orchestrator", "Daemon", "Console"],
    "L4_Integration": ["Contracts", "E2E", "APIs"]
  }
}
```

Assign one agent per layer; they only escalate cross-layer risks to L4.

---

## Cross‑Cutting Concern Matrix
For each **component × concern**, rate **Pass (✓)**, **Warn (⚠)**, or **Fail (✗)** and add a one‑line note.

| Component     | Security | Scalability | Observability | Testing |
|---------------|:--------:|:-----------:|:-------------:|:-------:|
| Console       | ✓/✗/⚠    | ✓/✗/⚠       | ✓/✗/⚠        | ✓/✗/⚠   |
| Orchestrator  | ✓/✗/⚠    | ✓/✗/⚠       | ✓/✗/⚠        | ✓/✗/⚠   |
| Terminal Dmn  | ✓/✗/⚠    | ✓/✗/⚠       | ✓/✗/⚠        | ✓/✗/⚠   |

JSON representation (for the report):
```json
{
  "concern_matrix": {
    "Console": {"Security": "pass|warn|fail", "Scalability": "pass|warn|fail", "Observability": "pass|warn|fail", "Testing": "pass|warn|fail"},
    "Orchestrator": {"Security": "pass|warn|fail", "Scalability": "pass|warn|fail", "Observability": "pass|warn|fail", "Testing": "pass|warn|fail"},
    "TerminalDaemon": {"Security": "pass|warn|fail", "Scalability": "pass|warn|fail", "Observability": "pass|warn|fail", "Testing": "pass|warn|fail"}
  }
}
```

---

## Severity‑Based Triage
Replace the single verdict with prioritized buckets.

```json
{
  "verdict": {
    "P0_blockers": [],
    "P1_critical": [],
    "P2_important": [],
    "P3_nice_to_have": []
  }
}
```

- **Gate**: Any P0/P1 MUST block the `final` label.
- Each finding MUST include `confidence` (0–1) and `evidence_quality` (`direct|inferred|assumed`).

Finding shape:
```json
{
  "id": "SEC-001",
  "title": "Missing rate limiting on /v1/runs",
  "layer": "L2_Platform",
  "files": ["apps/adk-orchestrator/main.py"],
  "evidence": "No decorator on route; tests absent.",
  "confidence": 0.95,
  "evidence_quality": "direct",
  "checkpoint": "security",
  "recommended_fix": "Add per-tenant limiter decorator and tests"
}
```

---

## Automated Fix Generation
Augment recommendations with executable patches when safe.

```json
{
  "recommended_prs": [{
    "branch": "fix/ratelimit-orchestrator",
    "title": "feat(orchestrator): per-tenant rate limits",
    "auto_fix_available": true,
    "patch_commands": [
      "pip install slowapi",
      "applypatch scripts/patches/ratelimit_orchestrator.diff"
    ],
    "test_command": "pytest -q && npm -w apps/console test -s"
  }]
}
```

> Agents SHOULD prefer patch files over inline `sed` for multi-line edits.

---

## Progressive Checkpoints
These checkpoints structure execution and reporting.

```yaml
checkpoints:
  - basic_health: "All services start & /healthz OK"
  - integration: "Console ↔ Orchestrator ↔ Daemon round-trip"
  - security: "Auth/tenancy enforced; rate limits on hot paths"
  - production_ready: "Scale/monitor/recover path present"
```

---

## Agent Handoff Protocol
Downstream specialists receive explicit task queues.

```json
{
  "next_agent_tasks": {
    "security_specialist": ["Review bearer auth + tenant threading", "Pen-test public endpoints"],
    "performance_agent": ["Load test /v1/runs/plan", "Profile SQLite hotspots"],
    "documentation_agent": ["Generate OpenAPI + human docs", "Author ADRs for auth & data store"]
  }
}
```

---

## ADR Generation (required for key decisions)
For each major decision, propose an ADR in `docs/adrs/`.

**Template**
```
# ADR-XXX: <Decision>

- Status: proposed
- Date: <YYYY-MM-DD>

## Context
What forces are at play?

## Decision
What architectural choice do we make?

## Consequences
Trade-offs accepted.

## Alternatives
What was considered but rejected?
```

---

## Execution Strategy (multi‑agent)
1. **Discovery** (Phase 0) → share `phase0` notes.
2. **Layered deep‑dives** (L1–L4) in parallel.
3. **Integration** consolidates findings → triage → `recommended_prs`.
4. **Specialist handoff** executes targeted tasks.
5. **QA agent** validates `reports/review.json` against schema and smoke-runs `test_command`s.

---

## Minimal Example Report
```json
{
  "phase0": {"missing_expected_files": ["docker-compose.yml"]},
  "concern_matrix": {"Orchestrator": {"Security": "warn"}},
  "verdict": {
    "P0_blockers": [],
    "P1_critical": [{"id": "SEC-001", "title": "Missing rate limit", "confidence": 0.95, "evidence_quality": "direct"}],
    "P2_important": [],
    "P3_nice_to_have": []
  },
  "recommended_prs": [{
    "branch": "feat/add-rate-limit",
    "title": "feat(orchestrator): add per-tenant rate limits",
    "auto_fix_available": true,
    "patch_commands": ["applypatch scripts/patches/add_rate_limit.diff"],
    "test_command": "pytest -q"
  }]
}
```

---

## Integration Notes for Kyros
- Place this file at `docs/AGENT_REVIEW_PROTOCOL.md`.
- Add JSON schema to `schemas/review_output.schema.json`.
- Update CI: add a job step to validate `reports/review.json` using a JSON Schema validator (e.g., `npx ajv validate -s schemas/review_output.schema.json -d reports/review.json`).
- Put a slim rule file into `.cursor/rules/agent-review.md` that embeds **Phase 0**, **layers**, **triage**, **matrix**, **checkpoints**, and **output path**.
