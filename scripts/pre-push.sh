#!/bin/bash

# Git pre-push hook for linting staged changes
# Place this in .git/hooks/pre-push and make it executable: chmod +x .git/hooks/pre-push

set -e

# Function to run pylint on Python files
lint_python() {
  local files=("$@")
  if [[ ${#files[@]} -gt 0 ]]; then
    echo "Running pylint on Python files..."
    pylint --rcfile=pyproject.toml "${files[@]}"
    if [[ $? -ne 0 ]]; then
      echo "Pylint failed. Fix issues before pushing."
      exit 1
    fi
  fi
}

# Function to run ESLint on JS/TS files
lint_js() {
  local files=("$@")
  if [[ ${#files[@]} -gt 0 ]]; then
    echo "Running ESLint on JS/TS files..."
    npx eslint --config .eslintrc.json "${files[@]}"
    if [[ $? -ne 0 ]]; then
      echo "ESLint failed. Fix issues before pushing."
      exit 1
    fi
  fi
}

# Get staged files (only added/modified files)
staged_files=$(git diff --cached --name-only --diff-filter=ACMRTUXB)

if [[ -z "$staged_files" ]]; then
  echo "No staged files to lint."
  exit 0
fi

# Separate files by type
python_files=()
js_files=()

for file in $staged_files; do
  if [[ $file == *.py ]]; then
    python_files+=("$file")
  elif [[ $file == *.js || $file == *.ts || $file == *.jsx || $file == *.tsx ]]; then
    js_files+=("$file")
  fi
done

# Run linters
lint_python "${python_files[@]}"
lint_js "${js_files[@]}"

echo "All linters passed! Push allowed."