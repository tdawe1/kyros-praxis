# Advance Task Workflow
Steps:
1) Ask for `TASK_ID` and NEW_STATUS (e.g., review, approved).
2) `execute_command`: `python scripts/state_update.py {TASK_ID} {NEW_STATUS}`
3) `attempt_completion` with bullet-point delta and next owner.
