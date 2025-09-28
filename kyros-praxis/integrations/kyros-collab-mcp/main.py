#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(__file__).resolve().parents[2]  # .../kyros-praxis
COLLAB_ROOT = Path(os.getenv("COLLAB_ROOT", ROOT / "collaboration"))
STATE_DIR = COLLAB_ROOT / "state"
EVENTS_FILE = COLLAB_ROOT / "events" / "events.jsonl"
TASKS_FILE = STATE_DIR / "tasks.json"
LOCKS_FILE = STATE_DIR / "locks.json"
AGENTS_FILE = STATE_DIR / "agents.json"


def _ensure_files():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (COLLAB_ROOT / "events").mkdir(parents=True, exist_ok=True)
    (COLLAB_ROOT / "logs").mkdir(parents=True, exist_ok=True)
    for p, default in [
        (TASKS_FILE, {"meta": {"seeded": True}, "tasks": []}),
        (LOCKS_FILE, []),
        (AGENTS_FILE, []),
    ]:
        if not p.exists():
            p.write_text(json.dumps(default, indent=2) + "\n", encoding="utf-8")
    if not EVENTS_FILE.exists():
        EVENTS_FILE.write_text("\n", encoding="utf-8")


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _etag(obj: Any) -> str:
    return hashlib.sha256(_canon(obj).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> Tuple[Any, str]:
    data = json.loads(path.read_text(encoding="utf-8") or "null")
    return data, _etag(data)


def _write_json_atomic(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _append_event(event: Dict[str, Any]) -> None:
    event = {**event, "ts": int(time.time())}
    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def send(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def respond(req_id, result=None, error=None):
    if error is not None:
        send({"jsonrpc": "2.0", "id": req_id, "error": error})
    else:
        send(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result if result is not None else {},
            }
        )


def handle_tools_list():
    return {
        "tools": [
            {
                "name": "collab/get_state",
                "description": "Return tasks, locks, agents with etags",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
            {
                "name": "collab/patch_task",
                "description": "Patch a task by id with optimistic concurrency via ifMatch (etag)",
                "inputSchema": {
                    "type": "object",
                    "required": ["id", "patch", "ifMatch"],
                    "properties": {
                        "id": {"type": "string"},
                        "patch": {"type": "object"},
                        "ifMatch": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "collab/acquire_lease",
                "description": "Acquire a lease on a resource id for ttlMs (default 300000)",
                "inputSchema": {
                    "type": "object",
                    "required": ["resourceId", "agentId"],
                    "properties": {
                        "resourceId": {"type": "string"},
                        "agentId": {"type": "string"},
                        "ttlMs": {"type": "number"},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "collab/release_lease",
                "description": "Release a lease for resourceId held by agentId",
                "inputSchema": {
                    "type": "object",
                    "required": ["resourceId", "agentId"],
                    "properties": {
                        "resourceId": {"type": "string"},
                        "agentId": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "collab/emit_event",
                "description": "Append an event to collaboration/events/events.jsonl",
                "inputSchema": {
                    "type": "object",
                    "required": ["event", "actor"],
                    "properties": {
                        "event": {"type": "string"},
                        "actor": {"type": "string"},
                        "target": {"type": "string"},
                        "details": {"type": "object"},
                    },
                    "additionalProperties": False,
                },
            },
        ]
    }


def call_tool(name: str, args: Dict[str, Any]):
    _ensure_files()

    if name == "collab/get_state":
        tasks, tasks_tag = _read_json(TASKS_FILE)
        locks, locks_tag = _read_json(LOCKS_FILE)
        agents, agents_tag = _read_json(AGENTS_FILE)
        return {
            "ok": True,
            "ts": int(time.time()),
            "tasks": {"etag": tasks_tag, "data": tasks},
            "locks": {"etag": locks_tag, "data": locks},
            "agents": {"etag": agents_tag, "data": agents},
        }

    if name == "collab/patch_task":
        task_id = args.get("id")
        patch = args.get("patch") or {}
        if_match = args.get("ifMatch")
        if not task_id or not isinstance(patch, dict) or not if_match:
            return {"ok": False, "error": "invalid_arguments"}
        tasks, etag = _read_json(TASKS_FILE)
        if if_match != etag:
            return {"ok": False, "error": "precondition_failed", "etag": etag}
        lst = tasks.get("tasks") if isinstance(tasks, dict) else []
        found = False
        for t in lst:
            if t.get("id") == task_id:
                t.update(patch)
                found = True
                break
        if not found:
            return {"ok": False, "error": "not_found"}
        _write_json_atomic(TASKS_FILE, tasks)
        tasks2, etag2 = _read_json(TASKS_FILE)
        _append_event(
            {
                "event": "task_patched",
                "actor": "kyros_collab_mcp",
                "target": task_id,
                "details": {"patch": patch},
            }
        )
        return {"ok": True, "etag": etag2, "tasks": tasks2}

    if name == "collab/acquire_lease":
        resource_id = args.get("resourceId")
        agent_id = args.get("agentId")
        ttl_ms = int(args.get("ttlMs") or 300_000)
        now = int(time.time() * 1000)
        locks, _ = _read_json(LOCKS_FILE)
        if not isinstance(locks, list):
            locks = []
        # Clean expired and check existing
        locks = [lock for lock in locks if int(lock.get("expiresAt", 0)) > now]
        for lock in locks:
            if lock.get("resourceId") == resource_id and int(lock.get("expiresAt", 0)) > now:
                return {
                    "ok": False,
                    "error": "already_locked",
                    "heldBy": lock.get("agentId"),
                    "expiresAt": lock.get("expiresAt"),
                }
        lock = {
            "resourceId": resource_id,
            "agentId": agent_id,
            "expiresAt": now + ttl_ms,
        }
        locks.append(lock)
        _write_json_atomic(LOCKS_FILE, locks)
        _append_event(
            {
                "event": "lease_acquired",
                "actor": agent_id,
                "target": resource_id,
                "details": {"ttlMs": ttl_ms},
            }
        )
        return {"ok": True, "lock": lock}

    if name == "collab/release_lease":
        resource_id = args.get("resourceId")
        agent_id = args.get("agentId")
        locks, _ = _read_json(LOCKS_FILE)
        if not isinstance(locks, list):
            locks = []
        new_locks = [
            lock
            for lock in locks
            if not (lock.get("resourceId") == resource_id and lock.get("agentId") == agent_id)
        ]
        _write_json_atomic(LOCKS_FILE, new_locks)
        _append_event(
            {"event": "lease_released", "actor": agent_id, "target": resource_id}
        )
        return {"ok": True}

    if name == "collab/emit_event":
        event = {
            "event": args.get("event"),
            "actor": args.get("actor"),
        }
        if args.get("target"):
            event["target"] = args.get("target")
        if isinstance(args.get("details"), dict):
            event["details"] = args.get("details")
        _append_event(event)
        return {"ok": True}

    return {"ok": False, "error": f"unknown_tool: {name}"}


def mcp_initialize_result():
    return {
        "serverInfo": {"name": "kyros-collab-mcp", "version": "0.1.0"},
        "protocolVersion": os.getenv("MCP_PROTOCOL_VERSION", "1.0"),
        "capabilities": {
            "tools": {},
            "resources": {},
            "prompts": {},
            "logging": {},
            "sampling": {},
        },
    }


def main():
    _ensure_files()
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            send(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"parse error: {e}"},
                }
            )
            continue
        method = req.get("method")
        req_id = req.get("id")

        if method == "initialize":
            respond(req_id, mcp_initialize_result())
            send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
            continue

        if method == "tools/list":
            respond(req_id, handle_tools_list())
            continue

        if method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            arguments = params.get("arguments") or {}
            result = call_tool(name, arguments)
            respond(req_id, result)
            continue

        respond(
            req_id, error={"code": -32601, "message": f"Method not found: {method}"}
        )


if __name__ == "__main__":
    main()
