#!/usr/bin/env python3
# scripts/docs-emit-event.py — append a docs_updated event to collaboration/events/events.jsonl
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
events = ROOT / "collaboration" / "events" / "events.jsonl"
events.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "event": "docs_updated",
    "path": sys.argv[1] if len(sys.argv) > 1 else "docs/",
    "actor": "watchdog",
}
with events.open("a", encoding="utf-8") as f:
    f.write(json.dumps(payload) + "\n")
print("OK")
