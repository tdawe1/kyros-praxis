#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-kyros-praxis/.env}"
[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE not found" >&2; exit 1; }

# Keys we can sync from the current shell (only if set and non-empty)
KEYS=(
  QDRANT_API_KEY
  CONTEXT7_API_TOKEN
  GITHUB_PERSONAL_ACCESS_TOKEN
  BROWSERLESS_TOKEN
  NOTION_TOKEN
  COMPOSER_API_KEY
  COMPOSER_SECRET_KEY
  EXA_API_KEY
  KYROS_MCP_API_KEY
)

escape_sed() { printf '%s' "$1" | sed -e 's/[\&/]/\\&/g'; }

TMP="$(mktemp)"
cp "$ENV_FILE" "$TMP"

updated=0
for k in "${KEYS[@]}"; do
  v="${!k-}"
  if [ -n "${v}" ]; then
    ev="$(escape_sed "$v")"
    if grep -q "^${k}=" "$TMP"; then
      sed -i "s/^${k}=.*/${k}=${ev}/" "$TMP"
    else
      printf '\n%s=%s\n' "$k" "$v" >> "$TMP"
    fi
    updated=$((updated+1))
  fi
done

mv "$TMP" "$ENV_FILE"
echo "Updated $updated keys in $ENV_FILE from current shell env (values not printed)."

