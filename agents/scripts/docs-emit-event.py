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
import sys

# … (other setup code)

# Sanitise the `path` argument
if len(sys.argv) > 1:
    input_path = sys.argv[1]
    if ".." in input_path or input_path.startswith("/"):
        print("Error: Invalid path argument", file=sys.stderr)
        sys.exit(1)
    path_value = input_path
else:
    path_value = "docs/"

payload = {
    # … (other payload fields)
    "path": path_value,
    # … (remaining payload fields)
}

# … (rest of script)
    "actor": "watchdog",
}
with events.open("a", encoding="utf-8") as f:
    f.write(json.dumps(payload) + "\n")
print("OK")
