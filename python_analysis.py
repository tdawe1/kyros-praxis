#!/usr/bin/env python3
"""
Python Code Analysis Script for Kyros Praxis
Analyzes code smells, bugs, PEP 8 violations, security issues, and more.
"""

import os
import re
import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    code_snippet: str = ""


class PythonCodeAnalyzer:
    """Analyzes Python code for various issues."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[CodeIssue] = []
        self.ignored_paths = {
            'venv', '.venv', 'node_modules', '__pycache__', '.git',
            '.pytest_cache', '.coverage', 'htmlcov', 'site-packages'
        }

    def should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        return any(
            ignored in file_path.parts
            for ignored in self.ignored_paths
        )

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_paths]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    if not self.should_ignore_file(file_path):
                        python_files.append(file_path)

        return python_files

    def analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze a single Python file."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Parse AST for structural analysis
            try:
                tree = ast.parse(content, filename=str(file_path))
                issues.extend(self._analyze_ast(tree, file_path, lines))
            except SyntaxError as e:
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=e.lineno or 0,
                    issue_type="syntax_error",
                    severity="critical",
                    message=f"Syntax error: {e.msg}",
                    code_snippet=lines[e.lineno - 1] if e.lineno and e.lineno <= len(lines) else ""
                ))

            # Analyze code patterns
            issues.extend(self._analyze_code_patterns(content, file_path, lines))

        except Exception as e:
            issues.append(CodeIssue(
                file_path=str(file_path),
                line_number=0,
                issue_type="analysis_error",
                severity="low",
                message=f"Could not analyze file: {e}"
            ))

        return issues

    def _analyze_ast(self, tree: ast.AST, file_path: Path, lines: List[str]) -> List[CodeIssue]:
        """Analyze AST for structural issues."""
        issues = []

        class IssueVisitor(ast.NodeVisitor):
            def __init__(self, analyzer):
                self.analyzer = analyzer
                self.file_path = file_path
                self.lines = lines

            def visit_Import(self, node):
                # Check for unused imports (simplified check)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                # Check for unused imports (simplified check)
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                # Check function length
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno + 1
                    if length > 50:
                        issues.append(CodeIssue(
                            file_path=str(self.file_path),
                            line_number=node.lineno,
                            issue_type="long_function",
                            severity="medium",
                            message=f"Function '{node.name}' is too long ({length} lines)",
                            code_snippet=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
                        ))

                # Check parameter count
                if len(node.args.args) > 5:
                    issues.append(CodeIssue(
                        file_path=str(self.file_path),
                        line_number=node.lineno,
                        issue_type="too_many_parameters",
                        severity="low",
                        message=f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                        code_snippet=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
                    ))

                self.generic_visit(node)

            def visit_ClassDef(self, node):
                # Check class length
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno + 1
                    if length > 300:
                        issues.append(CodeIssue(
                            file_path=str(self.file_path),
                            line_number=node.lineno,
                            issue_type="long_class",
                            severity="medium",
                            message=f"Class '{node.name}' is too long ({length} lines)",
                            code_snippet=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
                        ))

                self.generic_visit(node)

            def visit_For(self, node):
                # Check for nested loops
                for parent in ast.walk(node):
                    if isinstance(parent, (ast.For, ast.While)) and parent != node:
                        issues.append(CodeIssue(
                            file_path=str(self.file_path),
                            line_number=node.lineno,
                            issue_type="nested_loops",
                            severity="low",
                            message="Nested loop detected - consider refactoring",
                            code_snippet=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else ""
                        ))
                        break
                self.generic_visit(node)

            def visit_Try(self, node):
                # Check for bare except
                for handler in node.handlers:
                    if handler.type is None:
                        issues.append(CodeIssue(
                            file_path=str(self.file_path),
                            line_number=handler.lineno,
                            issue_type="bare_except",
                            severity="medium",
                            message="Bare except clause - specify exception type",
                            code_snippet=self.lines[handler.lineno - 1] if handler.lineno <= len(self.lines) else ""
                        ))
                self.generic_visit(node)

        visitor = IssueVisitor(self)
        visitor.visit(tree)

        return issues

    def _analyze_code_patterns(self, content: str, file_path: Path, lines: List[str]) -> List[CodeIssue]:
        """Analyze code for common patterns and anti-patterns."""
        issues = []

        for i, line in enumerate(lines, 1):
            # Check for TODO/FIXME comments
            if re.search(r'#\s*(TODO|FIXME|HACK|XXX)', line, re.IGNORECASE):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="todo_comment",
                    severity="low",
                    message="Found TODO/FIXME comment in code",
                    code_snippet=line.strip()
                ))

            # Check for print statements (might be debugging code)
            if re.search(r'\bprint\s*\(', line) and not re.search(r'#.*print', line):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="print_statement",
                    severity="low",
                    message="Print statement found - consider using logging",
                    code_snippet=line.strip()
                ))

            # Check for potential SQL injection
            if re.search(r'(execute|cursor)\s*\(\s*[f"]\s*%', line, re.IGNORECASE):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="sql_injection_risk",
                    severity="high",
                    message="Potential SQL injection vulnerability - use parameterized queries",
                    code_snippet=line.strip()
                ))

            # Check for hardcoded passwords/secrets
            if re.search(r'(password|secret|token|key)\s*=\s*[\'"][^\'"]{8,}[\'"]', line, re.IGNORECASE):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="hardcoded_secret",
                    severity="critical",
                    message="Potential hardcoded secret/password found",
                    code_snippet=line.strip()
                ))

            # Check for long lines (PEP 8)
            if len(line) > 79 and not line.strip().startswith('#'):
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="line_too_long",
                    severity="low",
                    message=f"Line too long ({len(line)} characters)",
                    code_snippet=line.strip()
                ))

            # Check for trailing whitespace
            if line.rstrip() != line:
                issues.append(CodeIssue(
                    file_path=str(file_path),
                    line_number=i,
                    issue_type="trailing_whitespace",
                    severity="low",
                    message="Trailing whitespace found",
                    code_snippet=line.strip()
                ))

        return issues

    def run_external_tools(self, file_path: Path) -> List[CodeIssue]:
        """Run external analysis tools if available."""
        issues = []

        # Try to run pylint
        try:
            result = subprocess.run(
                ['pylint', str(file_path), '--output-format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                try:
                    pylint_output = json.loads(result.stdout)
                    for item in pylint_output:
                        issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=item.get('line', 0),
                            issue_type=f"pylint_{item.get('type', '').lower()}",
                            severity=self._map_pylint_severity(item.get('type', '')),
                            message=item.get('message', ''),
                            code_snippet=""
                        ))
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Try to run bandit for security issues
        try:
            result = subprocess.run(
                ['bandit', '-r', '-f', 'json', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                try:
                    bandit_output = json.loads(result.stdout)
                    for item in bandit_output.get('results', []):
                        issues.append(CodeIssue(
                            file_path=str(file_path),
                            line_number=item.get('line_number', 0),
                            issue_type=f"bandit_{item.get('test_id', '')}",
                            severity=self._map_bandit_severity(item.get('issue_severity', '')),
                            message=item.get('issue_text', ''),
                            code_snippet=""
                        ))
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return issues

    def _map_pylint_severity(self, pylint_type: str) -> str:
        """Map pylint message type to severity."""
        mapping = {
            'error': 'high',
            'warning': 'medium',
            'convention': 'low',
            'refactor': 'low',
            'info': 'low'
        }
        return mapping.get(pylint_type.lower(), 'low')

    def _map_bandit_severity(self, bandit_severity: str) -> str:
        """Map bandit severity to our severity levels."""
        mapping = {
            'HIGH': 'high',
            'MEDIUM': 'medium',
            'LOW': 'low'
        }
        return mapping.get(bandit_severity.upper(), 'low')

    def analyze_project(self) -> Dict[str, Any]:
        """Analyze the entire project."""
        print(f"Analyzing Python files in {self.project_root}...")

        python_files = self.find_python_files()
        print(f"Found {len(python_files)} Python files")

        for file_path in python_files:
            print(f"Analyzing {file_path}...")

            # Basic analysis
            file_issues = self.analyze_file(file_path)
            self.issues.extend(file_issues)

            # External tools analysis
            external_issues = self.run_external_tools(file_path)
            self.issues.extend(external_issues)

        # Generate report
        report = self._generate_report()

        return report

    def _generate_report(self) -> Dict[str, Any]:
        """Generate analysis report."""
        # Group issues by type
        issues_by_type = defaultdict(list)
        issues_by_severity = defaultdict(list)
        issues_by_file = defaultdict(list)

        for issue in self.issues:
            issues_by_type[issue.issue_type].append(issue)
            issues_by_severity[issue.severity].append(issue)
            issues_by_file[issue.file_path].append(issue)

        # Count statistics
        total_issues = len(self.issues)
        severity_counts = {k: len(v) for k, v in issues_by_severity.items()}
        type_counts = {k: len(v) for k, v in issues_by_type.items()}
        file_counts = {k: len(v) for k, v in issues_by_file.items()}

        # Top problematic files
        top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Most common issue types
        common_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'summary': {
                'total_issues': total_issues,
                'severity_counts': severity_counts,
                'files_analyzed': len(issues_by_file),
                'critical_issues': len(issues_by_severity.get('critical', [])),
                'high_issues': len(issues_by_severity.get('high', [])),
                'medium_issues': len(issues_by_severity.get('medium', [])),
                'low_issues': len(issues_by_severity.get('low', []))
            },
            'top_problematic_files': top_files,
            'most_common_issues': common_types,
            'detailed_issues_by_file': {
                file_path: [
                    {
                        'line': issue.line_number,
                        'type': issue.issue_type,
                        'severity': issue.severity,
                        'message': issue.message,
                        'code': issue.code_snippet
                    }
                    for issue in issues
                ]
                for file_path, issues in issues_by_file.items()
            }
        }


def main():
    """Main entry point."""
    project_root = "/home/thomas/kyros-praxis"

    analyzer = PythonCodeAnalyzer(project_root)
    report = analyzer.analyze_project()

    # Print summary
    print("\n" + "="*60)
    print("PYTHON CODE ANALYSIS REPORT")
    print("="*60)

    summary = report['summary']
    print(f"\nTotal Issues Found: {summary['total_issues']}")
    print(f"Files Analyzed: {summary['files_analyzed']}")
    print(f"\nSeverity Distribution:")
    print(f"  Critical: {summary['critical_issues']}")
    print(f"  High: {summary['high_issues']}")
    print(f"  Medium: {summary['medium_issues']}")
    print(f"  Low: {summary['low_issues']}")

    print("\nTop 10 Most Problematic Files:")
    for file_path, count in report['top_problematic_files']:
        print(f"  {file_path}: {count} issues")

    print("\nTop 10 Most Common Issues:")
    for issue_type, count in report['most_common_issues']:
        print(f"  {issue_type}: {count} occurrences")

    # Save detailed report
    with open('/home/thomas/kyros-praxis/python_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to: /home/thomas/kyros-praxis/python_analysis_report.json")

    # Print critical and high severity issues
    print("\n" + "="*60)
    print("CRITICAL AND HIGH SEVERITY ISSUES")
    print("="*60)

    critical_high_issues = [
        issue for issue in analyzer.issues
        if issue.severity in ['critical', 'high']
    ]

    if critical_high_issues:
        for issue in critical_high_issues:
            print(f"\nFile: {issue.file_path}")
            print(f"Line: {issue.line_number}")
            print(f"Type: {issue.issue_type}")
            print(f"Severity: {issue.severity}")
            print(f"Message: {issue.message}")
            if issue.code_snippet:
                print(f"Code: {issue.code_snippet}")
    else:
        print("No critical or high severity issues found.")


if __name__ == "__main__":
    main()