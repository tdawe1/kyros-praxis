# agents.md — Codex Init Guide (Kyros Praxis)

**Goal:** bring Codex agents online with MCP, create the project bootstrap scripts/files, and operate within Kyros’ workflow (ETag/If-Match, Kanban, PR rules). See the configured MCP servers in `mcp.json`.&#x20;
**Backlog & priorities** (TDS-IDs) live in the deduped tasks list.&#x20;
**Workflow & gates** (Kanban, ETag, leases, CI/PR) are defined here. &#x20;
**Why this doc:** our last sync showed code changed but no tasks moved—this fixes that with automation and strict state updates.&#x20;

---

## TL;DR (do these first)

```bash
# 0) Work on a branch
git checkout -b chore/TDS-0-codex-init

# 1) Export any keys you have (optional ones are commented)
export ZEN_API_KEY=""                 # optional, for zen MCP fan-out
export KYROS_CONFIG=""                # kyros MCP if used
export COLLAB_CONFIG=""               # enable kyros-collab later (optional)
export GITHUB_PERSONAL_ACCESS_TOKEN=""# read-only GH MCP
export EXA_API_KEY=""                 # web search MCP (optional)
export NOTION_TOKEN=""                # notion MCP (optional)
export QDRANT_API_KEY=""              # vector MCP (optional)

# 2) Start codex with MCP (point to repo’s mcp.json)
# (Use your codex-CLI invocation and pass MCP config/path if required by your setup.)
codex --mcp-config ./mcp.json
```

> MCP servers and commands are declared in `mcp.json`. Don’t enable `kyros-collab` until `COLLAB_CONFIG` is set.&#x20;

---

## Operating rules (read once)

- **State is sacred.** Update `collaboration/state/*.json` only via the provided helper with **If-Match** ETags; append events only.&#x20;
- **Kanban flow:** `queued → claimed → in_progress → review → approved → merging → done` with events at each transition.&#x20;
- **Version control:** branch naming `feat/<TDS-###>-slug`, conventional commits, PR template, protected main.&#x20;
- **Scope & priorities:** focus P0 items (e.g., **TDS-1 Collab API with ETag+SSE**, **TDS-3 Jobs slice**, **TDS-4 Playwright flows**).&#x20;

---

## Step 1 — Bring up MCP for Codex

Codex agents rely on MCP servers in `mcp.json`. Validate the essentials:

- **filesystem** (repo path), **git (RO)**, **time**, **memory** — always on.
- **playwright/puppeteer** — for test/QA.
- **zen** — optional fan-out for tiny code patches (≤50 LOC).
- Disable/enable others as your keys/envs allow.&#x20;

**Smoke check** (adjust to your CLI flavor):

```bash
# List running MCP servers (example; use your CLI’s equivalent)
# codex mcp status
# or run a trivial filesystem read to confirm:
# codex mcp call filesystem listDir {"path": "."}
```

---

## Step 2 — Create the starter files (exact content below)

These scripts make progress visible and safe: **PR gate**, **ETag state updates**, **Codex↔Kilo bridge**, **request poller**, **usage tracking**. Commit them in this PR.

### 2.1 Minimal PR gate

`scripts/pr_gate_minimal.py`

```python
#!/usr/bin/env python3
import subprocess, sys

def check_tests() -> bool:
    r = subprocess.run(["pytest", "-q"])
    if r.returncode == 0:
        return True
    if r.returncode == 5:
        print("⚠️  No tests collected (Day-1 warning).")
        return True
    return False

def warn_large_staged_diff() -> None:
    r = subprocess.run(["git", "diff", "--cached", "--stat"], capture_output=True, text=True)
    files = [ln for ln in r.stdout.strip().splitlines() if "|" in ln]
    if len(files) > 20:
        print(f"⚠️  Large staged diff: {len(files)} files")

if __name__ == "__main__":
    if not check_tests():
        print("❌ Tests failed"); sys.exit(1)
    warn_large_staged_diff()
    print("✅ Ready for commit")
```

### 2.2 ETag-aware state updates (Kanban)

`scripts/state_update.py`

```python
#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path

TASKS = Path("collaboration/state/tasks.json")

def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()

def etag_for(obj) -> str:
    import hashlib as _h; return _h.sha256(canonical(obj)).hexdigest()

def load_tasks():
    data = json.loads(TASKS.read_text())
    return data, etag_for(data)

def save_tasks(data):
    TASKS.write_text(json.dumps(data, indent=2))
    return etag_for(data)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("task_id"); p.add_argument("new_status")
    p.add_argument("--if-match", default=None)
    a = p.parse_args()

    data, current = load_tasks()
    if a.if_match and a.if_match != current:
        raise SystemExit(f"412 Precondition Failed: ETag mismatch (have {current})")

    for t in data:
        if t.get("id") == a.task_id:
            t["status"] = a.new_status; break
    else:
        raise SystemExit(f"Task {a.task_id} not found")

    new_tag = save_tasks(data)
    print(f"OK {a.task_id} → {a.new_status}; ETag: {new_tag}")
```

