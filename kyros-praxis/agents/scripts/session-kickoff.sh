#!/usr/bin/env bash
set -euo pipefail
# scripts/session-kickoff.sh — print a prefilled kickoff message for Claude Max
GOAL="${1:-<fill goal>}"
cat <<'TEMPLATE'
# Claude Max Kickoff (paste as first message)
Role: architect.claude — Deep work session

Goal: TEMPLATE
Repo summary (short): backend/, frontend/, collaboration/
Context pack (paths): collaboration/state/*, backend/routers/collab.py, docs/ARCHITECTURE.md#collab-api
Constraints:
- Small, reviewable diffs; add/adjust tests
- ETag + atomic write semantics; SSE live tail
- No secrets; .env.example only

Deliverables this session:
- Code + tests + docs/BUILD_NOTES.md delta
- PR description with risk notes and next-step
TEMPLATE
