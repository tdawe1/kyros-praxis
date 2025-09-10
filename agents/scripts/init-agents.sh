#!/usr/bin/env bash
set -euo pipefail
# scripts/init-agents.sh — bootstrap local agent environments

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

echo "==> Checking .env for API keys..."
need=0
for k in OPENAI_API_KEY ANTHROPIC_API_KEY GOOGLE_API_KEY; do
  if ! grep -q "^${k}=" "$ENV_FILE" 2>/dev/null; then
    echo "Missing ${k} in .env"
    need=1
  fi
done

if [ "$need" -eq 1 ]; then
  cat <<EOF
Add keys to .env (example):
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
EOF
  exit 1
fi

echo "==> Creating local agent config directories (.claude, .gemini, .codex)"
mkdir -p "${ROOT_DIR}/.claude/session_templates" "${ROOT_DIR}/.gemini" "${ROOT_DIR}/.codex"

echo "==> Done. Use scripts/session-kickoff.sh to start a Claude session with context."