### 2.3 Codex → Kilo bridge (file-drop requests)

`scripts/agent_bridge.py`

```python
#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

REQ_DIR = Path("collaboration/requests"); REQ_DIR.mkdir(parents=True, exist_ok=True)

def request_kilo_task(task_type: str, payload: dict) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    f = REQ_DIR / f"{task_type}_{ts}.json"
    f.write_text(json.dumps({"from":"codex-cli","to":"kilo","task":task_type,"payload":payload,"ts":ts}))
    return f

if __name__ == "__main__":
    path = request_kilo_task("plan_jobs_api", {"task_id": "TDS-3"})
    print(f"Wrote {path}")
```

### 2.4 Kilo request poller (Orchestrator side)

`scripts/request_poller.py`

```python
#!/usr/bin/env python3
import json
from pathlib import Path

REQ_DIR = Path("collaboration/requests")
EVT = Path("collaboration/events/events.jsonl"); EVT.parent.mkdir(parents=True, exist_ok=True)

def main():
    for p in sorted(REQ_DIR.glob("*.json")):
        req = json.loads(p.read_text())
        EVT.open("a").write(json.dumps({"ts":req["ts"],"event":"bridge_request","payload":req})+"\n")
        p.unlink()
    print("OK: polled")

if __name__ == "__main__":
    main()
```

### 2.5 Usage/cost metering (log locally)

`scripts/track_usage.py`

```python
#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

LOG = Path("collaboration/usage.jsonl")

def log_api_call(model: str, tokens: int, cost: float) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.open("a").write(json.dumps({
        "timestamp": datetime.utcnow().isoformat()+"Z",
        "model": model, "tokens": tokens, "cost": cost
    })+"\n")

if __name__ == "__main__":
    log_api_call("openrouter/sonoma-sky-alpha", 1200, 0.0)
    print("OK: logged")
```

**Make them executable & commit:**

```bash
chmod +x scripts/*.py
git add scripts/*.py
python scripts/pr_gate_minimal.py
git commit -m "chore(TDS-0): add MCP bootstrap scripts for codex init"
```

---

## Step 3 — Work within the workflow (what to do next)

1. **Claim a task** (P0 first, e.g., TDS-1 or TDS-3). Update state with ETag:

```bash
# read current ETag
ETAG=$(python - <<'PY'
import json,hashlib,sys; d=json.load(open("collaboration/state/tasks.json"))
print(hashlib.sha256(json.dumps(d,sort_keys=True,separators=(",",":")).encode()).hexdigest())
PY
)
python scripts/state_update.py TDS-1 in_progress --if-match "$ETAG"
```

2. **Follow the 7-phase flow** (comprehend → decompose → implement → critique → review → converge → finalize). &#x20;

3. **Branching/PR rules**

   - Create `feat/TDS-###-slug`, conventional commits, PR template, CI green required.&#x20;

4. **Run the minimal gate before each commit**

   - `python scripts/pr_gate_minimal.py` (accepts “no tests” only during Day-1 bootstrap).

5. **Emit events**

   - Append JSONL entries to `collaboration/events/events.jsonl` for claim/progress/review.

---

## Step 4 — Model usage (for Codex team)

- Primary implementation model: **OpenAI (business) via codex-CLI**.
- Medium complexity: **GLM** (if routed through Kilo/Zen).
- Tiny patch fan-out (≤50 LOC): **zen MCP**. Do **not** use Zen for multi-file refactors.&#x20;

Kilo’s free models (e.g., Sonoma) are used by the other group for planning/orchestration/review; Codex focuses on **coding** and communicates via the **requests folder** and **state_update**.

---

## Step 5 — First two concrete tasks for Codex

- **TDS-1 (P0):** prepare the collab “steel thread” (at least `/healthz` or `POST /collab/tasks` w/o ETag), plus events on transitions.&#x20;
- **TDS-3 (P0):** stub Jobs vertical slice (model + one endpoint + unit test), keep diffs small; coordinate with Architect via `scripts/agent_bridge.py`.&#x20;

Use the Kanban, ETag writes, and PR rules above; this prevents the prior “work but no progress” issue.&#x20;

---

### Appendix — Useful references

- MCP servers and commands: `mcp.json`.&#x20;
- Workflow summary (Kanban, ETag/If-Match, leases): `docs/Workflow Summary.md`.&#x20;
- Multi-agent detailed guide: `docs/Multi-Agent Development Workflow in Kyro.md`.&#x20;
- Comprehensive workflow summary: `docs/# Comprehensive Summary of Multi-Agent D.md`.&#x20;
- Tasks/priorities (TDS-IDs): `tasks_deduped.md`.&#x20;
- Version control & PR rules: `docs/version-control.md`.&#x20;
- Last sync status: `docs/agent-sync.md` (“no completed tasks” finding).&#x20;

