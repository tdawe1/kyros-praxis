# Quality gates
- For any code change > 20 LOC, add/adjust tests and docs in the same PR.
- Before completing: run `scripts/pr_gate_minimal.py`; block completion if failing.
- Prefer `apply_diff` over wholesale rewrites. Match precision 100%.
