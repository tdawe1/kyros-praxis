# Run PR Gate
1) `execute_command`: `python scripts/pr_gate_minimal.py` (no auto-approval for commands).
2) If exit != 0: show raw output; DO NOT proceed; ask implementer to fix.
3) If success: `attempt_completion` with "Gate passed".
