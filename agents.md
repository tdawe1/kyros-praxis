# agents.md — Kyros Agent Framework

Kyros coordinates multiple AI and CLI agents to plan, implement, review, and integrate code changes safely. Day-1 favors fast DX (SQLite + in-proc bus) but all key pieces sit behind interfaces so we can swap Postgres/Redis/containers later without rewrites.

## Core roles

| Role                  | Primary responsibilities                                           |
| --------------------- | ------------------------------------------------------------------ |
| Planner               | Break work into small steps, define DoD, budget/complexity signals |
| Implementer (default) | Apply focused diffs (Gemini by default)                            |
| Implementer (deep)    | Hard changes / refactors (Claude Sonnet)                           |
| Critic                | Run gates (lint/type/test/security), enforce DoD                   |
| Integrator            | Merge/rollback, changelog, tag                                     |
| Watchdog              | Reclaim stale leases, re-queue, heal state                         |

> One physical agent may hold multiple roles.

---

## Runtime at a glance

- **Console (Next.js)**: UI and PR runners
- **Orchestrator (FastAPI)**: `/v1/*` runs, state machine, events, validation, budgeting
- **Terminal Daemon (node-pty WS)**: local shell sessions behind `TerminalService` (not Internet-exposed)
- **Storage**: Repositories + EventStore (SQLite file `data/kyros.db` by default)
- **Event bus**: in-process pub/sub (Redis Streams adapter later)
- **Config**: `apps/adk-orchestrator/config/{base,development,production}.yaml`

---

## Contracts (Agent SDK)

### Agent interface

```python
# packages/agent_sdk/contracts.py
from pydantic import BaseModel

class AgentContext(BaseModel):
    task: dict
    tools: list           # ToolSchema instances or proxies
    memory: dict          # injected store adapter
    telemetry: dict
    tenant_id: str | None = None

class AgentBase:
    def capabilities(self) -> list[str]: return []
    async def execute(self, ctx: AgentContext) -> dict:
        raise NotImplementedError
```

### Messages, artifacts (debuggable but safe)

```python
# packages/agent_sdk/protocol/messages.py
from pydantic import BaseModel
from typing import List

class Artifact(BaseModel):
    kind: str    # "diff" | "file" | "note" | "link"
    ref: str     # path or id
    summary: str

class AgentMessage(BaseModel):
    intent: str              # analyze | implement | review | integrate
    confidence: float | None = None
    rationale_summary: str   # short, user-shareable (no raw CoT)
    artifacts: List[Artifact] = []
    next_actions: List[str] = []
```

### Tool protocol & discovery

```python
# packages/agent_sdk/tools/protocol.py
from pydantic import BaseModel
from typing import Any, Dict, List

class ToolExample(BaseModel):
    name: str; input: Dict[str, Any]; output: Dict[str, Any]

class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]   # JSON Schema
    returns: Dict[str, Any]      # JSON Schema
    examples: List[ToolExample] = []

class ToolRegistry:
    def __init__(self): self._tools: dict[str, ToolSchema] = {}
    def register(self, tool: ToolSchema): self._tools[tool.name] = tool
    def get(self, name: str) -> ToolSchema | None: return self._tools.get(name)
    def discover(self, capabilities: List[str]) -> List[ToolSchema]: return list(self._tools.values())
```

### Memory (SQLite default, vector store later)

```python
# packages/agent_sdk/memory/store.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class AgentMemoryStore(ABC):
    @abstractmethod
    async def store_interaction(self, agent_id: str, task_id: str, context: Dict[str,Any], result: Dict[str,Any]): ...
    @abstractmethod
    async def history(self, task_id: str, limit: int=100) -> List[Dict[str,Any]]: ...
```

> A minimal SQLite implementation is provided at `packages/agent_sdk/memory/sqlite_store.py`.

### Sandbox (subprocess now; containers later)

