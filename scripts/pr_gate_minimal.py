#!/usr/bin/env python3
# scripts/pr_gate_minimal.py - Start with this, expand later

import subprocess
import sys

def check_tests():
    """Just run tests for now"""
    result = subprocess.run(["pytest", "-q"], capture_output=True)
    return result.returncode == 0

def check_diff_size():
    """Warn on large diffs"""
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD~1"],
        capture_output=True, text=True
    )
    lines = result.stdout.count('\n')
    if lines > 20:  # files changed
        print(f"⚠️  Large diff: {lines} files changed")
    return True

if __name__ == "__main__":
    if not check_tests():
        print("❌ Tests failed")
        sys.exit(1)
    check_diff_size()
    print("✅ Ready for commit")
