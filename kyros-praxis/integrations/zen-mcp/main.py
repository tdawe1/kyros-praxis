#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Import MCP security module
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_security import create_mcp_security, MCPSecurity


def now_ms() -> int:
    return int(time.time() * 1000)


ROOT = Path(__file__).resolve().parents[2]  # .../kyros-praxis
ZEN_ROOT = Path(os.getenv("ZEN_ROOT", ROOT / "zen"))
STATE_DIR = ZEN_ROOT / "state"
CONTEXT_DIR = ZEN_ROOT / "context"

AGENTS_FILE = STATE_DIR / "agents.json"
SESSIONS_FILE = STATE_DIR / "sessions.json"

# Initialize MCP Security
MCP_SECURITY = create_mcp_security(
    server_name="zen-mcp",
    jwt_secret=os.getenv("MCP_JWT_SECRET"),
    api_keys=os.getenv("ZEN_API_KEYS", "").split(",") if os.getenv("ZEN_API_KEYS") else [],
    allowed_roots=[
        str(ZEN_ROOT),
        str(STATE_DIR),
        str(CONTEXT_DIR),
        "/tmp/zen"  # Allow temporary files
    ],
    authorization_servers=[
        os.getenv("ZEN_AUTH_SERVER", "http://kyros_orchestrator:8000/auth")
    ],
    resource_uri="urn:kyros:mcp:zen"
)


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
    # Validate path to prevent directory traversal
    safe_session_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
    if safe_session_id != session_id:
        raise ValueError(f"Invalid session ID: {session_id}")
    
    file_path = CONTEXT_DIR / f"{safe_session_id}.jsonl"
    
    # Validate against filesystem boundaries
    is_allowed, resolved_path = MCP_SECURITY.validate_filesystem_path(str(file_path))
    if not is_allowed:
        raise PermissionError(f"Access denied to path: {file_path}")
    
    return resolved_path


def send(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def send_error(req_id, code: int, message: str, details: dict = None):
    """Send standardized error response."""
    error_response = MCP_SECURITY.create_error_response(code, message, details)
    if req_id:
        error_response["id"] = req_id
    send(error_response)

def validate_request_auth(headers: dict, method: str = "GET") -> tuple[bool, dict]:
    """Validate request authentication and return auth context."""
    is_authorized, auth_context = MCP_SECURITY.validate_request(headers, method)
    
    if is_authorized:
        MCP_SECURITY.audit_log("auth_success", auth_context)
    else:
        MCP_SECURITY.audit_log("auth_failure", auth_context)
    
    return is_authorized, auth_context


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
    base_capabilities = {
        "tools": {},
        "resources": {},
        "prompts": {},
        "logging": {},
        "sampling": {},
    }
    
    # Enhance with security information
    capabilities = MCP_SECURITY.create_capabilities_response(base_capabilities)
    
    return {
        "serverInfo": {
            "name": "zen-mcp",
            "version": os.getenv("ZEN_MCP_VERSION", "0.1.0"),
            "security": {
                "oauth_resource_server": True,
                "resource_uri": MCP_SECURITY.config.resource_uri,
                "authentication_required": True
            }
        },
        "protocolVersion": os.getenv("MCP_PROTOCOL_VERSION", "2025-06-01"),
        "capabilities": capabilities,
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


def call_tool(name: str, args: Dict[str, Any], auth_context: Dict[str, Any] = None):
    ensure_dirs()
    # Authorization checks for different operations
    write_operations = {"zen/register_agent", "zen/create_session", "zen/add_context", "zen/set_kv", "zen/close_session"}
    if name in write_operations:
        if not auth_context or "write" not in auth_context.get("scopes", []):
            return {
                "ok": False,
                "error": "insufficient_privileges",
                "message": "Write operations require 'write' scope",
                "required_scopes": ["write"]
            }
    
    if name == "zen/register_agent":
        aid = args.get("id") or str(uuid.uuid4())
        agent = {"id": aid}
        if isinstance(args.get("name"), str):
            agent["name"] = args["name"]
        if isinstance(args.get("capabilities"), list):
            agent["capabilities"] = args["capabilities"]
        if isinstance(args.get("metadata"), dict):
            agent["metadata"] = args["metadata"]
        
        # Add audit trail
        agent["created_by"] = auth_context.get("user_id") if auth_context else "unknown"
        
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
        # Validate session access
        session_id = args.get("sessionId")
        if not session_id:
            return {"ok": False, "error": "session_id_required"}
        
        # Add user context to metadata
        metadata = args.get("metadata", {})
        if auth_context:
            metadata["added_by"] = auth_context.get("user_id")
            metadata["auth_type"] = auth_context.get("auth_type")
        
        return append_context(
            sid=session_id,
            role=args.get("role"),
            provider=args.get("provider"),
            content=args.get("content"),
            metadata=metadata,
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
        headers = req.get("headers", {})

        # Special handling for initialize - no auth required for handshake
        if method == "initialize":
            respond(req_id, initialize_result())
            send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
            continue

        # OAuth protected resource metadata endpoint
        if method == "resources/oauth-protected-resource":
            respond(req_id, {"metadata": MCP_SECURITY.get_protected_resource_metadata()})
            continue

        # Authenticate all other requests
        is_authorized, auth_context = validate_request_auth(headers, method)
        if not is_authorized:
            send_error(req_id, 401, "Authentication required", {
                "www_authenticate": f'Bearer realm="zen-mcp"',
                "supported_methods": ["bearer", "api_key"]
            })
            continue

        # Authorized requests
        if method == "tools/list":
            respond(req_id, tools_list())
            continue
            
        if method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            
            try:
                result = call_tool(name, args, auth_context)
                respond(req_id, result)
                
                # Audit log the tool call
                MCP_SECURITY.audit_log("tool_call", auth_context, {
                    "tool_name": name,
                    "arguments": {k: "<redacted>" if k in ["password", "token", "secret"] else v 
                                for k, v in args.items()}
                })
            except (ValueError, PermissionError) as e:
                send_error(req_id, 403, f"Access denied: {str(e)}")
            except Exception as e:
                send_error(req_id, 500, f"Internal error: {str(e)}")
            continue
            
        respond(
            req_id, error={"code": -32601, "message": f"Method not found: {method}"}
        )


if __name__ == "__main__":
    main()
