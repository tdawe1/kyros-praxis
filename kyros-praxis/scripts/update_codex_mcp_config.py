#!/usr/bin/env python3
"""
Update ~/.codex/config.toml to include Kyros MCP server definitions.

This script:
- Backs up the existing Codex config to ~/.codex/config.toml.backup_<timestamp>
- Removes any existing [mcp_servers.*] sections from the config
- Appends the [mcp_servers.*] sections from codex-old-setup-revise.toml

Usage:
  python3 scripts/update_codex_mcp_config.py
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import time
from pathlib import Path


def extract_mcp_servers_block(template_path: Path) -> str:
    text = template_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    # Find the first [mcp_servers. line
    start_idx = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("[mcp_servers."):
            start_idx = i
            break
    if start_idx is None:
        raise RuntimeError("No [mcp_servers.*] section found in template")

    # Capture until the next major header (Providers) or end of file
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        if lines[j].strip().startswith("# ============================================================================"):
            # Stop if we encounter providers or another major section
            end_idx = j
            break

    block = "\n".join(lines[start_idx:end_idx]).strip() + "\n"
    return block


def remove_existing_mcp_servers(config_text: str) -> str:
    """Remove all [mcp_servers.*] tables from the TOML text."""
    out_lines = []
    in_mcp = False
    for ln in config_text.splitlines():
        stripped = ln.strip()
        if stripped.startswith("[mcp_servers."):
            in_mcp = True
            continue  # drop this line and subsequent lines until next top-level table
        if in_mcp:
            # End the block when we see another top-level table start, e.g. [profiles.x] or [tools]
            if stripped.startswith("[") and not stripped.startswith("[mcp_servers."):
                in_mcp = False
                out_lines.append(ln)
            # else still in mcp block: skip
            continue
        out_lines.append(ln)
    return "\n".join(out_lines) + "\n"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    template_path = repo_root / "codex-old-setup-revise.toml"
    if not template_path.exists():
        print(f"ERROR: Template not found: {template_path}", file=sys.stderr)
        return 2

    codex_conf = Path.home() / ".codex" / "config.toml"
    if not codex_conf.exists():
        print(f"ERROR: Codex config not found: {codex_conf}", file=sys.stderr)
        return 3

    try:
        mcp_block = extract_mcp_servers_block(template_path)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 4

    original = codex_conf.read_text(encoding="utf-8")
    cleaned = remove_existing_mcp_servers(original)

    header = "\n# ============================================================================\n# MCP servers (Kyros Praxis) — auto-synced\n# ============================================================================\n\n"
    updated = cleaned.rstrip() + "\n\n" + header + mcp_block

    # Backup
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup_path = codex_conf.with_name(f"config.toml.backup_{ts}")
    shutil.copy2(codex_conf, backup_path)

    codex_conf.write_text(updated, encoding="utf-8")
    print(f"Updated {codex_conf}\nBackup: {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

