# chore(repo): purge large patch artifacts, add ignore; remove leaked secrets; unblock push

## Summary
- Removed all `*.patch` artifacts under `tools/migration/patches/` from the entire branch history to satisfy GitHub file size limits (previously: 219 MB, 118 MB, 68 MB).
- Added ignore rule `tools/migration/patches/*.patch` to prevent re-adding large patch artifacts.
- Purged `kyros-praxis/kyros-praxis/mcp-servers.json` from history after GitHub Push Protection flagged a GitHub PAT and a Notion API token.
- Force-pushed the cleaned branch `refactor-simplifications-complete`.

## Notes
- Local backup of the large patch files was saved to `_backup_large_patches_20250910T083345Z/` (on the machine where the rewrite was run).
- No runtime/source code changes besides updating `.gitignore` in `kyros-praxis/.gitignore`.

## Impact
- Collaborators must hard reset their local branch to the updated remote to avoid dangling history:
  - `git fetch origin`
  - `git checkout refactor-simplifications-complete`
  - `git reset --hard origin/refactor-simplifications-complete`
- Repository size reduced; pushes no longer blocked by GitHub’s 100 MB limit or flagged secrets.

## Follow-ups
- Rotate the exposed tokens (GitHub PAT and Notion API token) immediately.
- Store tokens securely via environment variables or a secrets manager (e.g., 1Password, Vault, Doppler, GitHub Encrypted Secrets).
- If large patch artifacts are needed in the future, consider hosting them externally or using Git LFS (with history migration) rather than committing them directly.
