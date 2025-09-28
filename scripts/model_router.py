#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
from pathlib import Path

STATE = Path("collaboration/.router_state.json")
WINDOW_H = 5
MAX_IN_WINDOW = 580  # leave headroom


def _load():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"glm_start": datetime.utcnow().isoformat() + "Z", "glm_requests": 0}


def _save(s):
    STATE.write_text(json.dumps(s))


def glm_available() -> bool:
    s = _load()
    start = datetime.fromisoformat(s["glm_start"].replace("Z", ""))
    if datetime.utcnow() - start > timedelta(hours=WINDOW_H):
        s["glm_start"] = datetime.utcnow().isoformat() + "Z"
        s["glm_requests"] = 0
        _save(s)
    return s["glm_requests"] < MAX_IN_WINDOW


def select_model(task_type: str, complexity: str) -> str:
    # free by default for non-critical
    if task_type in {"planning", "review", "orchestration"}:
        return "openrouter/sonoma-sky-alpha"
    # use GLM for high-complexity coding within limits
    if complexity == "high" and glm_available():
        s = _load()
        s["glm_requests"] += 1
        _save(s)
        return "glm-4-9b"
    return "openrouter/sonoma-sky-alpha"


if __name__ == "__main__":
    print(select_model("coding", "high"))
