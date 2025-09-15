#!/usr/bin/env bash
set -euo pipefail

# Unified MCP stack control
# - Starts/stops dockerized infra (qdrant, kyros services, etc.)
# - Starts/stops local stdio MCP servers with logging
#
# Usage:
#   bash scripts/mcp-stack.sh up [--all] [--profiles "p1 p2 ..."] [--servers "filesystem memory ..."] [--no-docker] [--no-local]
#   bash scripts/mcp-stack.sh down [--no-docker] [--no-local]
#   bash scripts/mcp-stack.sh status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$ROOT_DIR"

cmd="${1:-}"
shift || true

DOCKER=1
LOCAL=1
ALL=0
PROFILES=""
SERVERS=""

usage() {
  echo "Usage: $0 {up|down|status} [options]" >&2
  echo "Options for up: --all | --profiles \"p1 p2\" | --servers \"filesystem memory\" | --no-docker | --no-local" >&2
  echo "Options for down: --no-docker | --no-local" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all) ALL=1 ;;
    --profiles) PROFILES="${2:-}"; shift ;;
    --servers)  SERVERS="${2:-}"; shift ;;
    --no-docker) DOCKER=0 ;;
    --no-local)  LOCAL=0 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
  shift || true
done

if [[ -z "$cmd" ]]; then usage; exit 2; fi

if [[ "$cmd" == "up" ]]; then
  if [[ "$DOCKER" == 1 ]]; then
    if [[ "$ALL" == 1 && -z "$PROFILES" ]]; then
      MCP_UP_PROFILES="qdrant fs memory context7 github puppeteer playwright zen zen-tools notion seq composer exasearch redis fireproof kyros kyros-mcp railway vercel coderabbit kyros-collab" \
        bash scripts/mcp-up.sh
    else
      MCP_UP_PROFILES="$PROFILES" bash scripts/mcp-up.sh
    fi
  fi
  if [[ "$LOCAL" == 1 ]]; then
    MCP_LOCAL_SERVERS="${SERVERS:-filesystem sequentialthinking}" bash scripts/start-mcp-servers.sh
  fi
  echo "MCP stack is up. Use: bash scripts/mcp-stack.sh status"
  exit 0
fi

if [[ "$cmd" == "down" ]]; then
  if [[ "$LOCAL" == 1 ]]; then bash scripts/stop-mcp-servers.sh || true; fi
  if [[ "$DOCKER" == 1 ]]; then docker compose -f docker-compose.integrations.yml down --remove-orphans || true; fi
  echo "MCP stack is down."
  exit 0
fi

if [[ "$cmd" == "status" ]]; then
  echo "--- Docker Compose ---"
  if [[ -f docker-compose.integrations.yml ]]; then
    docker compose -f docker-compose.integrations.yml ps || true
  else
    echo "docker-compose.integrations.yml not found"
  fi
  echo
  echo "--- Local MCP processes (top 20) ---"
  pgrep -af "@modelcontextprotocol/server-|mcp-remote|mcp-server-time|mcp-server-redis" | head -n 20 || true
  exit 0
fi

usage; exit 2