Great question — those defaults are a bit “open-floodgate.” They’ll inflate tokens and slow the agents, especially when GLM is the paid workhorse. Here’s a crisp set of **global defaults** and **mode-specific overrides** that match our plan (Sonoma for planning/orchestration/review; GLM for precise code), plus a **.kilocodeignore** you should add.

---

## Quick verdict

- Current values (Open tabs=20, Workspace files=200, Always read entire file, Condense at 100%) are **too generous** → higher token use, more latency, and noisier context.
- We want **tight, intentional context** and **early condensation** so Sonoma stays free/fast and GLM is used only when necessary.

---

## Global defaults (set once)

Use these as the **Global Default (all profiles)** in Kilo.

- **Open tabs context limit:** **10**
  Keeps focus on the currently active slice.

- **Workspace files context limit:** **60**
  Enough for our hot files without dragging the whole repo in.

- **Concurrent file reads limit:** **3**
  Reduces I/O spikes and racey diagnostics.

- **File read auto-truncate threshold:** **250 lines**
  **Uncheck** “Always read entire file”. The agent can request exact ranges when needed.

- **Allow very large file reads:** **Off**
  Prevents accidental token bombs (snapshots, lockfiles).

- **Show .kilocodeignore’d files in lists/searches:** **Off**
  Hide them completely to reduce noise.

- **Automatically include diagnostics in context:** **On**
  But cap messages (below).

- **Maximum diagnostic messages:** **20**
  Prioritize errors over warnings.

- **Delay after writes:** **500–600 ms**
  600 ms is fine; 500 ms if you want a snappier loop.

- **Automatically trigger intelligent context condensing:** **On**
  **Condensing Trigger Threshold:** **70 %** (global)
  This forces earlier summarization and keeps GLM calls cheap.

---

## Per-mode overrides (optional but recommended)

### Architect (Sonoma, planning)

- Open tabs: **12**
- Workspace files: **80**
- Condense threshold: **80 %** (keeps more spec context)
- Diagnostics in context: **Off** (architect doesn’t need lint spam)

### Orchestrator (Sonoma, routing/state)

- Open tabs: **8**
- Workspace files: **40**
- Condense threshold: **70 %**
- Diagnostics: **Off**
- Tip: Pin **collaboration/state/** and **docs/** as preferred read targets.

### Implementer (GLM for code)

- Open tabs: **8–10**
- Workspace files: **50**
- Condense threshold: **60 %** (condense earlier to save GLM tokens)
- Diagnostics: **On**, max **20**

### Critic (Sonoma, low-temp)

- Open tabs: **8**
- Workspace files: **40**
- Condense threshold: **70 %**
- Diagnostics: **On**, max **20**

---

## Add this `.kilocodeignore` (at repo root)

This keeps giant/irrelevant files out of context and lists.

```
# build artifacts & caches
**/node_modules/
**/.next/
**/dist/
**/build/
**/.turbo/
**/.vite/
**/.pytest_cache/
**/__pycache__/
**/.ruff_cache/
**/.mypy_cache/

# env & vcs
.env*
.git/
**/*.lock
**/package-lock.json
**/pnpm-lock.yaml
**/yarn.lock

# data & snapshots
**/coverage/
**/playwright-report/
**/*.snap
**/*.min.*
**/*.map
**/*.generated.*

# images & binaries
**/*.png
**/*.jpg
**/*.jpeg
**/*.gif
**/*.pdf
**/*.mp4
```

> If you need images/docs for a specific task, unignore just those paths temporarily.

---

## “Hot file” shortlist (seed context manually when starting a task)

Pin these first to keep the agent grounded in our steel-thread:

- **Backend:** `services/orchestrator/core/settings.py`, `db/session.py`, `main.py`, `routers/*`, `tests/**`
- **Frontend:** `services/console/app/**`, `src/providers/**`, `src/lib/**`, `tests/**`
- **Workflow & state:** `docs/backend-current-plan.md`, `docs/frontend-current-plan.md`, `scripts/pr_gate_minimal.py`, `scripts/state_update.py`, `collaboration/state/tasks.json`

## Why this setup works

- **Earlier condensation** + **smaller file cohorts** keeps Sonoma responses focused and **GLM costs low**.
- **Diagnostics capped** avoids drowning the model in lint noise.
- **.kilocodeignore** prevents accidental 1k-line lockfiles/images from entering the window.
- **Per-mode tweaks** mirror our operating model: Architect holds more prose context; Implementer condenses earlier and uses diagnostics; Orchestrator remains lean.

If you want, I can produce a tiny **mode profile JSON** you can import in Kilo to apply these per-mode overrides automatically.
