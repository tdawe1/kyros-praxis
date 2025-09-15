#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple


def now_ms() -> int:
    return int(time.time() * 1000)


ROOT = Path(__file__).resolve().parents[2]  # .../kyros-praxis
ZEN_ROOT = Path(os.getenv("ZEN_ROOT", ROOT / "zen"))
STATE_DIR = ZEN_ROOT / "state"
CONTEXT_DIR = ZEN_ROOT / "context"

AGENTS_FILE = STATE_DIR / "agents.json"
SESSIONS_FILE = STATE_DIR / "sessions.json"


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    if not AGENTS_FILE.exists():
        AGENTS_FILE.write_text(json.dumps([], indent=2) + "\n", encoding="utf-8")
    if not SESSIONS_FILE.exists():
        SESSIONS_FILE.write_text(
            json.dumps({"sessions": []}, indent=2) + "\n", encoding="utf-8"
        )


def canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def etag(obj: Any) -> str:
    return hashlib.sha256(canon(obj).encode("utf-8")).hexdigest()


def read_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8") or "null")
    return data, etag(data)


def write_json_atomic(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def context_file(session_id: str) -> Path:
    return CONTEXT_DIR / f"{session_id}.jsonl"


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


def initialize_result():
    return {
        "serverInfo": {
            "name": "zen-mcp",
            "version": os.getenv("ZEN_MCP_VERSION", "0.1.0"),
        },
        "protocolVersion": os.getenv("MCP_PROTOCOL_VERSION", "1.0"),
        "capabilities": {
            "tools": {},
            "resources": {},
            "prompts": {},
            "logging": {},
            "sampling": {},
        },
    }


def tools_list():
    return {
        "tools": [
            {
                "name": "zen/register_agent",
                "description": "Register or update an agent (id optional)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "capabilities": {"type": "array", "items": {"type": "string"}},
                        "metadata": {"type": "object"},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "zen/list_agents",
                "description": "List registered agents",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
            {
                "name": "zen/create_session",
                "description": "Create a session spanning multiple agents/providers",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agentIds": {"type": "array", "items": {"type": "string"}},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "ttlMs": {"type": "number"},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "zen/add_context",
                "description": "Append a context record to a session (role/provider/content/metadata)",
                "inputSchema": {
                    "type": "object",
                    "required": ["sessionId", "role", "content"],
                    "properties": {
                        "sessionId": {"type": "string"},
                        "role": {"type": "string"},
                        "provider": {"type": "string"},
                        "content": {},
                        "metadata": {"type": "object"},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "zen/get_context",
                "description": "Read session context with optional limit/sinceTs",
                "inputSchema": {
                    "type": "object",
                    "required": ["sessionId"],
                    "properties": {
                        "sessionId": {"type": "string"},
                        "limit": {"type": "number"},
                        "sinceTs": {"type": "number"},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "zen/set_kv",
                "description": "Set a key/value on a session",
                "inputSchema": {
                    "type": "object",
                    "required": ["sessionId", "key", "value"],
                    "properties": {
                        "sessionId": {"type": "string"},
                        "key": {"type": "string"},
                        "value": {},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "zen/get_kv",
                "description": "Get a key/value from a session",
                "inputSchema": {
                    "type": "object",
                    "required": ["sessionId", "key"],
                    "properties": {
                        "sessionId": {"type": "string"},
                        "key": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
            {
                "name": "zen/close_session",
                "description": "Close a session",
                "inputSchema": {
                    "type": "object",
                    "required": ["sessionId"],
                    "properties": {"sessionId": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
        ]
    }


def upsert_agent(agent: Dict[str, Any]) -> Dict[str, Any]:
    agents, _ = read_json(AGENTS_FILE)
    if not isinstance(agents, list):
        agents = []
    existing = None
    for a in agents:
        if a.get("id") == agent["id"]:
            existing = a
            break
    now = now_ms()
    if existing:
        existing.update({k: v for k, v in agent.items() if k != "id"})
        existing["updatedAt"] = now
    else:
        agent.setdefault("name", agent["id"])  # default name
        agent["createdAt"] = now
        agent["updatedAt"] = now
        agents.append(agent)
    write_json_atomic(AGENTS_FILE, agents)
    return agent


def create_session(
    agent_ids: List[str] | None, tags: List[str] | None, ttl_ms: int | None
) -> Dict[str, Any]:
    sessions_doc, _ = read_json(SESSIONS_FILE)
    if not isinstance(sessions_doc, dict) or not isinstance(
        sessions_doc.get("sessions"), list
    ):
        sessions_doc = {"sessions": []}
    s_id = str(uuid.uuid4())
    now = now_ms()
    session = {
        "id": s_id,
        "agentIds": agent_ids or [],
        "tags": tags or [],
        "kv": {},
        "status": "open",
        "ttlMs": int(ttl_ms) if ttl_ms else None,
        "createdAt": now,
        "updatedAt": now,
    }
    sessions_doc["sessions"].append(session)
    write_json_atomic(SESSIONS_FILE, sessions_doc)
    # initialize context file
    cf = context_file(s_id)
    if not cf.exists():
        cf.write_text("", encoding="utf-8")
    return session


def get_session(sid: str) -> Tuple[Dict[str, Any] | None, Dict[str, Any]]:
    doc, _ = read_json(SESSIONS_FILE)
    if not isinstance(doc, dict):
        doc = {"sessions": []}
    for s in doc.get("sessions", []):
        if s.get("id") == sid:
            return s, doc
    return None, doc


def append_context(
    sid: str,
    role: str,
    provider: str | None,
    content: Any,
    metadata: Dict[str, Any] | None,
) -> Dict[str, Any]:
    s, doc = get_session(sid)
    if not s:
        return {"ok": False, "error": "session_not_found"}
    if s.get("status") == "closed":
        return {"ok": False, "error": "session_closed"}
    rec = {
        "ts": now_ms(),
        "role": role,
        "provider": provider,
        "content": content,
    }
    if isinstance(metadata, dict):
        rec["metadata"] = metadata
    cf = context_file(sid)
    with cf.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    s["updatedAt"] = now_ms()
    write_json_atomic(SESSIONS_FILE, doc)
    return {"ok": True, "record": rec}


def read_context(sid: str, limit: int | None, since_ts: int | None) -> Dict[str, Any]:
    cf = context_file(sid)
    if not cf.exists():
        return {"ok": True, "items": []}
    items: List[Dict[str, Any]] = []
    with cf.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if since_ts and isinstance(obj.get("ts"), int) and obj["ts"] <= since_ts:
                continue
            items.append(obj)
    if limit:
        items = items[-int(limit) :]
    return {"ok": True, "items": items}


def set_kv(sid: str, key: str, value: Any) -> Dict[str, Any]:
    s, doc = get_session(sid)
    if not s:
        return {"ok": False, "error": "session_not_found"}
    s.setdefault("kv", {})[key] = value
    s["updatedAt"] = now_ms()
    write_json_atomic(SESSIONS_FILE, doc)
    return {"ok": True}


def get_kv(sid: str, key: str) -> Dict[str, Any]:
    s, _ = get_session(sid)
    if not s:
        return {"ok": False, "error": "session_not_found"}
    return {"ok": True, "value": s.get("kv", {}).get(key)}


def close_session(sid: str) -> Dict[str, Any]:
    s, doc = get_session(sid)
    if not s:
        return {"ok": False, "error": "session_not_found"}
    s["status"] = "closed"
    s["updatedAt"] = now_ms()
    write_json_atomic(SESSIONS_FILE, doc)
    return {"ok": True}


def call_tool(name: str, args: Dict[str, Any]):
    ensure_dirs()
    if name == "zen/register_agent":
        aid = args.get("id") or str(uuid.uuid4())
        agent = {"id": aid}
        if isinstance(args.get("name"), str):
            agent["name"] = args["name"]
        if isinstance(args.get("capabilities"), list):
            agent["capabilities"] = args["capabilities"]
        if isinstance(args.get("metadata"), dict):
            agent["metadata"] = args["metadata"]
        upsert_agent(agent)
        return {"ok": True, "agent": agent}

    if name == "zen/list_agents":
        agents, tag = read_json(AGENTS_FILE)
        if not isinstance(agents, list):
            agents = []
        return {"ok": True, "agents": agents, "etag": tag}

    if name == "zen/create_session":
        session = create_session(
            agent_ids=args.get("agentIds") or [],
            tags=args.get("tags") or [],
            ttl_ms=args.get("ttlMs"),
        )
        return {"ok": True, "session": session}

    if name == "zen/add_context":
        return append_context(
            sid=args.get("sessionId"),
            role=args.get("role"),
            provider=args.get("provider"),
            content=args.get("content"),
            metadata=args.get("metadata"),
        )

    if name == "zen/get_context":
        return read_context(
            sid=args.get("sessionId"),
            limit=args.get("limit"),
            since_ts=args.get("sinceTs"),
        )

    if name == "zen/set_kv":
        return set_kv(args.get("sessionId"), args.get("key"), args.get("value"))

    if name == "zen/get_kv":
        return get_kv(args.get("sessionId"), args.get("key"))

    if name == "zen/close_session":
        return close_session(args.get("sessionId"))

    return {"ok": False, "error": f"unknown_tool: {name}"}


def main():
    ensure_dirs()
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
            respond(req_id, initialize_result())
            send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
            continue
        if method == "tools/list":
            respond(req_id, tools_list())
            continue
        if method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            respond(req_id, call_tool(name, args))
            continue
        respond(
            req_id, error={"code": -32601, "message": f"Method not found: {method}"}
        )


if __name__ == "__main__":
    main()
