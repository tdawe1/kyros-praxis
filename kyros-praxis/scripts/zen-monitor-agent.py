#!/usr/bin/env python3
"""
Zen MCP Monitoring Agent

Continuously monitors Zen MCP for new agent registrations, session creations,
context additions, and agent status changes. Reports only new information
every 10 seconds.
"""

import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from subprocess import Popen, PIPE, STDOUT

# Add the integrations path to import from the local zen-mcp
sys.path.insert(0, str(Path(__file__).parent.parent / "integrations" / "zen-mcp"))

try:
    from main import (
        read_json, AGENTS_FILE, SESSIONS_FILE, CONTEXT_DIR, 
        context_file, canon, etag, now_ms
    )
except ImportError:
    print("Error: Could not import from zen-mcp integration", file=sys.stderr)
    sys.exit(1)


class ZenMonitor:
    def __init__(self, poll_interval: int = 10):
        self.poll_interval = poll_interval
        self.last_agents_etag = None
        self.last_sessions_etag = None
        self.last_context_timestamps: Dict[str, int] = {}
        self.agent_cache: Dict[str, Dict[str, Any]] = {}
        self.session_cache: Dict[str, Dict[str, Any]] = {}
        
    def log_change(self, change_type: str, details: str):
        """Log a change with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {change_type}: {details}")
    
    def check_agents(self) -> bool:
        """Check for new or updated agents"""
        try:
            agents_data, current_etag = read_json(AGENTS_FILE)
            
            if not isinstance(agents_data, list):
                agents_data = []
            
            # First run - just cache
            if self.last_agents_etag is None:
                self.last_agents_etag = current_etag
                self.agent_cache = {agent["id"]: agent for agent in agents_data}
                return False
            
            # No changes
            if current_etag == self.last_agents_etag:
                return False
            
            # Find changes
            current_agents = {agent["id"]: agent for agent in agents_data}
            changes_found = False
            
            # Check for new agents
            for agent_id, agent in current_agents.items():
                if agent_id not in self.agent_cache:
                    self.log_change("NEW_AGENT", 
                        f"{agent.get('name', agent_id)} (ID: {agent_id}) "
                        f"Capabilities: {agent.get('capabilities', [])}")
                    changes_found = True
            
            # Check for updated agents
            for agent_id, agent in current_agents.items():
                if agent_id in self.agent_cache:
                    old_agent = self.agent_cache[agent_id]
                    if agent.get("updatedAt", 0) > old_agent.get("updatedAt", 0):
                        self.log_change("UPDATED_AGENT",
                            f"{agent.get('name', agent_id)} (ID: {agent_id}) "
                            f"Capabilities: {agent.get('capabilities', [])}")
                        changes_found = True
            
            # Check for removed agents
            for agent_id in self.agent_cache:
                if agent_id not in current_agents:
                    self.log_change("REMOVED_AGENT", 
                        f"{self.agent_cache[agent_id].get('name', agent_id)} (ID: {agent_id})")
                    changes_found = True
            
            # Update cache
            self.last_agents_etag = current_etag
            self.agent_cache = current_agents
            
            return changes_found
            
        except Exception as e:
            print(f"Error checking agents: {e}", file=sys.stderr)
            return False
    
    def check_sessions(self) -> bool:
        """Check for new or updated sessions"""
        try:
            sessions_data, current_etag = read_json(SESSIONS_FILE)
            
            if not isinstance(sessions_data, dict) or "sessions" not in sessions_data:
                sessions_data = {"sessions": []}
            
            sessions_list = sessions_data["sessions"]
            
            # First run - just cache
            if self.last_sessions_etag is None:
                self.last_sessions_etag = current_etag
                self.session_cache = {session["id"]: session for session in sessions_list}
                return False
            
            # No changes
            if current_etag == self.last_sessions_etag:
                return False
            
            # Find changes
            current_sessions = {session["id"]: session for session in sessions_list}
            changes_found = False
            
            # Check for new sessions
            for session_id, session in current_sessions.items():
                if session_id not in self.session_cache:
                    self.log_change("NEW_SESSION",
                        f"Session {session_id} (Tags: {session.get('tags', [])}, "
                        f"Status: {session.get('status', 'unknown')})")
                    changes_found = True
            
            # Check for updated sessions
            for session_id, session in current_sessions.items():
                if session_id in self.session_cache:
                    old_session = self.session_cache[session_id]
                    if session.get("updatedAt", 0) > old_session.get("updatedAt", 0):
                        old_status = old_session.get("status", "unknown")
                        new_status = session.get("status", "unknown")
                        if old_status != new_status:
                            self.log_change("SESSION_STATUS_CHANGE",
                                f"Session {session_id}: {old_status} -> {new_status}")
                        else:
                            self.log_change("UPDATED_SESSION",
                                f"Session {session_id} (Tags: {session.get('tags', [])})")
                        changes_found = True
            
            # Check for removed sessions
            for session_id in self.session_cache:
                if session_id not in current_sessions:
                    self.log_change("REMOVED_SESSION", f"Session {session_id}")
                    changes_found = True
            
            # Update cache
            self.last_sessions_etag = current_etag
            self.session_cache = current_sessions
            
            return changes_found
            
        except Exception as e:
            print(f"Error checking sessions: {e}", file=sys.stderr)
            return False
    
    def check_context_activity(self) -> bool:
        """Check for new context activity in sessions"""
        changes_found = False
        
        try:
            # Get current sessions
            sessions_data, _ = read_json(SESSIONS_FILE)
            if not isinstance(sessions_data, dict) or "sessions" not in sessions_data:
                return False
            
            sessions_list = sessions_data["sessions"]
            
            for session in sessions_list:
                session_id = session.get("id")
                if not session_id:
                    continue
                
                context_path = context_file(session_id)
                if not context_path.exists():
                    continue
                
                last_known_ts = self.last_context_timestamps.get(session_id, 0)
                new_messages = []
                
                # Read context file and find new messages
                with context_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            ts = record.get("ts", 0)
                            if isinstance(ts, int) and ts > last_known_ts:
                                new_messages.append((ts, record))
                        except json.JSONDecodeError:
                            continue
                
                # Report new messages
                if new_messages:
                    # Sort by timestamp
                    new_messages.sort(key=lambda x: x[0])
                    
                    for ts, record in new_messages:
                        role = record.get("role", "unknown")
                        provider = record.get("provider", "unknown")
                        content = record.get("content", "")
                        
                        # Truncate long content
                        if len(str(content)) > 100:
                            content_str = str(content)[:100] + "..."
                        else:
                            content_str = str(content)
                        
                        self.log_change("NEW_CONTEXT",
                            f"Session {session_id}: {role} via {provider} - {content_str}")
                        changes_found = True
                    
                    # Update last timestamp
                    self.last_context_timestamps[session_id] = new_messages[-1][0]
            
        except Exception as e:
            print(f"Error checking context activity: {e}", file=sys.stderr)
        
        return changes_found
    
    def run_once(self) -> bool:
        """Run one monitoring cycle"""
        print(f"\n--- Monitoring cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        
        changes_found = False
        
        # Check agents
        if self.check_agents():
            changes_found = True
        
        # Check sessions
        if self.check_sessions():
            changes_found = True
        
        # Check context activity
        if self.check_context_activity():
            changes_found = True
        
        if not changes_found:
            print("No changes detected")
        
        return changes_found
    
    def run(self):
        """Run continuous monitoring"""
        print(f"Starting Zen MCP monitoring agent (polling every {self.poll_interval}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_once()
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except Exception as e:
            print(f"\nMonitoring error: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Zen MCP Monitoring Agent")
    parser.add_argument(
        "--interval", "-i", 
        type=int, 
        default=10,
        help="Polling interval in seconds (default: 10)"
    )
    parser.add_argument(
        "--once", 
        action="store_true",
        help="Run monitoring once and exit"
    )
    
    args = parser.parse_args()
    
    monitor = ZenMonitor(poll_interval=args.interval)
    
    if args.once:
        monitor.run_once()
    else:
        monitor.run()


if __name__ == "__main__":
    main()