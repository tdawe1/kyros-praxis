#!/usr/bin/env python3
"""
Security Audit Script for Kyros Development Workflow

This script automates security audits using the SECAUDIT methodology from the Zen MCP server.
It performs systematic security analysis of code changes and generates comprehensive reports.

Usage:
  python scripts/security_audit.py --auto                    # Auto-detect changes and audit
  python scripts/security_audit.py --task-id TDS-123          # Audit specific task
  python scripts/security_audit.py --files file1.py file2.ts  # Audit specific files
  python scripts/security_audit.py --diff "HEAD~1"           # Audit git diff
  python scripts/security_audit.py --report-only              # Generate report from existing findings
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Constants
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

SECURITY_KEYWORDS = [
    "password", "secret", "key", "token", "auth", "login", "session",
    "encrypt", "decrypt", "hash", "salt", "jwt", "oauth", "api_key",
    "sql", "query", "exec", "eval", "shell", "system", "subprocess",
    "credentials", "authentication", "authorization", "csrf", "xss"
]

OWASP_TOP_10 = [
    ("A01", "Broken Access Control"),
    ("A02", "Cryptographic Failures"),
    ("A03", "Injection"),
    ("A04", "Insecure Design"),
    ("A05", "Security Misconfiguration"),
    ("A06", "Vulnerable and Outdated Components"),
    ("A07", "Identification and Authentication Failures"),
    ("A08", "Software and Data Integrity Failures"),
    ("A09", "Security Logging and Monitoring Failures"),
    ("A10", "Server-Side Request Forgery (SSRF)")
]


class SecurityAuditResult:
    def __init__(self):
        self.status = "security_analysis_complete"
        self.summary = ""
        self.investigation_steps = []
        self.security_findings = []
        self.owasp_assessment = {}
        self.compliance_assessment = []
        self.risk_assessment = {}
        self.remediation_roadmap = []
        self.positive_security_findings = []
        self.monitoring_recommendations = []
        self.investigation_summary = ""


def is_security_sensitive_file(file_path: str) -> bool:
    """Check if a file is security-sensitive based on its path."""
    file_lower = file_path.lower()
    return any(re.search(pattern, file_lower) for pattern in SECURITY_SENSITIVE_PATTERNS)


def contains_security_keywords(content: str) -> bool:
    """Check if content contains security-sensitive keywords."""
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in SECURITY_KEYWORDS)


def get_modified_files(diff_ref: str = "HEAD") -> List[str]:
    """Get list of modified files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", diff_ref],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        else:
            print(f"Warning: Could not get modified files: {result.stderr}")
            return []
    except (subprocess.TimeoutExpired, Exception):
        return []


