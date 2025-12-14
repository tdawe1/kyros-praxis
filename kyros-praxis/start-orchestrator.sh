#!/bin/bash
# Startup script for Orchestrator service (package-safe)

set -euo pipefail

# Resolve repo root relative to this script
SCRIPT_DIR=$(cd -- "$(dirname "$0")" >/dev/null 2>&1 && pwd)
REPO_ROOT="$SCRIPT_DIR"

# Prefer service-local venv if present
if [ -d "$REPO_ROOT/services/orchestrator/venv" ]; then
  # shellcheck disable=SC1091
  source "$REPO_ROOT/services/orchestrator/venv/bin/activate"
fi

# Ensure imports resolve using package path
export PYTHONPATH="${REPO_ROOT}:${REPO_ROOT}/services/orchestrator:${PYTHONPATH:-}"

# Allow overriding port via ORCH_PORT env var
PORT="${ORCH_PORT:-8000}"

echo "Starting Orchestrator on http://localhost:$PORT"
echo "Press Ctrl+C to stop"

# Optional reload (set ORCH_RELOAD=1 for autoreload)
RELOAD_ARGS=""
if [ "${ORCH_RELOAD:-}" = "1" ]; then
  RELOAD_ARGS="--reload"
fi

# Use package path to avoid relative import issues
exec uvicorn services.orchestrator.main:app $RELOAD_ARGS --port "$PORT" --log-level info
