#!/usr/bin/env python3
"""
Agent Issue Runner (skeleton)

This script automates a minimal, safe set of actions for a GitHub Issue:
- Resolve issue metadata and agent role
- Create a feature branch
- Generate a role-appropriate planning file under docs/issues/
- Commit, push, and open a draft PR that references the issue
- Comment back to the issue with the PR link

It avoids any external LLM calls so it runs in vanilla GitHub Actions.
Extend it to call your local MCP or LLM backends as needed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict

import requests


def run(cmd: list[str], cwd: str | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def gh_api(method: str, url: str, token: str, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {})
    headers.update({"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
    resp = requests.request(method, url, headers=headers, **kwargs)
    return resp


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\-\s]+", "", text).strip().lower()
    s = re.sub(r"\s+", "-", s)
    return s[:40] or "task"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--role", choices=["architect", "conductor", "implement", "critic"], required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("GITHUB_TOKEN and GITHUB_REPOSITORY are required in the environment", file=sys.stderr)
        sys.exit(1)

    api_base = f"https://api.github.com/repos/{repo}"
    issue_url = f"{api_base}/issues/{args.issue_number}"
    r = gh_api("GET", issue_url, token)
    r.raise_for_status()
    issue: Dict = r.json()
    title = issue.get("title", f"Issue {args.issue_number}")
    body = issue.get("body", "")

    branch = f"agent/{args.role}/issue-{args.issue_number}-{slugify(title)}"
    print(f"Creating branch {branch}")
    run(["git", "checkout", "-b", branch])

    out_dir = Path("docs/issues")
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / f"ISSUE-{args.issue_number}-{args.role}.md"

    plan = [
        f"# Issue #{args.issue_number}: {title}",
        "",
        f"Role: **{args.role}**",
        "",
        "## Source",
        "```",
        body or "(no description)",
        "```",
    ]

    if args.role == "architect":
        plan += [
            "## High-Level Plan",
            "- Context",
            "- Milestones & dates",
            "- Risks & mitigations",
            "- RACI",
            "",
            "## API Contracts",
            "- Endpoints and schemas",
            "- Auth and error model",
        ]
    elif args.role == "conductor":
        plan += [
            "## Task Breakdown",
            "- Subtasks (labels, owners)",
            "- Acceptance criteria per task",
            "- Estimates",
        ]
    elif args.role == "implement":
        plan += [
            "## Implementation Notes",
            "- Code areas to touch",
            "- Testing plan (unit/e2e)",
            "- Rollback plan",
        ]
    elif args.role == "critic":
        plan += [
            "## Review Checklist",
            "- Lint/format",
            "- Tests/coverage",
            "- Security & secrets",
            "- Performance & accessibility",
        ]

    plan_text = "\n".join(plan) + "\n"
    plan_path.write_text(plan_text, encoding="utf-8")

    run(["git", "add", str(plan_path)])
    run(["git", "commit", "-m", f"chore(agent): add {args.role} plan for issue #{args.issue_number}"])
    run(["git", "push", "-u", "origin", branch])

    # Open draft PR
    pr_payload = {
        "title": f"agent({args.role}): Issue #{args.issue_number} — {title}",
        "head": branch,
        "base": "main",
        "draft": True,
        "body": f"Automated {args.role} run for issue #{args.issue_number}.\n\nThis PR tracks the planning artifacts under `{plan_path}`.\n\nCloses #{args.issue_number} (on merge).",
    }
    pr = gh_api("POST", f"{api_base}/pulls", token, json=pr_payload)
    pr.raise_for_status()
    pr_json = pr.json()
    pr_url = pr_json.get("html_url")
    print(f"Opened PR: {pr_url}")

    # Comment back to issue
    comment_payload = {"body": f"Agent run ({args.role}) opened PR: {pr_url}"}
    gh_api("POST", f"{issue_url}/comments", token, json=comment_payload).raise_for_status()


if __name__ == "__main__":
    main()

