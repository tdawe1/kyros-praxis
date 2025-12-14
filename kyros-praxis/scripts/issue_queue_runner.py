#!/usr/bin/env python3
"""
Issue Queue Runner

Consumes GitHub issues matching label filters and invokes the local
agent_issue_runner.py for each until none remain.

Environment:
  - GITHUB_TOKEN (required)
  - GITHUB_REPOSITORY (optional; fallback to origin remote)

Usage:
  python scripts/issue_queue_runner.py \
    --labels agent:architect,agent:implement \
    --exclude-labels needs-review \
    --fallback-role implement
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from typing import List

import requests


def detect_repo() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if repo:
        return repo
    try:
        url = (
            subprocess.run(
                ["git", "remote", "get-url", "origin"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        m = re.search(r"github.com[:/](?P<repo>[^/]+/[^/.]+)", url)
        if m:
            return m.group("repo")
    except Exception:
        pass
    print("ERROR: cannot determine repo (set GITHUB_REPOSITORY)", file=sys.stderr)
    sys.exit(2)


def gh_get(token: str, path: str, params: dict | None = None) -> requests.Response:
    repo = detect_repo()
    url = f"https://api.github.com/repos/{repo}{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    return requests.get(url, headers=headers, params=params or {})


def list_issues(token: str, labels: List[str], exclude_labels: List[str]) -> List[dict]:
    # Use GitHub search API for labels filtering (state=open)
    repo = detect_repo()
    q = [f"repo:{repo}", "is:issue", "is:open"] + [f"label:\"{l}\"" for l in labels]
    for l in exclude_labels:
        q.append(f"-label:\"{l}\"")
    query = "+".join(q)
    resp = requests.get(
        "https://api.github.com/search/issues",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        params={"q": query, "sort": "created", "order": "asc", "per_page": 50},
    )
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    results = []
    for it in items:
        # Hydrate labels
        labels_data = [l.get("name") for l in it.get("labels", [])]
        results.append({
            "number": it.get("number"),
            "title": it.get("title"),
            "labels": labels_data,
        })
    return results


def role_from_labels(labels: List[str], fallback: str) -> str:
    labels_l = [l.lower() for l in labels]
    if "agent:architect" in labels_l:
        return "architect"
    if "agent:conductor" in labels_l:
        return "conductor"
    if "agent:critic" in labels_l:
        return "critic"
    if "agent:implement" in labels_l:
        return "implement"
    return fallback


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="agent:architect,agent:conductor,agent:implement,agent:critic")
    ap.add_argument("--exclude-labels", default="")
    ap.add_argument("--fallback-role", default="implement")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    labels = [l.strip() for l in args.labels.split(",") if l.strip()]
    excl = [l.strip() for l in args.exclude_labels.split(",") if l.strip()]

    consumed_any = False
    while True:
        issues = list_issues(token, labels, excl)
        if not issues:
            print("No matching open issues. Done.")
            break
        for it in issues:
            num = it["number"]
            role = role_from_labels(it.get("labels", []), args.fallback_role)
            print(f"Consuming issue #{num} with role={role}: {it['title']}")
            consumed_any = True
            if args.dry_run:
                continue
            subprocess.run(
                [sys.executable, "scripts/agent_issue_runner.py", "--issue-number", str(num), "--role", role],
                check=True,
            )
        # Loop again in case more issues match after PR creation
    if not consumed_any:
        sys.exit(0)


if __name__ == "__main__":
    main()

