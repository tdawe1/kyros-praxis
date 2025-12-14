#!/usr/bin/env bash
set -euo pipefail

# Clean up top-level docs clutter in apps/ by archiving them under apps/docs/archive/
# - Moves markdown and text reports to a tidy archive
# - Keeps essential entry docs (README.md, QUICK-START.md, QUICKSTART.md) in place
# - Idempotent: safe to re-run

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
APPS_DIR="$ROOT_DIR/apps"
ARCHIVE_DIR="$APPS_DIR/docs/archive"

mkdir -p "$ARCHIVE_DIR"

# Files to keep at apps/ root (space-separated, exact matches)
KEEP=(
  "README.md"
  "QUICK-START.md"
  "QUICKSTART.md"
)

# Helper: check if a filename is in KEEP
keep_file() {
  local base="$1"
  for k in "${KEEP[@]}"; do
    if [[ "$base" == "$k" ]]; then
      return 0
    fi
  done
  return 1
}

echo "Archiving docs from: $APPS_DIR"

shopt -s nullglob
cd "$APPS_DIR"

MOVED=0
for f in *.md *.txt; do
  base="$(basename "$f")"
  # Skip if it's in KEEP or already in docs
  if keep_file "$base"; then
    continue
  fi
  if [[ "$f" == docs/* ]]; then
    continue
  fi
  # Skip dotfiles and non-regular files
  [[ -f "$f" ]] || continue

  # Prefer git mv when available to preserve history
  if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git mv -f "$f" "$ARCHIVE_DIR/" 2>/dev/null || mv -f "$f" "$ARCHIVE_DIR/"
  else
    mv -f "$f" "$ARCHIVE_DIR/"
  fi
  echo "  • moved $f -> docs/archive/$base"
  MOVED=$((MOVED+1))
done

echo "Done. Moved $MOVED file(s) to apps/docs/archive." 
echo "Update or prune the archive at: $ARCHIVE_DIR"