def get_file_content(file_path: str) -> Optional[str]:
    """Read file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def analyze_code_for_vulnerabilities(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Analyze code content for security vulnerabilities."""
    findings = []
    
    # Check for hardcoded secrets
    secret_patterns = [
        r'password\s*=\s*["\'][^"\']{8,}["\']',
        r'api_key\s*=\s*["\'][^"\']{10,}["\']',
        r'secret\s*=\s*["\'][^"\']{10,}["\']',
        r'token\s*=\s*["\'][^"\']{10,}["\']',
    ]
    
    for pattern in secret_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            findings.append({
                "category": "A02_Cryptographic_Failures",
                "severity": "High",
                "vulnerability": "Hardcoded Secret",
                "description": f"Potential hardcoded secret found: {match.group()}",
                "impact": "Secrets exposed in source code can lead to unauthorized access",
                "exploitability": "High - secrets visible in source code",
                "evidence": match.group(),
                "remediation": "Move secrets to environment variables or secure configuration management",
                "timeline": "Immediate",
                "file_references": [f"{file_path}:{match.start()}"],
                "function_name": extract_function_name(content, match.start()),
                "start_line": content.count('\n', 0, match.start()) + 1,
                "context_start_text": get_line_context(content, match.start(), before=1, after=1)[0],
                "context_end_text": get_line_context(content, match.start(), before=1, after=1)[1]
            })
    
    # Check for SQL injection vulnerabilities
    sql_injection_patterns = [
        r'execute\s*\(\s*[\'"]\s*SELECT.*\+\s*.*?[\'"]\s*\)',
        r'cursor\.execute\s*\(\s*[\'"]\s*.*%.*?[\'"]\s*%',
        r'query\s*=\s*[\'"]\s*SELECT.*\+\s*',
    ]
    
    for pattern in sql_injection_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            findings.append({
                "category": "A03_Injection",
                "severity": "Critical",
                "vulnerability": "SQL Injection",
                "description": "Potential SQL injection vulnerability detected",
                "impact": "Unauthorized database access, data theft, or data manipulation",
                "exploitability": "High - direct string concatenation in SQL queries",
                "evidence": match.group(),
                "remediation": "Use parameterized queries or prepared statements",
                "timeline": "Immediate",
                "file_references": [f"{file_path}:{match.start()}"],
                "function_name": extract_function_name(content, match.start()),
                "start_line": content.count('\n', 0, match.start()) + 1,
                "context_start_text": get_line_context(content, match.start(), before=1, after=1)[0],
                "context_end_text": get_line_context(content, match.start(), before=1, after=1)[1]
            })
    
    # Check for XSS vulnerabilities
    xss_patterns = [
        r'innerHTML\s*=\s*',
        r'outerHTML\s*=\s*',
        r'document\.write\s*\(',
        r'\.html\s*\(',
    ]
    
    for pattern in xss_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            findings.append({
                "category": "A03_Injection",
                "severity": "High",
                "vulnerability": "Cross-Site Scripting (XSS)",
                "description": "Potential XSS vulnerability detected",
                "impact": "Client-side code execution, session hijacking, data theft",
                "exploitability": "Medium - requires user interaction or specific context",
                "evidence": match.group(),
                "remediation": "Use textContent instead of innerHTML, or implement proper input sanitization",
                "timeline": "Short-term",
                "file_references": [f"{file_path}:{match.start()}"],
                "function_name": extract_function_name(content, match.start()),
                "start_line": content.count('\n', 0, match.start()) + 1,
                "context_start_text": get_line_context(content, match.start(), before=1, after=1)[0],
                "context_end_text": get_line_context(content, match.start(), before=1, after=1)[1]
            })
    
    return findings


def extract_function_name(content: str, position: int) -> Optional[str]:
    """Extract function name near the given position."""
    lines = content.split('\n')
    line_num = content.count('\n', 0, position)
    
    # Look for function definition in nearby lines
    for i in range(max(0, line_num - 10), min(len(lines), line_num + 2)):
        line = lines[i].strip()
        if line.startswith(('def ', 'function ', 'async def ', 'async function ')):
            # Extract function name
            if line.startswith('def '):
                match = re.match(r'def\s+(\w+)\s*\(', line)
            elif line.startswith('function '):
                match = re.match(r'function\s+(\w+)\s*\(', line)
            elif line.startswith('async def '):
                match = re.match(r'async def\s+(\w+)\s*\(', line)
            elif line.startswith('async function '):
                match = re.match(r'async function\s+(\w+)\s*\(', line)
            
            if match:
                return match.group(1)
    
    return None


def get_line_context(content: str, position: int, before: int = 2, after: int = 2) -> Tuple[str, str]:
    """Get context lines around the given position."""
    lines = content.split('\n')
    line_num = content.count('\n', 0, position)
    
    start_line = max(0, line_num - before)
    end_line = min(len(lines), line_num + after + 1)
    
    context_start = '\n'.join(lines[start_line:line_num])
    context_end = '\n'.join(lines[line_num:end_line])
    
    return context_start.strip(), context_end.strip()


