#!/usr/bin/env python3
import json
from pathlib import Path

REQ_DIR = Path("collaboration/requests")
EVT = Path("collaboration/events/events.jsonl")
EVT.parent.mkdir(parents=True, exist_ok=True)


def main():
    for p in sorted(REQ_DIR.glob("*.json")):
        req = json.loads(p.read_text())
        EVT.open("a").write(
            json.dumps({"ts": req["ts"], "event": "bridge_request", "payload": req})
            + "\n"
        )
        p.unlink()
    print("OK: polled")


if __name__ == "__main__":
    main()
