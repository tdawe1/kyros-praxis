#!/usr/bin/env python3
"""
State Update Script for Kyros Development Workflow

This script provides ETag-guarded updates to task state and emits events
to the collaboration/events/events.jsonl log. Used by Orchestrator and Integrator modes.

Usage:
  python scripts/state_update.py TDS-123 in_progress --if-match "abc123"
  python scripts/state_update.py TDS-456 done --if-match "def456"
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Constants
TASKS_FILE = Path("collaboration/state/tasks.json")
EVENTS_FILE = Path("collaboration/events/events.jsonl")
VALID_STATUSES = ["todo", "in_progress", "review", "approved", "merging", "done", "blocked", "security_audit", "security_review"]


def calculate_etag(data: Dict[str, Any]) -> str:
    """Calculate SHA256 ETag for the given data."""
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode()).hexdigest()


def read_tasks_file() -> Dict[str, Any]:
    """Read and parse the tasks.json file."""
    if not TASKS_FILE.exists():
        print(f"Error: Tasks file not found at {TASKS_FILE}")
        sys.exit(1)
    
    try:
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing tasks.json: {e}")
        sys.exit(1)


def write_tasks_file(data: Dict[str, Any]) -> None:
    """Write data to tasks.json file."""
    try:
        with open(TASKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing tasks.json: {e}")
        sys.exit(1)


def emit_event(event_type: str, task_id: str, old_status: str, new_status: str, user: str = "system", metadata: Optional[Dict[str, Any]] = None) -> None:
    """Emit an event to the events log."""
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    base_metadata = {
        "source": "state_update.py",
        "version": "1.0"
    }
    
    if metadata:
        base_metadata.update(metadata)
    
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "task_id": task_id,
        "old_status": old_status,
        "new_status": new_status,
        "user": user,
        "metadata": base_metadata
    }
    
    with open(EVENTS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(event) + '\n')


def find_task_by_id(tasks_data: Dict[str, Any], task_id: str) -> Optional[Dict[str, Any]]:
    """Find a task by its ID."""
    for task in tasks_data.get("tasks", []):
        if task.get("id") == task_id:
            return task
    return None


def validate_status_transition(old_status: str, new_status: str) -> bool:
    """Validate that the status transition is allowed."""
    # Define allowed transitions
    transitions = {
        "todo": ["in_progress", "blocked", "security_audit"],
        "in_progress": ["review", "blocked", "todo", "security_audit"],
        "review": ["approved", "blocked", "in_progress", "security_audit"],
        "approved": ["merging", "blocked", "security_audit"],
        "merging": ["done", "blocked", "approved", "security_audit"],
        "done": [],  # Terminal state
        "blocked": ["todo", "in_progress", "security_audit"],
        "security_audit": ["security_review", "blocked", "in_progress"],
        "security_review": ["review", "blocked", "in_progress"]
    }
    
    return new_status in transitions.get(old_status, [])


def update_task_status(task_id: str, new_status: str, if_match: str, user: str = "system") -> None:
    """Update task status with ETag validation."""
    # Read current state
    tasks_data = read_tasks_file()
    current_etag = calculate_etag(tasks_data)
    
    # Validate ETag
    if if_match and current_etag != if_match:
        print(f"ETag mismatch! Expected: {if_match}, Actual: {current_etag}")
        print("Another process has modified the tasks file. Please fetch the latest and try again.")
        sys.exit(1)
    
    # Find and update task
    task = find_task_by_id(tasks_data, task_id)
    if not task:
        print(f"Error: Task {task_id} not found")
        sys.exit(1)
    
    old_status = task.get("status")
    
    # Validate new status
    if new_status not in VALID_STATUSES:
        print(f"Error: Invalid status '{new_status}'. Valid statuses: {', '.join(VALID_STATUSES)}")
        sys.exit(1)
    
    # Validate transition
    if not validate_status_transition(old_status, new_status):
        print(f"Error: Invalid status transition from '{old_status}' to '{new_status}'")
        sys.exit(1)
    
    # Update task
    task["status"] = new_status
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Write back with new ETag
    write_tasks_file(tasks_data)
    new_etag = calculate_etag(tasks_data)
    
    # Emit event
    emit_event("status_changed", task_id, old_status, new_status, user)
    
    # Print success message
    print(f"✓ Updated task {task_id}: {old_status} → {new_status}")
    print(f"  New ETag: {new_etag}")


def add_security_findings(task_id: str, findings: List[Dict[str, Any]], if_match: str, user: str = "security_audit") -> None:
    """Add security findings to a task."""
    tasks_data = read_tasks_file()
    current_etag = calculate_etag(tasks_data)
    
    # Validate ETag
    if if_match and current_etag != if_match:
        print(f"ETag mismatch! Expected: {if_match}, Actual: {current_etag}")
        print("Another process has modified the tasks file. Please fetch the latest and try again.")
        sys.exit(1)
    
    task = find_task_by_id(tasks_data, task_id)
    if not task:
        print(f"Error: Task {task_id} not found")
        sys.exit(1)
    
    # Add or update security findings
    if "security_findings" not in task:
        task["security_findings"] = []
    
    task["security_findings"].extend(findings)
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Calculate severity summary
    critical_count = sum(1 for f in findings if f.get("severity") == "Critical")
    high_count = sum(1 for f in findings if f.get("severity") == "High")
    medium_count = sum(1 for f in findings if f.get("severity") == "Medium")
    low_count = sum(1 for f in findings if f.get("severity") == "Low")
    
    # Write back with new ETag
    write_tasks_file(tasks_data)
    new_etag = calculate_etag(tasks_data)
    
    # Emit security audit event
    emit_event(
        "security_findings_added",
        task_id,
        task.get("status"),
        task.get("status"),
        user,
        metadata={
            "findings_count": len(findings),
            "severity_summary": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            }
        }
    )
    
    # Print success message
    print(f"✓ Added {len(findings)} security findings to task {task_id}")
    print(f"  Critical: {critical_count}, High: {high_count}, Medium: {medium_count}, Low: {low_count}")
    print(f"  New ETag: {new_etag}")


def update_security_status(task_id: str, security_status: str, if_match: str, user: str = "security_audit") -> None:
    """Update security-specific status for a task."""
    tasks_data = read_tasks_file()
    current_etag = calculate_etag(tasks_data)
    
    # Validate ETag
    if if_match and current_etag != if_match:
        print(f"ETag mismatch! Expected: {if_match}, Actual: {current_etag}")
        print("Another process has modified the tasks file. Please fetch the latest and try again.")
        sys.exit(1)
    
    task = find_task_by_id(tasks_data, task_id)
    if not task:
        print(f"Error: Task {task_id} not found")
        sys.exit(1)
    
    old_status = task.get("status")
    
    # Validate security status
    valid_security_statuses = ["security_audit", "security_review"]
    if security_status not in valid_security_statuses:
        print(f"Error: Invalid security status '{security_status}'. Valid statuses: {', '.join(valid_security_statuses)}")
        sys.exit(1)
    
    # Validate transition
    if not validate_status_transition(old_status, security_status):
        print(f"Error: Invalid status transition from '{old_status}' to '{security_status}'")
        sys.exit(1)
    
    # Update task
    task["status"] = security_status
    task["security_status"] = security_status
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Write back with new ETag
    write_tasks_file(tasks_data)
    new_etag = calculate_etag(tasks_data)
    
    # Emit security status event
    emit_event(
        "security_status_changed",
        task_id,
        old_status,
        security_status,
        user,
        metadata={"security_status": security_status}
    )
    
    # Print success message
    print(f"✓ Updated security status for task {task_id}: {old_status} → {security_status}")
    print(f"  New ETag: {new_etag}")


def list_tasks() -> None:
    """List all tasks with their current status."""
    tasks_data = read_tasks_file()
    current_etag = calculate_etag(tasks_data)
    
    print(f"Current tasks (ETag: {current_etag}):")
    print("-" * 80)
    
    for task in tasks_data.get("tasks", []):
        task_id = task.get("id", "unknown")
        title = task.get("title", "Untitled")
        status = task.get("status", "unknown")
        security_status = task.get("security_status", "none")
        
        # Show security findings if present
        findings_count = len(task.get("security_findings", []))
        security_info = f" ({findings_count} findings)" if findings_count > 0 else ""
        
        print(f"{task_id:12} {status:12} {title}{security_info}")
        if security_status != "none":
            print(f"{'':12} {'':12} Security: {security_status}")


def main():
    parser = argparse.ArgumentParser(
        description="Update task status with ETag validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/state_update.py TDS-123 in_progress --if-match "abc123"
  python scripts/state_update.py TDS-456 done --if-match "def456" --user "integrator"
  python scripts/state_update.py --list
  python scripts/state_update.py TDS-789 review --show-etag
  
Security Audit Commands:
  python scripts/state_update.py TDS-123 security_audit --if-match "abc123"
  python scripts/state_update.py --security-findings TDS-123 findings.json --if-match "abc123"
        """
    )
    
    parser.add_argument("task_id", nargs="?", help="Task ID to update (e.g., TDS-123)")
    parser.add_argument("status", nargs="?", help=f"New status: {', '.join(VALID_STATUSES)}")
    parser.add_argument("--if-match", help="ETag for optimistic concurrency control")
    parser.add_argument("--user", default="system", help="User making the change")
    parser.add_argument("--list", action="store_true", help="List all tasks")
    parser.add_argument("--show-etag", action="store_true", help="Show current ETag and exit")
    parser.add_argument("--security-findings", help="Add security findings from JSON file")
    parser.add_argument("--security-status", help="Set security-specific status (security_audit, security_review)")
    
    args = parser.parse_args()
    
    # List tasks mode
    if args.list:
        list_tasks()
        return
    
    # Show ETag mode
    if args.show_etag:
        tasks_data = read_tasks_file()
        etag = calculate_etag(tasks_data)
        print(f"Current ETag: {etag}")
        return
    
    # Security findings mode
    if args.security_findings:
        if not args.task_id:
            parser.error("task_id is required when using --security-findings")
        if not args.if_match:
            parser.error("--if-match is required when using --security-findings")
        
        # Load findings from JSON file
        try:
            with open(args.security_findings, 'r', encoding='utf-8') as f:
                findings_data = json.load(f)
            
            # Handle different JSON formats
            if isinstance(findings_data, list):
                findings = findings_data
            elif isinstance(findings_data, dict) and "security_findings" in findings_data:
                findings = findings_data["security_findings"]
            else:
                print(f"Error: Invalid findings format in {args.security_findings}")
                sys.exit(1)
            
            add_security_findings(args.task_id, findings, args.if_match, args.user)
            return
            
        except FileNotFoundError:
            print(f"Error: Findings file not found: {args.security_findings}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing findings file: {e}")
            sys.exit(1)
    
    # Security status mode
    if args.security_status:
        if not args.task_id:
            parser.error("task_id is required when using --security-status")
        if not args.if_match:
            parser.error("--if-match is required when using --security-status")
        
        update_security_status(args.task_id, args.security_status, args.if_match, args.user)
        return
    
    # Update mode
    if not args.task_id or not args.status:
        parser.error("task_id and status are required unless --list or --show-etag is used")
    
    update_task_status(args.task_id, args.status, args.if_match, args.user)


if __name__ == "__main__":
    main()