# Submit PR
1) `search_files` for TODO/console.log and list.
2) `execute_command`: run tests (e.g., `pytest -q` or `npm test`).
3) If green, `execute_command`: `git add -A && git commit -m "<conventional>"`.
4) `execute_command`: `git push -u origin $(git branch --show-current)`
5) `execute_command`: `gh pr create --fill` (ask for title/desc if needed).
6) `attempt_completion` with PR URL.
