import json
import os
import sys
import time
import urllib.error
import urllib.request

# Basic env wiring for Kyros backends this MCP server might bridge
API_BASE = os.getenv("KYROS_API_BASE", "http://kyros_orchestrator:8000")
REG_URL = os.getenv("KYROS_REGISTRY_URL", "http://kyros_registry:9000")
DAEMON_URL = os.getenv("KYROS_DAEMON_URL", "ws://kyros_daemon:8080/ws")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
TOOLS = [
    t.strip()
    for t in os.getenv("KYROS_MCP_TOOLS", "runs,registry,memory,terminal").split(",")
    if t.strip()
]
SERVER_NAME = os.getenv("KYROS_MCP_NAME", "kyros-mcp")
SERVER_VERSION = os.getenv("KYROS_MCP_VERSION", "0.0.1")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")


def send(obj: dict) -> None:
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


def mcp_initialize_result():
    # Minimal MCP initialize payload. Some clients only require `capabilities` to exist.
    return {
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        # Keep protocolVersion loose to avoid strict mismatches; adjust if your client requires a specific value.
        "protocolVersion": os.getenv("MCP_PROTOCOL_VERSION", "1.0"),
        # Advertise empty capabilities to satisfy handshake; flesh out as tools/resources are implemented.
        "capabilities": {
            # Common sections (empty objects are acceptable for many clients during handshake)
            "tools": {},
            "resources": {},
            "prompts": {},
            "sampling": {},
            "logging": {},
        },
    }


def list_tools_result():
    # Expose stub tool list derived from env; real servers should provide inputSchema for each tool.
    tools = [
        {
            "name": f"kyros/{t}",
            "description": f"Kyros tool: {t}",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": True,
            },
        }
        for t in TOOLS
    ]
    return {"tools": tools}


def call_tool(name: str, args: dict | None):
    args = args or {}
    # Generic stub implementation: allow a simple connectivity check and
    # provide a structured not_implemented response otherwise.
    action = str(args.get("action", "")).lower()
    ping = bool(args.get("ping")) or action in {"ping", "check"}

    if ping:
        return {
            "ok": True,
            "ts": int(time.time()),
            "tool": name,
            "api_base": API_BASE,
            "registry": REG_URL,
            "daemon": DAEMON_URL,
            "qdrant": QDRANT_URL,
            "tools": TOOLS,
        }

    # Minimal real implementations for common Kyros backends.
    # Helper: simple GET with urllib to avoid extra deps
    def _http_get(url: str, headers: dict | None = None, timeout: int = 3):
        req = urllib.request.Request(url, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.getcode()
                body = resp.read()
                try:
                    data = json.loads(body.decode("utf-8")) if body else None
                except Exception:
                    data = body.decode("utf-8", errors="replace")
                return True, status, data
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
            except Exception:
                err_json = {"message": err_body or str(e)}
            return False, e.code, err_json
        except Exception as e:
            return False, 0, {"error": str(e)}

    # Orchestrator health checks via kyros/runs tool
    if name == "kyros/runs":
        act = action or "health"
        if act in {"health", "check"}:
            ok, status, data = _http_get(API_BASE.rstrip("/") + "/health")
            return {"ok": ok, "status": status, "data": data}
        if act in {"healthz", "db"}:
            ok, status, data = _http_get(API_BASE.rstrip("/") + "/healthz")
            return {"ok": ok, "status": status, "data": data}
        return {
            "ok": False,
            "error": "unsupported_action",
            "message": f"Unsupported action for kyros/runs: {act}",
            "allowed": ["health", "healthz"],
        }

    # Registry checks: readyz or per-service health
    if name == "kyros/registry":
        act = action or "readyz"
        if act in {"ready", "readyz"}:
            ok, status, data = _http_get(REG_URL.rstrip("/") + "/readyz")
            return {"ok": ok, "status": status, "data": data}
        if act in {"health", "service"}:
            svc = args.get("serviceName") or args.get("service")
            if not svc:
                return {
                    "ok": False,
                    "error": "invalid_arguments",
                    "message": "Provide serviceName for registry health",
                }
            ok, status, data = _http_get(
                f"{REG_URL.rstrip('/')}/health/{svc}"
            )
            return {"ok": ok, "status": status, "data": data}
        return {
            "ok": False,
            "error": "unsupported_action",
            "message": f"Unsupported action for kyros/registry: {act}",
            "allowed": ["readyz", "health"],
        }

    # Memory (Qdrant) basic info
    if name == "kyros/memory":
        act = action or "collections"
        if act in {"collections", "list"}:
            headers = {}
            if QDRANT_API_KEY:
                headers["api-key"] = QDRANT_API_KEY
            ok, status, data = _http_get(
                QDRANT_URL.rstrip("/") + "/collections", headers=headers
            )
            return {"ok": ok, "status": status, "data": data}
        return {
            "ok": False,
            "error": "unsupported_action",
            "message": f"Unsupported action for kyros/memory: {act}",
            "allowed": ["collections"],
        }

    # Default: not implemented yet, but echo useful context for callers.
    return {
        "ok": False,
        "error": "not_implemented",
        "tool": name,
        "message": "This Kyros MCP tool is not yet implemented.",
        "hints": [
            "Pass {ping: true} or action='ping' to verify connectivity.",
            "Available tool keys are derived from KYROS_MCP_TOOLS.",
        ],
        "api_base": API_BASE,
        "registry": REG_URL,
        "daemon": DAEMON_URL,
        "qdrant": QDRANT_URL,
        "tools": TOOLS,
        "args": args,
    }


def main():
    # Read JSON-RPC messages line-by-line from stdin.
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

        # MCP handshake
        if method == "initialize":
            respond(req_id, mcp_initialize_result())
            # Optional: immediately announce that tools list may be available
            send({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
            continue

        # Minimal tool listing endpoint
        if method == "tools/list":
            respond(req_id, list_tools_result())
            continue

        if method == "tools/call":
            params = req.get("params") or {}
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if not isinstance(name, str) or not name:
                respond(
                    req_id,
                    error={
                        "code": -32602,
                        "message": "Invalid params: 'name' must be a non-empty string",
                    },
                )
                continue
            result = call_tool(name, arguments)
            respond(req_id, result)
            continue

        # Optionally support a keepalive/ping
        if method in ("ping", "health", "kyros/handshake"):
            respond(
                req_id,
                {
                    "ok": True,
                    "ts": int(time.time()),
                    "api_base": API_BASE,
                    "registry": REG_URL,
                    "daemon": DAEMON_URL,
                    "qdrant": QDRANT_URL,
                    "tools": TOOLS,
                },
            )
            continue

        # Default: method not found
        respond(
            req_id, error={"code": -32601, "message": f"Method not found: {method}"}
        )


if __name__ == "__main__":
    main()
