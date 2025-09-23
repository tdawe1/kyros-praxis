import json
import os
import sys
import time

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
        if req_id is not None:
            respond(
                req_id,
                error={"code": -32601, "message": f"Method not found: {method}"},
            )


if __name__ == "__main__":
    main()
