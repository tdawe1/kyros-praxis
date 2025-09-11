#!/bin/sh
# Pre-push hook that inspects files being pushed rather than the staged index.
# Usage: place in .git/hooks/pre-push or referenced via config.

remote="$1"
url="$2"

# Read ref lines from stdin
while read local_ref local_sha remote_ref remote_sha; do
  if [ -z "$remote_sha" ] || [ "$remote_sha" = 0000000000000000000000000000000000000000 ]; then
    range="$local_sha"
  else
    range="$remote_sha..$local_sha"
  fi
  files=$(git diff --name-only "$range")
  [ -z "$files" ] && continue
  echo "Checking files:\n$files"
  # run desired checks here, e.g., linting or tests on $files
  # placeholder: ensure script exits non-zero on failure
  echo "$files" >/dev/null
done
