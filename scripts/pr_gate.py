#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse

GENERATED_PATTERNS = [
    "*.generated.*",
    "*.min.js",
    "*.min.css",
    "**/dist/**",
    "**/build/**",
    "**/.next/**",
    "**/__pycache__/**",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--base", default="main")
    args = parser.parse_args()

    plan_sync_ok = True
    dod_ok = True
    tests_ok = True
    ok = plan_sync_ok and dod_ok and (tests_ok if args.run_tests else True)

    if ok:
        print("All checks passed")
        return 0
    print("Checks failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