```python
# packages/agent_sdk/sandbox/executor.py
from pydantic import BaseModel

class ExecutionResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

class SandboxExecutor:
    async def execute(self, code:str, language:str, timeout:int=30, mem_mb:int=512) -> ExecutionResult: ...
```

A timeout-limited subprocess implementation ships at `sandbox/subprocess_executor.py`. Containerized profiles can replace it later by keeping this interface.

---

## State & events

- **Tasks** and **leases** live in small JSON documents for local collaboration; authoritative persistence is via repos/EventStore.
- **Leases, not locks**: TTL + heartbeat; stale leases are reclaimable. Keep files small to reduce conflicts.
- **Events** are append-only JSON lines (machine log). Human `logs/log.md` is generated from events. Typical events: `task_claimed`, `file_locked`, `tests_run`, `review_feedback`, `merged`, `error`.

**State write protocol (atomic + optimistic)**

1. Read current file and compute an ETag (sha256).
2. Validate and write to a temp file; `os.replace(temp, target)` atomically swaps.
3. If ETag changed, re-read and retry with backoff.

---

## Workflow orchestration (lightweight DAG)

- Orchestrator executes small DAGs (Plan → Implement → Critic → Integrate), checkpointing after each node.
- Retries with backoff; circuit-break on repeated failure.
- Compensation hooks (e.g., revert branch) can be wired per node.

---

## Validation gates (Critic)

- **Code**: formatter/linter/type checker
- **Tests**: unit + optional integration
- **Security**: secret scan baseline; optional SAST
- **DoD**: enforce acceptance criteria per task

> A minimal validator interface lives in `packages/validation/contracts.py`.

---

## Terminal Daemon & CLI agents

- The daemon is local-only, accessed via `TerminalService` interface (WebSocket implementation in the console later).
- CLI agents (e.g., Claude Code CLI) use a **runner** that proxies stdin/stdout through `TerminalService`, so we can later swap to containers or remote hosts without changing call sites.

---

## Implementer strategy & model routing

- Default implementer uses Gemini; tasks labeled `needs:deep-refactor` or similar trigger Claude Sonnet.
- Strategy considers tenant budgets, recent failure rate, and task complexity.

---

## Security & tenancy

- JWT (or dev header) injects a `TenantContext` with rate limits and model caps.
- **Never** log secrets or raw chain-of-thought; store only `rationale_summary`.
- Rate limit by tenant; budget ceilings enforced before long runs.

---

## How to add a new agent

### 1) Create the agent

```python
# apps/adk-orchestrator/agents/my_impl.py
from packages.agent_sdk.contracts import AgentBase, AgentContext
from packages.agent_sdk.protocol.messages import AgentMessage, Artifact

class MyImplementer(AgentBase):
    def capabilities(self): return ["implement", "python"]

    async def execute(self, ctx: AgentContext) -> dict:
        # use tools if registered (e.g., file edit, git utils)
        # ask router LLM or run sandboxed code as needed
        result = AgentMessage(
            intent="implement",
            rationale_summary="Added function X and unit tests.",
            artifacts=[Artifact(kind="diff", ref="src/foo.py", summary="new function + tests")],
            next_actions=["run tests", "request review"]
        )
        return result.model_dump()
```

### 2) Register tools (optional)

```python
# packages/agent_sdk/tools/register_my_tools.py
from .protocol import ToolSchema, ToolRegistry
registry = ToolRegistry()
registry.register(ToolSchema(
  name="fs.read_text",
  description="Read a UTF-8 file",
  parameters={"type":"object","properties":{"path":{"type":"string"}},"required":["path"]},
  returns={"type":"object","properties":{"text":{"type":"string"}}},
  examples=[]
))
```

### 3) Wire into the orchestrator

- Add to the agent registry used by the workflow node.
- Persist interaction: call `AgentMemoryStore.store_interaction(...)` after each node.
- Emit `agent_started/agent_output/agent_error/agent_completed` events.

