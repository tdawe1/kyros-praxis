#!/usr/bin/env fish
# Dev bootstrap for Kyros Praxis
# - Starts the orchestrator (port 8000) if not running
# - Optionally resets the local SQLite DB
# - Seeds a demo user and sample jobs
#
# Usage:
#   scripts/dev-bootstrap.fish                # start + seed
#   scripts/dev-bootstrap.fish --reset-db     # wipe DB then start + seed
#   scripts/dev-bootstrap.fish --no-seed      # start only
#

function _echo
  set_color cyan
  echo -n "[dev] "
  set_color normal
  echo $argv
end

set reset_db 0
set do_seed 1
for arg in $argv
  switch $arg
    case '--reset-db'
      set reset_db 1
    case '--no-seed'
      set do_seed 0
  end
end

# Resolve repo root relative to this script
set script_dir (dirname (status -f))
set repo_root (realpath "$script_dir/..")
set orch_dir "$repo_root/services/orchestrator"

_echo "Repo root: $repo_root"
cd "$repo_root" || begin; echo "Failed to cd to repo root"; exit 1; end

if test $reset_db -eq 1
  _echo "Resetting local DB: $orch_dir/orchestrator.db"
  rm -f "$orch_dir/orchestrator.db"
end

# Ensure virtualenv
if not test -d "$orch_dir/.venv"
  _echo "Creating virtualenv for orchestrator"
  python3 -m venv "$orch_dir/.venv" || begin; echo "Failed to create venv"; exit 1; end
end

_echo "Activating venv"
source "$orch_dir/.venv/bin/activate.fish"

_echo "Installing backend requirements (if needed)"
pip install -q -r "$orch_dir/requirements.txt" || begin; echo "pip install failed"; exit 1; end

# Start orchestrator if not responding on health
if not curl -sSf http://localhost:8000/health > /dev/null
  _echo "Starting orchestrator on http://localhost:8000"
  cd "$orch_dir"
  nohup uvicorn main:app --reload --host 0.0.0.0 --port 8000 > "$orch_dir/orchestrator-8000.log" 2>&1 &
  set orch_pid $last_pid
  _echo "Orchestrator PID: $orch_pid (logs: $orch_dir/orchestrator-8000.log)"
else
  _echo "Orchestrator already running on :8000"
end

# Wait for health endpoint
_echo "Waiting for orchestrator to be ready..."
set -l attempts 0
while true
  if curl -sSf http://localhost:8000/health > /dev/null
    break
  end
  set attempts (math $attempts + 1)
  if test $attempts -gt 50
    echo "Timed out waiting for orchestrator. Check $orch_dir/orchestrator-8000.log"
    exit 1
  end
  sleep 0.2
end
_echo "Orchestrator is healthy."

if test $do_seed -eq 1
  _echo "Seeding demo data (user + jobs)"
  python "$repo_root/scripts/seed_demo.py"; or begin
    echo "Seeding failed"; exit 1
  end
else
  _echo "Skipping seeding (--no-seed)"
end

_echo "Done. Login via frontend:"
echo "  Email:    user@example.com"
echo "  Password: password123"
_echo "If frontend isn't running: cd services/console; npm install; set -x NEXTAUTH_SECRET devsecret_dev_abcdefghijklmnopqrstuvwxyz123456; npm run dev -- -p 3001"
