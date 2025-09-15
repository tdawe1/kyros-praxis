# Scripts

This directory contains utility scripts for the Kyros Praxis project.

## Pre-commit Hook

The `pre-commit-secret-check` script is a pre-commit hook that prevents committing secrets to the repository.

### Installation

To install the pre-commit hook, run:

```bash
ln -s ../../scripts/pre-commit-secret-check .git/hooks/pre-commit
```

### Functionality

The pre-commit hook:
- Checks for common secret patterns in staged files
- Prevents committing `.env` files
- Blocks commits that contain potential secrets

### Customization

You can modify the secret patterns in the script by editing the `SECRET_PATTERNS` array.