# Git Pre-Push Hooks Setup

This guide explains how to set up Git pre-push hooks to run linters on staged changes before allowing a push. This prevents pushing code with quality issues to the remote repository.

## Overview

Git hooks are scripts that run automatically at certain points in Git's execution. The `pre-push` hook runs before a push is completed and can block the push if it fails.

We'll create a `pre-push` hook that:

- Runs `pylint` on Python files (`.py`).
- Runs `ESLint` on JavaScript/TypeScript files (`.js`, `.ts`, `.jsx`, `.tsx`).
- Only lints staged changes (added or modified files).
- Blocks the push and provides feedback if linters fail.

This is useful for maintaining code quality in mixed-language projects like Kyros Praxis (Python backend, JavaScript/TypeScript frontend).

## Prerequisites

### For Python Projects

- Install `pylint`: `pip install pylint`
- Create or update `pyproject.toml` in your project root for pylint configuration (e.g., ignore certain codes, set max line length).

Example `pyproject.toml`:

```toml
[tool.pylint]
max-line-length = 88
disable = ["C0115", "C0116"]  # Disable missing module docstring warnings
```

### For Node.js Projects

- Install `ESLint`: `npm install --save-dev eslint`
- Create or update `.eslintrc.json` in your project root for ESLint configuration.

Example `.eslintrc.json`:

```json
{
  "env": {
    "browser": true,
    "es2021": true,
    "node": true
  },
  "extends": ["eslint:recommended"],
  "parserOptions": {
    "ecmaVersion": 12,
    "sourceType": "module"
  },
  "rules": {
    "no-unused-vars": "error"
  }
}
```

### For CSS (Optional)

- Install `stylelint`: `npm install --save-dev stylelint stylelint-config-standard`
- Create `.stylelintrc.json` if needed.

## Setup Instructions

1. **Create the Hook Script**:

   - Copy the sample pre-push script to `.git/hooks/pre-push`:
     ```bash
     cp scripts/pre-push.sh .git/hooks/pre-push
     ```
   - Make it executable:
     ```bash
     chmod +x .git/hooks/pre-push
     ```

   The script is located at `scripts/pre-push.sh` in the repository root.

2. **Configure Linters**:

   - Ensure `pyproject.toml` (Python) and `.eslintrc.json` (Node.js) are set up as above.
   - For multi-language repos, place configs in the root or subdirectories (e.g., `frontend/.eslintrc.json`).

3. **Install Dependencies**:

   - Python: Run `pip install pylint` in your virtual environment.
   - Node.js: Run `npm install --save-dev eslint` in your project root or frontend directory.

4. **Test the Hook**:
   - Stage some files: `git add <files>`
   - Attempt a push: `git push`
   - If linters fail, the push will be blocked with error output. Fix issues and try again.

## Sample Hook Script

The sample script (`scripts/pre-push.sh`) is a Bash script that:

- Identifies files in the push range by reading ref updates from STDIN and
  running `git diff --name-only --diff-filter=ACMRTUXB "$remote_sha..$local_sha"`.
- Separates Python (`.py`) and JS/TS files.
- Runs `pylint` on Python files (using `pyproject.toml` config).
- Runs `npx eslint` on JS/TS files (using `.eslintrc.json` config).
- Exits with code 1 on failure, blocking the push.

Full script content:

```bash
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
```

## Error Handling

- **No Staged Files**: Script exits 0 if no files are staged.
- **Linter Failures**: If `pylint` or `ESLint` returns a non-zero exit code, the script prints an error message and exits 1, blocking the push.
- **Missing Configs**: Linters will fail if `pyproject.toml` or `.eslintrc.json` are missing. Ensure configs exist in the project root.
- **Tool Not Found**: If `pylint` or `npx eslint` are not installed, the script will fail with a command-not-found error. Install via package managers.
- **Cross-Platform**: The script assumes Bash (Unix-like). On Windows, use Git Bash or WSL. For native Windows, consider PowerShell adaptations.

## Configuration for Common Environments

### Node.js Project (e.g., Kyros Frontend)

- Run in project root: `npm install --save-dev eslint`
- Config: `.eslintrc.json` as shown.
- Usage: The hook runs `npx eslint` on staged JS/TS files.

### Python Project (e.g., Kyros Backend)

- Run in project root: `pip install pylint`
- Config: `pyproject.toml` as shown.
- Usage: The hook runs `pylint` on staged `.py` files.

### Mixed-Language Repo (e.g., Kyros Praxis)

- Place configs in root for global linting.
- For sub-projects (e.g., `services/console/` for frontend), the hook runs from repo root but can be extended to cd into subdirs if needed.
- Extend the script for CSS: Add `stylelint` function similar to above, targeting `.css`/`.scss` files.

## Best Practices

- **Customize Linters**: Adjust configs to ignore generated files (e.g., `generated/` in `.eslintignore`).
- **Performance**: Linting only staged changes keeps the hook fast.
- **CI Integration**: Add the same linting to CI pipelines for consistency.
- **Bypass if Needed**: Use `git push --no-verify` to skip hooks temporarily (not recommended).

For more advanced setups, consider Husky for Node.js or pre-commit for Python to manage hooks across environments.
