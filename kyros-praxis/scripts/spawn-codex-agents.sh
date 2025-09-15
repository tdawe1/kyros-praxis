#!/usr/bin/env bash
set -euo pipefail

# Spawn Codex CLI agents in a persistent tmux session so they can run unattended.
# This is useful for 1h+ autonomous operation without manual intervention.
#
# Requirements:
# - tmux installed (sudo apt-get install tmux)
# - ~/.codex/config.toml has profiles: orchestrator, implementer, critic
#   with approval_policy = "never" for autonomous roles (except orchestrator if you want control)
#
# Usage:
#   bash scripts/spawn-codex-agents.sh           # starts session kyros-agents
#   bash scripts/stop-codex-agents.sh            # stops the session

SESSION=${SESSION:-kyros-agents}
ORCH_PROFILE=${ORCH_PROFILE:-orchestrator}
IMPL_PROFILE=${IMPL_PROFILE:-implementer}
CRIT_PROFILE=${CRIT_PROFILE:-critic}

if ! command -v tmux >/dev/null 2>&1; then
  echo "ERROR: tmux not found. Install with: sudo apt-get install -y tmux" >&2
  exit 127
fi

# Create session detached
tmux new-session -d -s "$SESSION" "codex --profile $ORCH_PROFILE" \;
  rename-window orchestrator \;
  new-window -n implementer "codex --profile $IMPL_PROFILE" \;
  new-window -n critic "codex --profile $CRIT_PROFILE"

echo "Spawned Codex agents in tmux session '$SESSION' (windows: orchestrator, implementer, critic)."
echo "Attach: tmux attach -t $SESSION  |  Detach: Ctrl-b then d  |  Stop: bash scripts/stop-codex-agents.sh"

