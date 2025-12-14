#!/usr/bin/env python3
"""
Focused analysis of the orchestrator service for code quality issues.
"""

import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Issue:
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    message: str
    recommendation: str = ""


class OrchestratorAnalyzer:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.issues: List[Issue] = []
        self.files_analyzed = 0

    def analyze_orchestrator(self) -> Dict[str, Any]:
        """Analyze the orchestrator service."""
        orchestrator_path = self.base_path / "kyros-praxis/services/orchestrator"

        if not orchestrator_path.exists():
            return {"error": "Orchestrator directory not found"}

        python_files = list(orchestrator_path.rglob("*.py"))
        print(f"Found {len(python_files)} Python files in orchestrator")

        for file_path in python_files:
            if self._should_analyze_file(file_path):
                self.analyze_file(file_path)

        return self._generate_report()

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        return not any(
            part in file_path.parts
            for part in ["__pycache__", ".venv", "venv", "node_modules"]
        )

    def analyze_file(self, file_path: Path):
        """Analyze a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.files_analyzed += 1
            lines = content.split('\n')

            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
                self._analyze_ast(tree, file_path, lines)
            except SyntaxError as e:
                self.issues.append(Issue(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    issue_type="syntax_error",
                    severity="high",
                    message=f"Syntax error: {e.msg}",
                    recommendation="Fix syntax error"
                ))

            # Pattern analysis
            self._analyze_patterns(content, file_path, lines)

        except Exception as e:
            self.issues.append(Issue(
                file_path=str(file_path),
                line_number=0,
                issue_type="analysis_error",
                severity="low",
                message=f"Could not analyze file: {e}",
                recommendation=""
            ))

    def _analyze_ast(self, tree: ast.AST, file_path: Path, lines: List[str]):
        """Analyze AST for code quality issues."""
        class Analyzer(ast.NodeVisitor):
            def __init__(self, outer):
                self.outer = outer
                self.file_path = file_path
                self.lines = lines

            def visit_Import(self, node):
                # Check for unused imports (basic check)
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                # Check function length
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno + 1
                    if length > 50:
                        self.outer.issues.append(Issue(
                            file_path=str(self.file_path),
                            line_number=node.lineno,
                            issue_type="long_function",
                            severity="medium",
                            message=f"Function '{node.name}' is {length} lines long",
                            recommendation="Break down into smaller functions"
                        ))

                # Check for functions without docstrings
                if not ast.get_docstring(node):
                    self.outer.issues.append(Issue(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        issue_type="missing_docstring",
                        severity="low",
                        message=f"Function '{node.name}' missing docstring",
                        recommendation="Add docstring describing function purpose"
                    ))

                self.generic_visit(node)

            def visit_ClassDef(self, node):
                # Check class length
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno + 1
                    if length > 200:
                        self.outer.issues.append(Issue(
                            file_path=str(self.file_path),
                            line_number=node.lineno,
                            issue_type="long_class",
                            severity="medium",
                            message=f"Class '{node.name}' is {length} lines long",
                            recommendation="Consider breaking into smaller classes"
                        ))

                self.generic_visit(node)

            def visit_ExceptHandler(self, node):
                # Check for bare except
                if node.type is None:
                    self.outer.issues.append(Issue(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        issue_type="bare_except",
                        severity="medium",
                        message="Bare except clause detected",
                        recommendation="Specify exception type"
                    ))
                self.generic_visit(node)

        analyzer = Analyzer(self)
        analyzer.visit(tree)

    def _analyze_patterns(self, content: str, file_path: Path, lines: List[str]):
        """Analyze code patterns for issues."""
        for i, line in enumerate(lines, 1):
            # Check for hardcoded secrets
            if self._is_hardcoded_secret(line):
                self.issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="hardcoded_secret",
                    severity="critical",
                    message="Potential hardcoded secret/password",
                    recommendation="Use environment variables or secret management"
                ))

            # Check for print statements
            if 'print(' in line and not line.strip().startswith('#'):
                self.issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="print_statement",
                    severity="low",
                    message="Print statement found in code",
                    recommendation="Use proper logging instead"
                ))

            # Check for TODO comments
            if '# TODO' in line.upper():
                self.issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="todo_comment",
                    severity="low",
                    message="TODO comment found",
                    recommendation="Address TODO item or create issue tracker"
                ))

            # Check for long lines
            if len(line) > 100 and not line.strip().startswith('#'):
                self.issues.append(Issue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="long_line",
                    severity="low",
                    message=f"Line too long ({len(line)} characters)",
                    recommendation="Break long lines or use line continuation"
                ))

    def _is_hardcoded_secret(self, line: str) -> bool:
        """Check if line contains hardcoded secrets."""
        import re

        # Check for common secret patterns
        secret_patterns = [
            r'password\s*=\s*[\'"][^\'"]{8,}[\'"]',
            r'secret\s*=\s*[\'"][^\'"]{8,}[\'"]',
            r'api_key\s*=\s*[\'"][^\'"]{8,}[\'"]',
            r'token\s*=\s*[\'"][^\'"]{8,}[\'"]',
            r'PRIVATE_KEY\s*=\s*[\'"][^\'"]+',
        ]

        for pattern in secret_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Exclude test files and obvious dummy values
                if ('test' not in line.lower() and
                    'dummy' not in line.lower() and
                    'example' not in line.lower() and
                    'testpassword' not in line.lower()):
                    return True

        return False

    def _generate_report(self) -> Dict[str, Any]:
        """Generate analysis report."""
        # Group issues by severity
        by_severity = {}
        for issue in self.issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)

        # Group issues by type
        by_type = {}
        for issue in self.issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)

        # Group issues by file
        by_file = {}
        for issue in self.issues:
            if issue.file_path not in by_file:
                by_file[issue.file_path] = []
            by_file[issue.file_path].append(issue)

        return {
            "summary": {
                "files_analyzed": self.files_analyzed,
                "total_issues": len(self.issues),
                "by_severity": {k: len(v) for k, v in by_severity.items()},
                "by_type": {k: len(v) for k, v in by_type.items()},
                "by_file": {k: len(v) for k, v in by_file.items()}
            },
            "issues": [
                {
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "message": issue.message,
                    "recommendation": issue.recommendation
                }
                for issue in sorted(self.issues, key=lambda x: (x.severity, x.file_path))
            ]
        }


def main():
    """Main analysis function."""
    analyzer = OrchestratorAnalyzer("/home/thomas/kyros-praxis")
    report = analyzer.analyze_orchestrator()

    print("\n" + "="*60)
    print("ORCHESTRATOR SERVICE CODE ANALYSIS")
    print("="*60)

    summary = report["summary"]
    print(f"\nFiles Analyzed: {summary['files_analyzed']}")
    print(f"Total Issues: {summary['total_issues']}")

    print("\nIssues by Severity:")
    for severity, count in summary['by_severity'].items():
        print(f"  {severity.upper()}: {count}")

    print("\nIssues by Type:")
    for issue_type, count in sorted(summary['by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue_type}: {count}")

    print("\n" + "="*60)
    print("CRITICAL AND HIGH SEVERITY ISSUES")
    print("="*60)

    critical_issues = [issue for issue in report["issues"] if issue["severity"] in ["critical", "high"]]

    if critical_issues:
        for issue in critical_issues:
            print(f"\n🔥 {issue['file_path']}:{issue['line_number']}")
            print(f"   Type: {issue['issue_type']}")
            print(f"   Message: {issue['message']}")
            if issue['recommendation']:
                print(f"   Recommendation: {issue['recommendation']}")
    else:
        print("✅ No critical or high severity issues found!")

    # Save detailed report
    with open('/home/thomas/kyros-praxis/orchestrator_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to: /home/thomas/kyros-praxis/orchestrator_analysis_report.json")


if __name__ == "__main__":
    main()