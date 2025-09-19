#!/bin/bash
# One command to rule them all
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="${SCRIPT_DIR%/scripts}"
PYTHON_BIN="${PYTHON:-python3}"
cd "$REPO_ROOT"
if "$PYTHON_BIN" scripts/pr_gate.py --base main "$@"; then
  echo "Ready to commit! Run: git commit -m 'feat(TDS-XXX): your message'"
  exit 0
else
  echo "Fix issues above, or run with --fix for auto-fixes"
  exit 1
fi