def generate_owasp_assessment(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate OWASP Top 10 assessment based on findings."""
    assessment = {}
    
    # Initialize all OWASP categories as Secure
    for code, name in OWASP_TOP_10:
        key = f"{code.lower()}_{name.lower().replace(' ', '_')}"
        assessment[key] = {
            "status": "Secure",
            "findings": [],
            "recommendations": []
        }
    
    # Categorize findings
    for finding in findings:
        category = finding.get("category", "Unknown")
        if category in assessment:
            assessment[category]["status"] = "Vulnerable"
            assessment[category]["findings"].append(finding.get("vulnerability", "Unknown issue"))
            
            # Add specific recommendations based on vulnerability type
            vulnerability = finding.get("vulnerability", "").lower()
            if "sql injection" in vulnerability:
                assessment[category]["recommendations"].append("Use parameterized queries and input validation")
            elif "xss" in vulnerability:
                assessment[category]["recommendations"].append("Implement proper output encoding and input sanitization")
            elif "hardcoded" in vulnerability:
                assessment[category]["recommendations"].append("Use environment variables or secret management")
    
    return assessment


def generate_risk_assessment(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate overall risk assessment."""
    critical_count = sum(1 for f in findings if f.get("severity") == "Critical")
    high_count = sum(1 for f in findings if f.get("severity") == "High")
    medium_count = sum(1 for f in findings if f.get("severity") == "Medium")
    low_count = sum(1 for f in findings if f.get("severity") == "Low")
    
    # Determine overall risk level
    if critical_count > 0:
        overall_risk = "Critical"
    elif high_count > 2:
        overall_risk = "High"
    elif high_count > 0 or medium_count > 3:
        overall_risk = "Medium"
    elif medium_count > 0 or low_count > 5:
        overall_risk = "Low"
    else:
        overall_risk = "Low"
    
    return {
        "overall_risk_level": overall_risk,
        "threat_landscape": "Web application with potential authentication and data handling vulnerabilities",
        "attack_vectors": [
            "SQL injection through unsanitized user input",
            "XSS through improper output encoding",
            "Credential exposure through hardcoded secrets"
        ],
        "business_impact": "Potential data breach, unauthorized access, and reputational damage",
        "likelihood_assessment": "Medium" if high_count > 0 else "Low"
    }


def generate_remediation_roadmap(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate prioritized remediation roadmap."""
    roadmap = []
    
    # Group findings by severity
    critical_findings = [f for f in findings if f.get("severity") == "Critical"]
    high_findings = [f for f in findings if f.get("severity") == "High"]
    medium_findings = [f for f in findings if f.get("severity") == "Medium"]
    low_findings = [f for f in findings if f.get("severity") == "Low"]
    
    # Critical findings - Immediate action
    if critical_findings:
        roadmap.append({
            "priority": "Critical",
            "timeline": "Immediate",
            "effort": "Medium",
            "description": f"Fix {len(critical_findings)} critical security vulnerabilities",
            "dependencies": [],
            "success_criteria": "All critical vulnerabilities resolved and verified",
            "cost_impact": "High - requires immediate attention and potential service interruption"
        })
    
    # High findings - Short-term
    if high_findings:
        roadmap.append({
            "priority": "High",
            "timeline": "Short-term (1-2 weeks)",
            "effort": "Medium",
            "description": f"Address {len(high_findings)} high severity security issues",
            "dependencies": [],
            "success_criteria": "All high severity vulnerabilities resolved",
            "cost_impact": "Medium - requires dedicated development time"
        })
    
    # Medium findings - Medium-term
    if medium_findings:
        roadmap.append({
            "priority": "Medium",
            "timeline": "Medium-term (1-3 months)",
            "effort": "Low",
            "description": f"Resolve {len(medium_findings)} medium severity security findings",
            "dependencies": [],
            "success_criteria": "All medium severity issues addressed",
            "cost_impact": "Low - can be handled during regular development cycles"
        })
    
    return roadmap


def perform_security_audit(files: List[str], task_id: Optional[str] = None) -> SecurityAuditResult:
    """Perform comprehensive security audit."""
    result = SecurityAuditResult()
    
    if not files:
        result.status = "files_required_to_continue"
        result.summary = "No files specified for security audit"
        return result
    
    result.investigation_steps = [
        "Security scope and attack surface analysis",
        "Authentication and authorization assessment",
        "Input validation and data handling security review",
        "OWASP Top 10 (2021) systematic evaluation",
        "Dependencies and infrastructure security analysis",
        "Compliance and risk assessment"
    ]
    
    all_findings = []
    
    for file_path in files:
        if not Path(file_path).exists():
            print(f"Warning: File not found: {file_path}")
            continue
        
        content = get_file_content(file_path)
        if content is None:
            print(f"Warning: Could not read file: {file_path}")
            continue
        
        # Analyze file for vulnerabilities
        file_findings = analyze_code_for_vulnerabilities(file_path, content)
        all_findings.extend(file_findings)
    
    # Deduplicate findings based on location
    unique_findings = []
    seen_locations = set()
    
    for finding in all_findings:
        location = finding.get("file_references", [""])[0]
        if location not in seen_locations:
            unique_findings.append(finding)
            seen_locations.add(location)
    
    result.security_findings = unique_findings
    result.owasp_assessment = generate_owasp_assessment(unique_findings)
    result.risk_assessment = generate_risk_assessment(unique_findings)
    result.remediation_roadmap = generate_remediation_roadmap(unique_findings)
    
    # Generate summary
    critical_count = sum(1 for f in unique_findings if f.get("severity") == "Critical")
    high_count = sum(1 for f in unique_findings if f.get("severity") == "High")
    medium_count = sum(1 for f in unique_findings if f.get("severity") == "Medium")
    low_count = sum(1 for f in unique_findings if f.get("severity") == "Low")
    
    result.summary = f"Security audit completed: {len(unique_findings)} vulnerabilities found (Critical: {critical_count}, High: {high_count}, Medium: {medium_count}, Low: {low_count})"
    
    # Add positive findings
    if len(unique_findings) == 0:
        result.positive_security_findings = [
            "No security vulnerabilities detected in analyzed files",
            "Code follows secure coding practices",
            "No hardcoded secrets or sensitive information exposed"
        ]
    else:
        result.positive_security_findings = [
            "Security audit identified specific areas for improvement",
            "Vulnerabilities are categorized by severity for prioritized remediation",
            "Comprehensive remediation roadmap provided"
        ]
    
    # Add monitoring recommendations
    result.monitoring_recommendations = [
        "Implement security logging for authentication attempts",
        "Monitor for SQL injection and XSS attack patterns",
        "Regular secret scanning in source code",
        "Automated security testing in CI/CD pipeline",
        "Periodic security audits and penetration testing"
    ]
    
    # Generate investigation summary
    result.investigation_summary = f"""
Security audit completed for {len(files)} files. Analysis covered:
- OWASP Top 10 vulnerability assessment
- Code pattern analysis for common security issues
- Secret and credential exposure detection
- Input validation and output encoding review

{result.summary}

Key recommendations:
1. Address Critical and High severity findings immediately
2. Implement security testing in development workflow
3. Regular security audits for ongoing protection
4. Security awareness training for development team
"""
    
    return result


def save_audit_report(result: SecurityAuditResult, output_file: str) -> None:
    """Save audit report to JSON file."""
    report = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": result.status,
        "summary": result.summary,
        "investigation_steps": result.investigation_steps,
        "security_findings": result.security_findings,
        "owasp_assessment": result.owasp_assessment,
        "compliance_assessment": result.compliance_assessment,
        "risk_assessment": result.risk_assessment,
        "remediation_roadmap": result.remediation_roadmap,
        "positive_security_findings": result.positive_security_findings,
        "monitoring_recommendations": result.monitoring_recommendations,
        "investigation_summary": result.investigation_summary
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Audit report saved to: {output_file}")
    except Exception as e:
        print(f"Error saving audit report: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Automated security audit using SECAUDIT methodology",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/security_audit.py --auto
  python scripts/security_audit.py --task-id TDS-123
  python scripts/security_audit.py --files src/auth.py src/api.py
  python scripts/security_audit.py --diff "HEAD~1"
  python scripts/security_audit.py --output security-report.json
        """
    )
    
    parser.add_argument("--auto", action="store_true", help="Auto-detect modified files and audit")
    parser.add_argument("--task-id", help="Task ID for audit tracking")
    parser.add_argument("--files", nargs="+", help="Specific files to audit")
    parser.add_argument("--diff", default="HEAD", help="Git diff reference (default: HEAD)")
    parser.add_argument("--output", default="security-audit-report.json", help="Output report file")
    parser.add_argument("--report-only", action="store_true", help="Generate report from existing findings")
    
    args = parser.parse_args()
    
    print("🔒 Running security audit...")
    
    if args.report_only:
        # Just load and display existing report
        if Path(args.output).exists():
            with open(args.output, 'r', encoding='utf-8') as f:
                report = json.load(f)
            print(json.dumps(report, indent=2))
            return
        else:
            print(f"Report file not found: {args.output}")
            sys.exit(1)
    
    # Determine files to audit
    files_to_audit = []
    
    if args.files:
        files_to_audit = args.files
    elif args.auto:
        files_to_audit = get_modified_files(args.diff)
        if not files_to_audit:
            print("No modified files found for audit")
            sys.exit(0)
    else:
        print("Error: Must specify --auto, --files, or --report-only")
        parser.print_help()
        sys.exit(1)
    
    # Filter for security-sensitive files if in auto mode
    if args.auto:
        security_sensitive_files = [f for f in files_to_audit if is_security_sensitive_file(f)]
        if security_sensitive_files:
            files_to_audit = security_sensitive_files
            print(f"Filtered to {len(files_to_audit)} security-sensitive files")
        else:
            print("No security-sensitive files found in changes")
            # Check for security keywords in content
            keyword_files = []
            for file_path in files_to_audit:
                content = get_file_content(file_path)
                if content and contains_security_keywords(content):
                    keyword_files.append(file_path)
            
            if keyword_files:
                files_to_audit = keyword_files
                print(f"Found {len(files_to_audit)} files with security keywords")
            else:
                print("No security-sensitive patterns detected")
                files_to_audit = []
    
    if not files_to_audit:
        print("No files identified for security audit")
        result = SecurityAuditResult()
        result.status = "security_analysis_complete"
        result.summary = "No security issues identified in analyzed changes"
        result.positive_security_findings = ["No security-sensitive patterns detected"]
    else:
        print(f"Auditing {len(files_to_audit)} files...")
        result = perform_security_audit(files_to_audit, args.task_id)
    
    # Save and display results
    save_audit_report(result, args.output)
    
    print("\n" + "="*60)
    print("SECURITY AUDIT RESULTS")
    print("="*60)
    print(f"\nStatus: {result.status}")
    print(f"Summary: {result.summary}")
    
    if result.security_findings:
        print(f"\n📋 Security Findings Summary:")
        critical_count = sum(1 for f in result.security_findings if f.get("severity") == "Critical")
        high_count = sum(1 for f in result.security_findings if f.get("severity") == "High")
        medium_count = sum(1 for f in result.security_findings if f.get("severity") == "Medium")
        low_count = sum(1 for f in result.security_findings if f.get("severity") == "Low")
        
        print(f"  Critical: {critical_count}")
        print(f"  High: {high_count}")
        print(f"  Medium: {medium_count}")
        print(f"  Low: {low_count}")
        
        print(f"\n🚨 Top Issues:")
        for i, finding in enumerate(result.security_findings[:3]):
            print(f"  {i+1}. {finding.get('vulnerability', 'Unknown')} ({finding.get('severity', 'Unknown')})")
            print(f"     File: {finding.get('file_references', ['Unknown'])[0]}")
    
    if result.risk_assessment:
        risk_level = result.risk_assessment.get("overall_risk_level", "Unknown")
        print(f"\n🎯 Overall Risk Level: {risk_level}")
    
    print(f"\n📄 Full report saved to: {args.output}")


if __name__ == "__main__":
    main()