### 4) Tests

- Unit-test your agent with a fake ToolRegistry and in-memory memory store.
- Contract test the `/v1` endpoint that triggers your agent (e.g., Schemathesis on `api-specs/orchestrator-v1.yaml`).

---

## Agent workflow (field guide)

1. **Sync & claim** the next `queued` task with satisfied deps. Create branch `feat/<task-id>-slug`.
2. **Lease only** files you will edit; TTL ≈ 15m; heartbeat ~5m. Reclaim stale leases if needed.
3. **Implement in small diffs**; commit frequently with messages like `feat(task-007-01): short summary`.
4. **Request review**; critic runs gates and either `changes_requested` or `approved`.
5. **Integrate**: `approved → merging → done`; update changelog; release leases.

**Task state machine**

```
queued → claimed → in_progress → review → approved → merging → done
            ↘ blocked ↘ failed ↘ abandoned
            ↘ changes_requested → in_progress
```

---

## Configuration

Key knobs (defaults in `config/base.yaml`):

- `agents.sandbox.enabled` / `timeout_seconds` / `memory_limit_mb`
- `agents.memory.history_limit`
- `agents.tools.auto_discover` (=true in dev; use registry whitelist in prod)
- Environment: `MODEL_PLANNER`, `MODEL_IMPL`, `MODEL_DEEP`, `NEXT_PUBLIC_ADK_URL`, plus router base

---

## Testing & CI

- **Unit**: agent logic, memory store, sandbox executor
- **Integration**: orchestrator DAG happy path (SQLite)
- **Contract**: `/v1` OpenAPI with Schemathesis
- **E2E**: click "Run Plan" in Console and assert a run id is returned
- CI must gate on tests + secret scan + lint/type checks

---

## Appendices

### Event names (suggested)

- `task_created`, `task_claimed`, `status_changed`, `file_locked`, `lease_renewed`, `locks_reclaimed`, `tests_run`, `pr_opened`, `review_requested`, `review_feedback`, `approved`, `merged`, `released`, `agent_started`, `agent_output`, `agent_error`, `agent_completed`.

### Collaboration files (dev-friendly)

- `collaboration/state/tasks.json`
- `collaboration/state/locks.json`
- `collaboration/state/agents.json`
- `collaboration/events/events.jsonl`
- `collaboration/logs/log.md` (generated)

> Keep state files small and focused; the authoritative history is the event log.

---

If you want, I can open a PR in `tdawe1/kyros-console` that adds this file and the missing stubs (`agent_sdk`, `validation`, etc.) in a few focused commits.

---

## Cursor Rules & how agents use them

Kyros includes a small, high-signal Cursor ruleset:

- **Project base:** `.cursor/rules/base.mdc`
- **Security/Tenancy:** `.cursor/rules/security-tenancy.mdc`
- **Orchestrator (FastAPI):** `apps/adk-orchestrator/.cursor/rules/fastapi.mdc`
- **Console (Next.js App Router):** `apps/console/.cursor/rules/next-app-router.mdc`
- **Terminal Daemon:** `apps/terminal-daemon/.cursor/rules/daemon-pty.mdc`
- **Final Review Gate:** `.cursor/rules/final-review.mdc`

**How it works:** Cursor auto-attaches rules found under `.cursor/rules` (and nested app folders) when files in those areas are referenced. Keep rules concise; they act as on-disk system prompts for contributors and AI agents.

**Agent usage:**

- **Planner / Implementer:** The app-specific rules auto-attach in Cursor when editing those areas. Follow their patterns and the Security/Tenancy guardrails.
- **Critic:** Use the **Final Review Gate** rule when a PR is labeled `final`. It expects required CI checks to be green and enforces security/tenancy before returning APPROVE/DENY.
- **Integrator:** Ensure Final Review passed (Codex/CodeRabbit checks + our CI). If APPROVE, proceed with merge; if DENY, apply the minimal "required_changes".
