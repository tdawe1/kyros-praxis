#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

REQ_DIR = Path("collaboration/requests")
REQ_DIR.mkdir(parents=True, exist_ok=True)


def request_kilo_task(task_type: str, payload: dict) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
    f = REQ_DIR / f"{task_type}_{ts}.json"
    f.write_text(
        json.dumps(
            {
                "from": "codex-cli",
                "to": "kilo",
                "task": task_type,
                "payload": payload,
                "ts": ts,
            }
        )
    )
    return f


if __name__ == "__main__":
    path = request_kilo_task("plan_jobs_api", {"task_id": "TDS-3"})
    print(f"Wrote {path}")
