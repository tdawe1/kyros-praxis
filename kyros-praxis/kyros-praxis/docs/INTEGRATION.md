# Collaboration and GitHub Integration

This project uses a local collaboration state alongside GitHub issues.

## Local State
- `collaboration/state/tasks.json`: backlog and in‑flight tasks (includes `github_issue_number`).
- `collaboration/state/locks.json`: optional agent/task locks.
- `collaboration/state/agents.json`: registered automation agents.
- `collaboration/events/events.jsonl`: append‑only events.
- `collaboration/logs/log.md`: human log/notes.

## Linking to GitHub
1. Read `tasks.json` and create an issue per task (title, body, DoD).
2. Write the returned issue number back to `tasks.json` as `github_issue_number`.
3. Reference issues in PR titles/bodies (e.g., "Fixes #123").
4. Use local scripts (see below) or your preferred CLI with a `GITHUB_TOKEN`.

## Script Stub (Node/TypeScript)
Add a script (e.g., `tools/link-github-issues.ts`) that:
- Loads `collaboration/state/tasks.json`.
- Calls GitHub REST to create missing issues.
- Updates the JSON in place.

Environment:
- `GITHUB_TOKEN`, `GITHUB_REPO` (e.g., `owner/name`).

## Workflow
- Propose tasks → create GitHub issues → update tasks.json → implement → PR references issue → merge → close issue.
