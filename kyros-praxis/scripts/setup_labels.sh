#!/usr/bin/env bash
set -euo pipefail

# Creates or updates recommended repository labels using GitHub CLI.
# Usage: scripts/setup_labels.sh [owner/repo]

REPO="${1:-${GITHUB_REPOSITORY:-}}"
if [[ -z "$REPO" ]]; then
  # Derive from git remote
  url=$(git remote get-url origin 2>/dev/null || true)
  if [[ "$url" =~ github.com[:/](.+/.+)(\.git)?$ ]]; then
    REPO="${BASH_REMATCH[1]}"
  else
    echo "ERROR: Could not determine repo. Pass owner/repo as arg." >&2
    exit 2
  fi
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh (GitHub CLI) not found. Install https://cli.github.com/" >&2
  exit 127
fi

labels=(
  "agent:architect:#7b61ff:Tasks for planning/specification"
  "agent:conductor:#9b59b6:Tasks for slicing/coordination"
  "agent:implement:#2ecc71:Tasks for implementation"
  "agent:critic:#e67e22:Tasks for review/quality"
  "agent:auto-run:#34495e:Trigger automation on label"
  "component:console:#1abc9c:Frontend (Next.js)"
  "component:orchestrator:#3498db:Backend (FastAPI)"
  "type:bug:#e74c3c:Defects"
  "type:feature:#f1c40f:New features"
  "triage:#95a5a6:Needs triage/refinement"
)

echo "Configuring labels for $REPO"
for entry in "${labels[@]}"; do
  IFS=":" read -r name color desc <<<"$entry"
  if gh label view "$name" -R "$REPO" >/dev/null 2>&1; then
    echo "Updating $name"
    gh label edit "$name" -R "$REPO" --color "$color" --description "$desc" || true
  else
    echo "Creating $name"
    gh label create "$name" -R "$REPO" --color "$color" --description "$desc" || true
  fi
done

echo "Done. Current labels:"
gh label list -R "$REPO"

