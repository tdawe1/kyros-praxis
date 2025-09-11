#!/usr/bin/env python3
import argparse
import subprocess
import sys
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


GENERATED_PATTERNS = [
    "*.generated.*",
    "*.min.js",
    "*.min.css",
    "dist/*",
    "build/*",
    ".next/*",
    "__pycache__/*",
]


def run(
    cmd: List[str], cwd: Path = REPO_ROOT, check: bool = False
) -> Tuple[int, str, str]:
    proc = subprocess.run(
        cmd, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(
            proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr
        )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def resolve_base_ref(base: str) -> str:
    # Prefer local base if exists, else origin/base
    code, _, _ = run(["git", "rev-parse", "--verify", base])
    if code == 0:
        return base
    origin = f"origin/{base}"
    code, _, _ = run(["git", "rev-parse", "--verify", origin])
    if code == 0:
        return origin
    # Last resort: fetch and try again
    run(["git", "fetch", "origin", base])
    code, _, _ = run(["git", "rev-parse", "--verify", origin])
    if code == 0:
        return origin
    return base


def git_range(base: str) -> str:
    base_ref = resolve_base_ref(base)
    code, merge_base, _ = run(["git", "merge-base", "HEAD", base_ref])
    if code == 0 and merge_base:
        return f"{merge_base}..HEAD"
    return f"{base_ref}..HEAD"


def is_generated(path: str) -> bool:
    return any(fnmatch(path, pattern) for pattern in GENERATED_PATTERNS)


def is_test_file(path: str) -> bool:
    p = Path(path)
    name = p.name
    s = str(p)
    return any(
        [
            "/tests/" in s,
            "/test_" in s,
            name.endswith("_test.py"),
            ".test." in name,
            ".spec." in name,
        ]
    )


def classify_changes(files: List[str]):
    docs_changed = any(f.startswith("docs/") or "/docs/" in f for f in files)
    code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}
    code_changed = any(
        (
            Path(f).suffix in code_exts
            or f.startswith("services/")
            or f.startswith("kyros-praxis/services/")
        )
        and not is_generated(f)
        for f in files
    )
    tests_changed = any(is_test_file(f) for f in files)
    return code_changed, docs_changed, tests_changed


def count_loc(diff_range: str) -> Tuple[int, int, int]:
    # returns (files_count, added+deleted (approx), files_count_excluding_generated)
    _, out, _ = run(["git", "diff", "--numstat", diff_range])
    total_loc = 0
    files = 0
    files_excl = 0
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add, delete, path = parts
        files += 1
        if add == "-" or delete == "-":
            # binary changes, skip from LOC
            continue
        if is_generated(path):
            continue
        files_excl += 1
        try:
            total_loc += int(add) + int(delete)
        except ValueError:
            pass
    return files, total_loc, files_excl


def get_changed_files(diff_range: str) -> List[str]:
    _, out, _ = run(["git", "diff", "--name-only", diff_range])
    files = [f for f in out.splitlines() if f]
    return files


def run_pytests() -> bool:
    code, _, _ = run(["pytest", "-q"])
    return code == 0


def main():
    ap = argparse.ArgumentParser(
        description="PR gate checks: plan-sync, tests, diff size, positive feedback"
    )
    ap.add_argument(
        "--base", default="main", help="Base branch to diff against (default: main)"
    )
    ap.add_argument(
        "--run-tests", action="store_true", help="Run test suite as part of the gate"
    )
    ap.add_argument(
        "--skip-plan-sync",
        action="store_true",
        help="Skip plan-sync check (use when docs already complete)",
    )
    ap.add_argument(
        "--fix", action="store_true", help="Attempt to fix issues automatically"
    )
    args = ap.parse_args()

    diff_range = git_range(args.base)
    changed_files = get_changed_files(diff_range)
    code_changed, docs_changed, tests_changed = classify_changes(changed_files)
    files_count, total_loc, files_count_excl = count_loc(diff_range)

    ok = True

    # Plan-sync: require docs changes when code changes, unless skipped
    plan_sync_ok = True
    if code_changed and not docs_changed and not args.skip_plan_sync:
        plan_sync_ok = False
        ok = False
        print(
            "❌ Plan-sync: code changed but no docs updated (docs/*). Use --skip-plan-sync if intentional."
        )

    # DoD: tests touched when code changes
    dod_ok = True
    if code_changed and not tests_changed:
        dod_ok = False
        ok = False
        print("❌ DoD: code changed but no tests updated. Add or update tests.")

    # Run tests if requested
    tests_ok = True
    if args.run_tests:
        print("▶️  Running tests...")
        tests_ok = run_pytests()
        if not tests_ok:
            ok = False
            print("❌ Tests failed. Fix before opening PR.")

    # Auto-fix attempts
    if args.fix and not plan_sync_ok:
        plan_path = REPO_ROOT / "docs" / "PLAN.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        with open(plan_path, "a", encoding="utf-8") as f:
            f.write(f"\n<!-- Updated: {datetime.now().isoformat()} -->\n")
        print("  Auto-fix: Added timestamp to docs/PLAN.md")
    if args.fix and not dod_ok:
        test_path = (
            REPO_ROOT
            / "services"
            / "orchestrator"
            / "tests"
            / "unit"
            / "test_generated.py"
        )
        test_path.parent.mkdir(parents=True, exist_ok=True)
        if not test_path.exists():
            test_path.write_text(
                "# TODO: Replace with real tests\n"
                "def test_placeholder():\n"
                "    assert True\n",
                encoding="utf-8",
            )
            print(
                "  Auto-fix: Created placeholder test at services/orchestrator/tests/unit/test_generated.py (UPDATE IT!)"
            )
        else:
            print("  Auto-fix skipped: placeholder test already exists")

    # Re-evaluate status post auto-fix without clobbering failure states
    ok = plan_sync_ok and dod_ok and (tests_ok if args.run_tests else True)

    # Positive feedback
    if ok:
        print("✅ All checks passed! Ready for PR.")
        print(
            f"  Total changes: {files_count} files, ~{total_loc} LOC (excl. generated)"
        )
        if total_loc < 100:
            print("  Nice focused change! 🎯")
        if not args.run_tests:
            print("  Tip: run with --run-tests for extra confidence.")
        sys.exit(0)
    else:
        print("—")
        print(
            "Use --fix to apply simple auto-fixes or --skip-plan-sync if appropriate."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
