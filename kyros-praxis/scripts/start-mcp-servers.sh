#!/usr/bin/env bash
set -euo pipefail

# Start selected local MCP servers (non-Docker) in the background with logging.
# Configure which to start via MCP_LOCAL_SERVERS (space-separated).
# Defaults: filesystem sequentialthinking
#
# Examples:
#   MCP_LOCAL_SERVERS="filesystem memory puppeteer time" bash scripts/start-mcp-servers.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="${ROOT_DIR}/logs"
PID_DIR="${ROOT_DIR}/.mcp/pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

SERVERS=(${MCP_LOCAL_SERVERS:-filesystem sequentialthinking})

have() { command -v "$1" >/dev/null 2>&1; }

start_server() {
  local name="$1"
  local log="$LOG_DIR/mcp-${name}.log"
  local pidf="$PID_DIR/${name}.pid"

  # Skip if already running from pidfile
  if [[ -f "$pidf" ]] && ps -p "$(cat "$pidf" 2>/dev/null)" >/dev/null 2>&1; then
    echo "[skip] ${name} is already running (pid $(cat "$pidf"))"
    return 0
  fi

  case "$name" in
    filesystem)
      if ! have npx; then echo "WARN: npx not found for filesystem" >&2; return 0; fi
      nohup npx -y @modelcontextprotocol/server-filesystem "$HOME/" \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    memory)
      if ! have npx; then echo "WARN: npx not found for memory" >&2; return 0; fi
      nohup npx -y @modelcontextprotocol/server-memory \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    puppeteer)
      if ! have npx; then echo "WARN: npx not found for puppeteer" >&2; return 0; fi
      nohup npx -y @modelcontextprotocol/server-puppeteer \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    sequentialthinking)
      if ! have npx; then echo "WARN: npx not found for sequentialthinking" >&2; return 0; fi
      nohup npx -y @modelcontextprotocol/server-sequential-thinking \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    time)
      if ! have uvx; then echo "WARN: uvx not found for time" >&2; return 0; fi
      nohup uvx mcp-server-time \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    redis)
      if ! have uvx; then echo "WARN: uvx not found for redis" >&2; return 0; fi
      nohup uvx mcp-server-redis --url "${REDIS_URL:-redis://localhost:6379}" \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    notion)
      if ! have npx; then echo "WARN: npx not found for notion" >&2; return 0; fi
      nohup npx -y @notionhq/notion-mcp-server \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    exa)
      if ! have npx; then echo "WARN: npx not found for exa" >&2; return 0; fi
      if [[ -z "${EXA_API_KEY:-}" ]]; then echo "WARN: EXA_API_KEY not set for exa" >&2; return 0; fi
      # Avoid single quotes so ${EXA_API_KEY} expands
      nohup sh -lc "npx -y mcp-remote \"https://mcp.exa.ai/mcp?exaApiKey=${EXA_API_KEY}\"" \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    context7)
      if ! have npx; then echo "WARN: npx not found for context7" >&2; return 0; fi
      if [[ -z "${CONTEXT7_API_TOKEN:-}" ]]; then echo "WARN: CONTEXT7_API_TOKEN not set for context7" >&2; return 0; fi
      nohup env CONTEXT7_API_TOKEN="${CONTEXT7_API_TOKEN}" DEFAULT_MINIMUM_TOKENS="${CONTEXT7_DEFAULT_MINIMUM_TOKENS:-256}" \
        npx -y @upstash/context7-mcp \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    composer-trade)
      if ! have uvx; then echo "WARN: uvx not found for composer-trade" >&2; return 0; fi
      if [[ -z "${COMPOSER_API_KEY:-}" || -z "${COMPOSER_SECRET_KEY:-}" ]]; then echo "WARN: COMPOSER_API_KEY/COMPOSER_SECRET_KEY not set" >&2; return 0; fi
      nohup env COMPOSER_API_KEY="${COMPOSER_API_KEY}" COMPOSER_SECRET_KEY="${COMPOSER_SECRET_KEY}" \
        uvx composer-trade-mcp==0.1.4 --hash sha256:37d8fcfd6ddc9c8155633f755159f3fcb1a63e7acc2a32513613341a851c84e2 \
        >"$log" 2>&1 & echo $! > "$pidf" ;;
    *)
      echo "WARN: unknown server '$name' (skipping)" >&2 ;;
  esac
}

echo "Starting MCP servers: ${SERVERS[*]}"
for s in "${SERVERS[@]}"; do
  start_server "$s"
done

echo "Done. Logs: $LOG_DIR, PIDs: $PID_DIR"
