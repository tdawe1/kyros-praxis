# Apps Docs

This folder collects documentation, reports, and notes related to the apps/ workspace.

- `archive/` — bulk documents and reports moved out of `apps/` to reduce clutter
- Keep at apps/ root:
  - `README.md` — main overview
  - `QUICK-START.md` / `QUICKSTART.md` — quick start references

To archive new files later, run:

```
bin/cleanup-apps-docs.sh
```

If there are specific documents you want pinned at the apps/ root, add their filenames to `KEEP` in `bin/cleanup-apps-docs.sh`.

