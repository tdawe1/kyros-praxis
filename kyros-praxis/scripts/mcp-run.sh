#!/usr/bin/env bash
set -euo pipefail

# Run an MCP server defined in docker-compose.integrations.yml and attach stdio.
# Usage: bash kyros-praxis/scripts/mcp-run.sh <service_name>

SERVICE_NAME="${1:-}"
if [[ -z "${SERVICE_NAME}" ]]; then
  echo "Usage: $0 <service_name>" >&2
  exit 64
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Locate compose root (repo root containing docker-compose.integrations.yml)
ROOT_DIR=""
for CANDIDATE in \
  "${SCRIPT_DIR}/.." \
  "${SCRIPT_DIR}/../.." \
  "${PWD}" \
  "${PWD}/.."; do
  if [[ -f "${CANDIDATE}/docker-compose.integrations.yml" ]]; then
    ROOT_DIR="$(cd "${CANDIDATE}" && pwd)"
    break
  fi
done

if [[ -z "${ROOT_DIR}" ]]; then
  echo "ERROR: Could not locate docker-compose.integrations.yml; run from project or keep script under kyros-praxis/scripts" >&2
  exit 2
fi

COMPOSE_FILE="${ROOT_DIR}/docker-compose.integrations.yml"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found in PATH" >&2
  exit 127
fi

# Load project .env if present so non-exported values are available
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
  set +a
fi

# Ensure shared integrations network exists for external: true network
if ! docker network inspect kyros-integrations >/dev/null 2>&1; then
  docker network create kyros-integrations >/dev/null
fi

# Build -e passthroughs for common API keys and config if set in the caller's environment
PASS_KEYS=(
  OPENAI_API_KEY GEMINI_API_KEY OPENROUTER_API_KEY
  GITHUB_PERSONAL_ACCESS_TOKEN GITHUB_TOOLSETS GITHUB_READ_ONLY
  VERCEL_TOKEN RAILWAY_TOKEN EXA_API_KEY CODERABBIT_API_KEY CONTEXT7_API_TOKEN
  COMPOSER_API_KEY COMPOSER_SECRET_KEY BROWSERLESS_TOKEN
  QDRANT_API_KEY QDRANT_URL
  KYROS_API_BASE KYROS_REGISTRY_URL KYROS_DAEMON_URL KYROS_MCP_API_KEY KYROS_MCP_TOOLS
  COLLAB_ROOT ZEN_ROOT
)
ENV_ARGS=()
for k in "${PASS_KEYS[@]}"; do
  if [[ -n "${!k:-}" ]]; then
    ENV_ARGS+=("-e" "${k}=${!k}")
  fi
done

# Attach to stdio (-T disables TTY since MCP uses raw stdio JSON-RPC)
cd "${ROOT_DIR}"
exec docker compose -p kyros-integrations -f "${COMPOSE_FILE}" run --rm --no-deps -T "${ENV_ARGS[@]}" "${SERVICE_NAME}"
