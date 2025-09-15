#!/usr/bin/env bash
set -euo pipefail

# Stop the tmux session created by scripts/spawn-codex-agents.sh

SESSION=${SESSION:-kyros-agents}

if command -v tmux >/dev/null 2>&1 && tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux kill-session -t "$SESSION"
  echo "Stopped tmux session '$SESSION'"
else
  echo "No tmux session named '$SESSION' found"
fi

