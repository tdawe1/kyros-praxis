#!/usr/bin/env bash
set -euo pipefail

# Stop MCP servers started by start-mcp-servers.sh (uses pidfiles),
# and optionally fall back to pkill if no pidfiles are present.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PID_DIR="${ROOT_DIR}/.mcp/pids"

stopped_any=0
if [[ -d "$PID_DIR" ]]; then
  for pidf in "$PID_DIR"/*.pid; do
    [[ -e "$pidf" ]] || continue
    name="$(basename "$pidf" .pid)"
    pid="$(cat "$pidf" 2>/dev/null || true)"
    if [[ -n "${pid:-}" ]] && ps -p "$pid" >/dev/null 2>&1; then
      echo "Stopping $name (pid $pid)"
      kill "$pid" 2>/dev/null || true
      sleep 0.2
      if ps -p "$pid" >/dev/null 2>&1; then
        kill -9 "$pid" 2>/dev/null || true
      fi
      stopped_any=1
    fi
    rm -f "$pidf"
  done
fi

if [[ "$stopped_any" = 0 ]]; then
  echo "No pidfiles found; attempting pkill fallback (may stop unrelated MCP processes)"
  pkill -f "@modelcontextprotocol/server-" 2>/dev/null || true
  pkill -f "mcp-remote .*mcp.exa.ai" 2>/dev/null || true
  pkill -f "mcp-server-time" 2>/dev/null || true
  pkill -f "mcp-server-redis" 2>/dev/null || true
fi

echo "MCP servers stopped."

