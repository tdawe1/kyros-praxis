# Claim Task Workflow
You will:
1) Ask for `TASK_ID` if missing.
2) Use `new_task` to record a subtask for Implementer with the given `TASK_ID`.
3) Run `execute_command` to update local state: `python scripts/state_update.py {TASK_ID} in_progress`.
4) Use `attempt_completion` with a short summary.

If repo has tests, propose `run-pr-gate.md` next.
