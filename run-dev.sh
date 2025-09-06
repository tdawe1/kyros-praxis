#!/usr/bin/env bash
set -euo pipefail
export NEXT_PUBLIC_ADK_URL="${NEXT_PUBLIC_ADK_URL:-http://localhost:8080}"
export KYROS_DAEMON_PORT="${KYROS_DAEMON_PORT:-8787}"
export PORT="${PORT:-3001}"
mkdir -p .devlogs data

# Python path so orchestrator can import ../packages/*
export PYTHONPATH="$(pwd)/packages:$(pwd):$PYTHONPATH"

echo "== Kyros dev =="
echo "Console:      http://localhost:${PORT}"
echo "Orchestrator: http://localhost:8080/healthz  (internal)"
echo "Daemon (WS):  ws://localhost:${KYROS_DAEMON_PORT}/term (internal)"

pip install --user -r apps/adk-orchestrator/requirements.txt
[ -d apps/terminal-daemon/node_modules ] || (cd apps/terminal-daemon && npm i)
[ -d apps/console/node_modules ] || (cd apps/console && npm i)

( cd apps/adk-orchestrator && python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload ) > .devlogs/adk.log 2>&1 &
ADK_PID=$!
( cd apps/terminal-daemon && KYROS_DAEMON_PORT="$KYROS_DAEMON_PORT" node server.js ) > .devlogs/daemon.log 2>&1 &
DAEMON_PID=$!
( cd apps/console && PORT="$PORT" npm run dev -- -p "$PORT" ) > .devlogs/console.log 2>&1 &
CONSOLE_PID=$!

trap 'kill $ADK_PID $DAEMON_PID $CONSOLE_PID || true' EXIT
echo "== Tailing logs (Ctrl+C to stop) ==" && tail -n +1 -F .devlogs/*.log