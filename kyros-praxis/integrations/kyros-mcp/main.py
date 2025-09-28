import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Import MCP security module
sys.path.insert(0, str(Path(__file__).parent.parent))
from mcp_security import create_mcp_security, MCPSecurity

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

# Initialize MCP Security
MCP_SECURITY = create_mcp_security(
    server_name=SERVER_NAME,
    jwt_secret=os.getenv("MCP_JWT_SECRET"),
    api_keys=[QDRANT_API_KEY] if QDRANT_API_KEY else [],
    allowed_roots=[
        os.getenv("KYROS_DATA_ROOT", "/tmp/kyros"),
        "/app",  # Allow access to application directory
        "/opt/kyros"  # Allow access to kyros installation
    ],
    authorization_servers=[
        os.getenv("KYROS_AUTH_SERVER", "http://kyros_orchestrator:8000/auth")
    ],
    resource_uri=f"urn:kyros:mcp:{SERVER_NAME}"
)


def send(obj: dict) -> None:
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


def mcp_initialize_result():
    # MCP initialize with security capabilities
    base_capabilities = {
        "tools": {},
        "resources": {},
        "prompts": {},
        "sampling": {},
        "logging": {},
    }
    
    # Enhance with security information
    capabilities = MCP_SECURITY.create_capabilities_response(base_capabilities)
    
    return {
        "serverInfo": {
            "name": SERVER_NAME, 
            "version": SERVER_VERSION,
            "security": {
                "oauth_resource_server": True,
                "resource_uri": MCP_SECURITY.config.resource_uri,
                "authentication_required": True
            }
        },
        "protocolVersion": os.getenv("MCP_PROTOCOL_VERSION", "2025-06-01"),
        "capabilities": capabilities,
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


def call_tool(name: str, args: dict | None, auth_context: dict = None):
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
    # Security check for sensitive operations
    if auth_context and auth_context.get("auth_type") != "api_key":
        # Require API key for backend operations
        if name in ["kyros/runs", "kyros/registry", "kyros/memory"]:
            if "admin" not in auth_context.get("scopes", []):
                return {
                    "ok": False,
                    "error": "insufficient_privileges",
                    "message": "Backend operations require admin privileges",
                    "required_scopes": ["admin"]
                }
    
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
            # Add authentication from context
            if auth_context and auth_context.get("auth_type") == "bearer":
                headers["Authorization"] = f"Bearer {auth_context.get('token')}"
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
        headers = req.get("headers", {})

        # Special handling for initialize - no auth required for handshake
        if method == "initialize":
            respond(req_id, mcp_initialize_result())
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
                "www_authenticate": f'Bearer realm="{SERVER_NAME}"',
                "supported_methods": ["bearer", "api_key"]
            })
            continue

        # Authorized requests
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
            
            # Pass auth context to tool for authorization checks
            result = call_tool(name, arguments, auth_context)
            respond(req_id, result)
            
            # Audit log the tool call
            MCP_SECURITY.audit_log("tool_call", auth_context, {
                "tool_name": name,
                "arguments": arguments
            })
            continue

        # Authenticated ping/health check
        if method in ("ping", "health", "kyros/handshake"):
            respond(
                req_id,
                {
                    "ok": True,
                    "ts": int(time.time()),
                    "authenticated": True,
                    "user_id": auth_context.get("user_id"),
                    "auth_type": auth_context.get("auth_type"),
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
