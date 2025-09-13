#!/usr/bin/env python3
import subprocess, sys

def check_tests() -> bool:
    r = subprocess.run(["pytest", "-q"])
    if r.returncode == 0:
        return True
    if r.returncode == 5:
        print("⚠️  No tests collected (Day-1 warning).")
        return True
    return False

def warn_large_staged_diff() -> None:
    r = subprocess.run(["git", "diff", "--cached", "--stat"], capture_output=True, text=True)
    files = [ln for ln in r.stdout.strip().splitlines() if "|" in ln]
    if len(files) > 20:
        print(f"⚠️  Large staged diff: {len(files)} files")

if __name__ == "__main__":
    if not check_tests():
        print("❌ Tests failed"); sys.exit(1)
    warn_large_staged_diff()
    print("✅ Ready for commit")
