#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

LOG = Path("collaboration/usage.jsonl")


def log_api_call(model: str, tokens: int, cost: float) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.open("a").write(
        json.dumps(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "model": model,
                "tokens": tokens,
                "cost": cost,
            }
        )
        + "\n"
    )


if __name__ == "__main__":
    log_api_call("openrouter/sonoma-sky-alpha", 1200, 0.0)
    print("OK: logged")
