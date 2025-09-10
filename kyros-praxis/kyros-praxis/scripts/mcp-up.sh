#!/usr/bin/env bash
set -euo pipefail

# Launch all MCP servers defined in docker-compose.integrations.yml
# Includes: qdrant, filesystem, memory, context7, github, puppeteer, playwright,
# notion, sequentialthinking, composer-trade, exasearch, kyros-mcp (+ kyros deps).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Probe for the compose file in likely roots
for CANDIDATE in \
  "${SCRIPT_DIR}/.." \
  "${SCRIPT_DIR}/../.." \
  "${PWD}" \
  "${PWD}/.."; do
  if [ -f "${CANDIDATE}/docker-compose.integrations.yml" ]; then
    ROOT_DIR="$(cd "${CANDIDATE}" && pwd)"
    break
  fi
done
: "${ROOT_DIR:?Could not locate docker-compose.integrations.yml; run from project or keep script under kyros-praxis/scripts}"
cd "$ROOT_DIR"

COMPOSE_FILE="docker-compose.integrations.yml"
DC=(docker compose -f "$COMPOSE_FILE")

# Prefer classic builder if buildx isn't available to avoid Bake warnings
export COMPOSE_DOCKER_CLI_BUILD=${COMPOSE_DOCKER_CLI_BUILD:-1}
export DOCKER_BUILDKIT=${DOCKER_BUILDKIT:-0}

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "ERROR: $COMPOSE_FILE not found in $ROOT_DIR" >&2
  exit 1
fi

# Load env if present so we can warn about missing tokens
if [ -f .env ]; then
  # Temporarily disable nounset while sourcing .env to avoid errors on
  # variable references that are defined later in the file.
  set +u; set -a; source .env; set +a; set -u
  echo "Using env: $ROOT_DIR/.env"
else
  echo "Hint: cp .env.integrations.example .env and set required tokens (GitHub, Notion, Exa, etc.)"
fi

warn_if_empty() {
  local name="$1"; local pretty="${2:-$1}"
  if [ -z "${!name:-}" ]; then
    echo "WARN: $pretty is not set" >&2
  fi
}

# Token preflight (optional but recommended)
warn_if_empty GITHUB_PERSONAL_ACCESS_TOKEN "GitHub token (GITHUB_PERSONAL_ACCESS_TOKEN)"
warn_if_empty NOTION_TOKEN "Notion token (NOTION_TOKEN used inside OPENAPI_MCP_HEADERS)"
warn_if_empty EXA_API_KEY "ExaSearch API key (EXA_API_KEY)"
warn_if_empty CONTEXT7_API_TOKEN "Context7 API token (CONTEXT7_API_TOKEN)"
warn_if_empty COMPOSER_API_KEY "Composer Trade API key (COMPOSER_API_KEY)"
warn_if_empty COMPOSER_SECRET_KEY "Composer Trade secret (COMPOSER_SECRET_KEY)"
# Optional
warn_if_empty QDRANT_API_KEY "Qdrant API key (QDRANT_API_KEY)"
warn_if_empty BROWSERLESS_TOKEN "Browserless token (BROWSERLESS_TOKEN)"
warn_if_empty KYROS_MCP_API_KEY "Kyros MCP API key (KYROS_MCP_API_KEY)"

# All profiles that correspond to MCP servers and their infra
PROFILES=(
  qdrant
  fs
  memory
  context7
  github
  puppeteer
  playwright
  notion
  seq
  composer
  exasearch
  kyros         # Kyros app deps for kyros-mcp
  kyros-mcp
)

PROFILE_ARGS=()
for p in "${PROFILES[@]}"; do PROFILE_ARGS+=(--profile "$p"); done

echo "Bringing up MCP stack: ${PROFILES[*]}"
# Preflight: check Docker daemon access
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Cannot talk to Docker daemon. Ensure Docker is installed, running, and your user has permissions (e.g., in the 'docker' group)." >&2
  exit 2
fi
"${DC[@]}" "${PROFILE_ARGS[@]}" up -d --build

echo
echo "MCP services status:"
"${DC[@]}" ps
echo
echo "Tail logs (example):"
echo "  ${DC[*]} logs -f mcp_kyros"
