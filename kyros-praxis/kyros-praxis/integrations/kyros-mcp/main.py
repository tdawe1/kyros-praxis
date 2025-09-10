import os, sys, json, time

API_BASE = os.getenv("KYROS_API_BASE", "http://kyros_orchestrator:8000")
REG_URL = os.getenv("KYROS_REGISTRY_URL", "http://kyros_registry:9000")
DAEMON_URL = os.getenv("KYROS_DAEMON_URL", "ws://kyros_daemon:8080/ws")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
TOOLS = [t.strip() for t in os.getenv("KYROS_MCP_TOOLS", "runs,registry,memory,terminal").split(",") if t.strip()]

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def main():
    # Minimal handshake so clients can see the server is alive
    send({
        "jsonrpc": "2.0",
        "method": "kyros/handshake",
        "params": {
            "api_base": API_BASE,
            "registry": REG_URL,
            "daemon": DAEMON_URL,
            "qdrant": QDRANT_URL,
            "tools": TOOLS,
            "ts": int(time.time())
        }
    })

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            send({"jsonrpc":"2.0","error":{"code":-32700,"message":f"parse error: {e}"}})
            continue
        # Echo a stub result so clients don’t block; extend here with real MCP methods
        send({
            "jsonrpc":"2.0",
            "id": req.get("id"),
            "result": {
                "ok": True,
                "echo_method": req.get("method"),
                "note": "Kyros MCP skeleton — implement real methods here"
            }
        })

if __name__ == "__main__":
    main()

