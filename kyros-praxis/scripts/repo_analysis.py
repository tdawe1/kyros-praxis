#!/usr/bin/env python3
"""
Repo Analysis Runner

Runs a suite of linters and tests, summarizes notable findings, and writes
an analysis report to docs/analysis/ANALYSIS.md (and a dated copy).

Tools invoked (best effort):
- Ruff (Python): ruff check
- Pytest: pytest -q
- ESLint (frontend): npm run lint (services/console)
- Jest (frontend unit): npx jest (services/console)

This script is resilient: if a tool is missing, it records a note and continues.
It is safe to run locally or in CI.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple


def run(cmd: list[str], cwd: str | None = None, timeout: int = 600) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError as e:
        return 127, "", f"{e}"
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", f"Timeout: {e}"


def section(title: str, body: str) -> str:
    return f"\n\n## {title}\n\n````\n{body.strip()}\n````\n"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "docs" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = [
        f"# Repository Analysis", 
        f"Date: {datetime.utcnow().isoformat()}Z",
    ]

    # Ruff
    code, out, err = run(["ruff", "check"], cwd=str(repo_root))
    report.append(section("Ruff (Python)", out or err or f"Exit {code}"))

    # Pytest (only API tests)
    code, out, err = run(["pytest", "-q"], cwd=str(repo_root))
    report.append(section("Pytest", (out + "\n" + err).strip()))

    # ESLint
    code, out, err = run(["npm", "run", "lint"], cwd=str(repo_root / "services" / "console"))
    report.append(section("ESLint (console)", (out + "\n" + err).strip()))

    # Jest
    code, out, err = run(["npx", "jest", "--runInBand"], cwd=str(repo_root / "services" / "console"))
    report.append(section("Jest (console)", (out + "\n" + err).strip()))

    # Write report(s)
    combined = "\n".join(report) + "\n"
    (out_dir / "ANALYSIS.md").write_text(combined, encoding="utf-8")
    dated = out_dir / ("ANALYSIS-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S") + ".md")
    dated.write_text(combined, encoding="utf-8")

    print(str(dated))
    return 0


if __name__ == "__main__":
    sys.exit(main())

