#!/usr/bin/env python3
"""
Minimal PR Gate Script for Kyros Development Workflow

This script runs basic checks before allowing commits or PR merges.
Used by Implementer, Critic, and Integrator modes.
Includes security audit capabilities using SECAUDIT methodology.

Usage:
  python scripts/pr_gate_minimal.py                    # Basic checks
  python scripts/pr_gate_minimal.py --run-tests       # Include test execution
  python scripts/pr_gate_minimal.py --security-only   # Security audit only
  python scripts/pr_gate_minimal.py --strict         # Fail on warnings
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Constants
MAX_CHANGED_LINES = 200
MAX_MODULES = 3
PLAN_FILES = ["docs/backend-current-plan.md", "docs/frontend-current-plan.md"]
DISALLOWED_PATTERNS = [
    r"API_KEY\s*=",
    r"SECRET\s*=",
    r"PASSWORD\s*=",
    r"TOKEN\s*=",
]

# Security-sensitive file patterns
SECURITY_SENSITIVE_PATTERNS = [
    r".*auth.*",
    r".*login.*",
    r".*password.*",
    r".*token.*",
    r".*crypt.*",
    r".*encrypt.*",
    r".*decrypt.*",
    r".*session.*",
    r".*jwt.*",
    r".*oauth.*",
    r".*api.*endpoint.*",
    r".*input.*validation.*",
    r".*sanitiz.*",
    r".*upload.*",
    r".*download.*",
]

# Security-sensitive keywords in code
SECURITY_KEYWORDS = [
    "password", "secret", "key", "token", "auth", "login", "session",
    "encrypt", "decrypt", "hash", "salt", "jwt", "oauth", "api_key",
    "sql", "query", "exec", "eval", "shell", "system", "subprocess"
]


class PRGateResult:
    def __init__(self):
        self.passed = True
        self.warnings = []
        self.errors = []
        self.suggestions = []
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.passed = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def add_suggestion(self, message: str):
        self.suggestions.append(message)
    
    def print_report(self):
        print("\n" + "=" * 60)
        print("PR GATE REPORT")
        print("=" * 60)
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.suggestions:
            print("\n💡 SUGGESTIONS:")
            for suggestion in self.suggestions:
                print(f"  • {suggestion}")
        
        if self.passed:
            print("\n✅ All checks passed!")
        else:
            print("\n❌ PR gate failed - fix errors before proceeding")
        
        print("=" * 60)


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def check_diff_size(result: PRGateResult) -> None:
    """Check if the diff size is within limits."""
    # Get staged changes
    retcode, stdout, stderr = run_command(["git", "diff", "--cached", "--stat"])
    if retcode != 0:
        result.add_error(f"Failed to get diff stats: {stderr}")
        return
    
    # Parse diff stats to count changed lines
    lines_changed = 0
    for line in stdout.split('\n'):
        if ' insertion' in line or ' deletion' in line:
            # Extract numbers from lines like "5 files changed, 42 insertions(+), 10 deletions(-)"
            match = re.search(r'(\d+)\s+insertion', line)
            if match:
                lines_changed += int(match.group(1))
            match = re.search(r'(\d+)\s+deletion', line)
            if match:
                lines_changed += int(match.group(1))
    
    if lines_changed > MAX_CHANGED_LINES:
        result.add_error(
            f"Too many changed lines: {lines_changed} (max {MAX_CHANGED_LINES})\n"
            f"Consider splitting into multiple smaller PRs"
        )
    elif lines_changed > MAX_CHANGED_LINES * 0.8:
        result.add_warning(
            f"Large diff: {lines_changed} lines (recommended max {MAX_CHANGED_LINES})"
        )


def check_modified_modules(result: PRGateResult) -> None:
    """Check if too many modules are modified."""
    retcode, stdout, stderr = run_command(["git", "diff", "--cached", "--name-only"])
    if retcode != 0:
        result.add_error(f"Failed to get modified files: {stderr}")
        return
    
    # Extract module directories from file paths
    modules = set()
    for line in stdout.split('\n'):
        if line.strip():
            parts = line.strip().split('/')
            if len(parts) > 1:
                modules.add(parts[0])
    
    if len(modules) > MAX_MODULES:
        result.add_error(
            f"Too many modules modified: {len(modules)} ({', '.join(sorted(modules))})\n"
            f"Consider splitting changes across multiple PRs"
        )


def check_secrets(result: PRGateResult) -> None:
    """Check for potential secrets in staged changes."""
    retcode, stdout, stderr = run_command(["git", "diff", "--cached"])
    if retcode != 0:
        result.add_error(f"Failed to get diff: {stderr}")
        return
    
    # Check for potential secrets
    for pattern in DISALLOWED_PATTERNS:
        if re.search(pattern, stdout, re.IGNORECASE):
            result.add_error(f"Potential secret found in diff (pattern: {pattern})")


def check_plan_sync(result: PRGateResult) -> None:
    """Check if code changes are accompanied by plan updates."""
    retcode, stdout, stderr = run_command(["git", "diff", "--cached", "--name-only"])
    if retcode != 0:
        result.add_error(f"Failed to get modified files: {stderr}")
        return
    
    modified_files = [line.strip() for line in stdout.split('\n') if line.strip()]
    
    # Check if any source code files are modified
    has_code_changes = any(
        f.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')) 
        and not f.startswith('docs/') 
        and not f.startswith('scripts/')
        for f in modified_files
    )
    
    # Check if plan files are updated
    plan_files_updated = any(f in modified_files for f in PLAN_FILES)
    
    if has_code_changes and not plan_files_updated:
        result.add_error(
            "Code changes detected but plan files not updated.\n"
            f"Please update one of: {', '.join(PLAN_FILES)}\n"
            "This ensures plan-sync requirement is met."
        )


def is_security_sensitive_file(file_path: str) -> bool:
    """Check if a file is security-sensitive based on its path."""
    file_lower = file_path.lower()
    return any(re.search(pattern, file_lower) for pattern in SECURITY_SENSITIVE_PATTERNS)


def contains_security_keywords(diff_content: str) -> bool:
    """Check if diff contains security-sensitive keywords."""
    content_lower = diff_content.lower()
    return any(keyword in content_lower for keyword in SECURITY_KEYWORDS)


def check_security_audit_requirements(result: PRGateResult) -> None:
    """Check if changes require security audit and trigger SECAUDIT if needed."""
    print("\n🔒 Checking security audit requirements...")
    
    # Get modified files
    retcode, stdout, stderr = run_command(["git", "diff", "--cached", "--name-only"])
    if retcode != 0:
        result.add_error(f"Failed to get modified files: {stderr}")
        return
    
    modified_files = [line.strip() for line in stdout.split('\n') if line.strip()]
    
    # Check for security-sensitive files
    security_sensitive_files = [f for f in modified_files if is_security_sensitive_file(f)]
    
    # Get diff content for keyword analysis
    retcode, diff_stdout, stderr = run_command(["git", "diff", "--cached"])
    if retcode == 0 and contains_security_keywords(diff_stdout):
        result.add_warning(
            "Security-sensitive keywords detected in changes.\n"
            "Consider running security audit: python scripts/security_audit.py --auto"
        )
    
    # Check file extensions for security-sensitive code
    code_files = [f for f in modified_files if f.endswith(('.py', '.ts', '.tsx', '.js', '.jsx'))]
    
    if security_sensitive_files:
        result.add_warning(
            f"Security-sensitive files modified: {', '.join(security_sensitive_files)}\n"
            "Security audit recommended: python scripts/security_audit.py --auto"
        )
    
    # Check for high-risk file types
    high_risk_files = [f for f in modified_files if any(keyword in f.lower() for keyword in ['auth', 'login', 'password', 'token'])]
    if high_risk_files:
        result.add_warning(
            f"High-risk security files modified: {', '.join(high_risk_files)}\n"
            "Security audit required: python scripts/security_audit.py --auto"
        )


def run_security_audit(result: PRGateResult) -> None:
    """Run automated security audit using SECAUDIT methodology."""
    print("\n🔍 Running automated security audit...")
    
    # Check if security audit script exists
    security_script = Path("scripts/security_audit.py")
    if not security_script.exists():
        result.add_warning(
            "Security audit script not found.\n"
            "Create scripts/security_audit.py to enable automated security auditing."
        )
        return
    
    # Run security audit
    retcode, stdout, stderr = run_command(["python", "scripts/security_audit.py", "--auto"])
    
    if retcode == 0:
        try:
            # Parse JSON output from security audit
            audit_result = json.loads(stdout)
            
            if audit_result.get("status") == "security_analysis_complete":
                findings = audit_result.get("security_findings", [])
                
                # Count findings by severity
                critical_count = sum(1 for f in findings if f.get("severity") == "Critical")
                high_count = sum(1 for f in findings if f.get("severity") == "High")
                medium_count = sum(1 for f in findings if f.get("severity") == "Medium")
                
                if critical_count > 0:
                    result.add_error(
                        f"Security audit found {critical_count} Critical vulnerabilities.\n"
                        "These must be fixed before proceeding."
                    )
                elif high_count > 0:
                    result.add_error(
                        f"Security audit found {high_count} High severity vulnerabilities.\n"
                        "These should be fixed before proceeding."
                    )
                elif medium_count > 0:
                    result.add_warning(
                        f"Security audit found {medium_count} Medium severity issues.\n"
                        "Consider fixing these before proceeding."
                    )
                else:
                    print("✅ Security audit passed - no vulnerabilities found")
                
                # Print summary of findings
                if findings:
                    print("\n📋 Security Audit Summary:")
                    print(f"  Critical: {critical_count}, High: {high_count}, Medium: {medium_count}")
                    for finding in findings[:3]:  # Show first 3 findings
                        print(f"  - {finding.get('category', 'Unknown')}: {finding.get('vulnerability', 'Unknown')}")
                    
            elif audit_result.get("status") == "files_required_to_continue":
                result.add_warning(
                    "Security audit requires additional files:\n"
                    f"{audit_result.get('files_needed', [])}"
                )
            else:
                result.add_warning("Security audit returned unexpected status")
                
        except json.JSONDecodeError:
            result.add_warning("Failed to parse security audit results")
    
    else:
        result.add_warning(f"Security audit failed (exit code {retcode})")
        if stderr:
            print(f"Audit error: {stderr}")


def run_tests(result: PRGateResult) -> None:
    """Run backend and frontend test suites."""
    print("\n🧪 Running tests...")

    # Run backend tests
    backend_path = Path("services/orchestrator")
    if backend_path.exists():
        print("Running backend tests...")
        retcode, stdout, stderr = run_command(["pytest", "-q"], cwd=backend_path)
        if retcode == 0:
            print("✅ Backend tests passed")
            # Show summary output
            lines = stdout.split('\n')[-10:]
            print("Test summary:")
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        else:
            result.add_error(f"Backend tests failed (exit code {retcode})")
            print(f"Error output:\n{stderr}")
    else:
        result.add_warning("Backend directory not found - skipping backend tests")

    # Run frontend tests
    frontend_path = Path("services/console")
    if frontend_path.exists():
        print("Running frontend tests...")
        retcode, stdout, stderr = run_command(["npx", "jest"], cwd=frontend_path)
        if retcode == 0:
            print("✅ Frontend tests passed")
            # Show summary output
            lines = stdout.split('\n')[-10:]
            print("Test summary:")
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        else:
            result.add_error(f"Frontend tests failed (exit code {retcode})")
            print(f"Error output:\n{stderr}")
    else:
        result.add_warning("Frontend directory not found - skipping frontend tests")


def run_orchestrator_targets(result: PRGateResult, targets: List[str]) -> None:
    """Run Make targets in services/orchestrator if present."""
    mk = Path("services/orchestrator/Makefile")
    if not mk.exists():
        result.add_warning("Orchestrator Makefile not found; skipping orchestrator targets")
        return
    for t in targets:
        print(f"\n🔧 Running orchestrator target: {t}...")
        rc, out, err = run_command(["make", "-C", "services/orchestrator", t])
        if rc == 0:
            print(f"✅ {t} passed")
            lines = out.split('\n')[-20:]
            print("Last 20 lines:")
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        else:
            result.add_error(f"Orchestrator target '{t}' failed (exit {rc})")
            if err:
                print(f"Error:\n{err}")


def check_code_quality(result: PRGateResult) -> None:
    """Run basic code quality checks."""
    print("\n🔍 Running code quality checks...")
    
    # Python checks
    if Path("requirements.txt").exists() or Path("pyproject.toml").exists():
        # Try ruff if available
        retcode, stdout, stderr = run_command(["ruff", "check", "."])
        if retcode == 0:
            print("✅ Ruff checks passed")
        elif retcode == 127:  # Command not found
            print("⚠️  Ruff not found - skipping lint checks")
        else:
            result.add_error(f"Ruff found issues (exit code {retcode})")
            print(f"Issues:\n{stdout}")
    
    # Node.js checks
    if Path("package.json").exists():
        # Try ESLint if available
        if Path("node_modules/.bin/eslint").exists():
            retcode, stdout, stderr = run_command(["npm", "run", "lint"])
            if retcode == 0:
                print("✅ ESLint checks passed")
            else:
                result.add_error(f"ESLint found issues (exit code {retcode})")
                print(f"Issues:\n{stdout}")


def main():
    parser = argparse.ArgumentParser(
        description="Minimal PR gate for Kyros development workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pr_gate_minimal.py                    # Basic checks
  python scripts/pr_gate_minimal.py --run-tests       # Include test execution
  python scripts/pr_gate_minimal.py --security-only   # Security audit only
  python scripts/pr_gate_minimal.py --strict          # Fail on warnings
        """
    )
    
    parser.add_argument("--run-tests", action="store_true", help="Run test suite")
    parser.add_argument("--orchestrator-smoke", action="store_true", help="Run orchestrator steel-thread tests")
    parser.add_argument("--orchestrator-events", action="store_true", help="Run orchestrator events tests")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings")
    parser.add_argument("--skip-code-quality", action="store_true", help="Skip code quality checks")
    parser.add_argument("--security-only", action="store_true", help="Run security audit only")
    parser.add_argument("--run-security-audit", action="store_true", help="Run automated security audit")
    
    args = parser.parse_args()
    
    result = PRGateResult()
    
    # Handle security-only mode
    if args.security_only:
        print("🔒 Running security audit only...")
        check_security_audit_requirements(result)
        if args.run_security_audit:
            run_security_audit(result)
        result.print_report()
        if not result.passed:
            sys.exit(1)
        elif args.strict and result.warnings:
            print("\n⚠️  Strict mode: warnings treated as errors")
            sys.exit(1)
        else:
            sys.exit(0)
    
    print("🚀 Running PR gate checks...")
    
    # Always run these checks
    check_diff_size(result)
    check_modified_modules(result)
    check_secrets(result)
    check_plan_sync(result)
    
    # Check security requirements
    check_security_audit_requirements(result)
    
    # Run automated security audit if requested
    if args.run_security_audit:
        run_security_audit(result)
    
    # Run code quality checks unless skipped
    if not args.skip_code_quality:
        check_code_quality(result)
    
    # Run tests if requested
    if args.run_tests:
        run_tests(result)
    if args.orchestrator_smoke:
        # Ensure a default SECRET_KEY for tests that depend on it
        os.environ.setdefault("SECRET_KEY", "test-secret")
        run_orchestrator_targets(result, ["test-thread"])
    if args.orchestrator_events:
        os.environ.setdefault("SECRET_KEY", "test-secret")
        run_orchestrator_targets(result, ["test-events"])
    
    # Print report
    result.print_report()
    
    # Exit with appropriate code
    if not result.passed:
        sys.exit(1)
    elif args.strict and result.warnings:
        print("\n⚠️  Strict mode: warnings treated as errors")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
