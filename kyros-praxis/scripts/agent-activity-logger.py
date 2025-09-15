#!/usr/bin/env python3

import json
import time
from datetime import datetime
from pathlib import Path

class AgentActivityLogger:
    def __init__(self):
        self.log_file = Path("/tmp/kyros-agent-activity.jsonl")
        self.log_file.parent.mkdir(exist_ok=True)
    
    def log_activity(self, agent_type, action, details=None):
        """Log agent activity for all users to see"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_type": agent_type,
            "action": action,
            "details": details or {},
            "session_id": self._get_session_id()
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Also publish to Redis if available
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.publish("agent:activity", json.dumps(entry))
        except:
            pass
    
    def _get_session_id(self):
        """Get or create session ID"""
        session_file = Path("/tmp/kyros-session-id")
        if session_file.exists():
            return session_file.read_text().strip()
        else:
            import uuid
            session_id = str(uuid.uuid4())[:8]
            session_file.write_text(session_id)
            return session_id
    
    def get_recent_activity(self, limit=50):
        """Get recent activity for status reporting"""
        if not self.log_file.exists():
            return []
        
        lines = self.log_file.read_text().strip().split("\n")
        if lines[0] == "":
            return []
        
        activities = []
        for line in lines[-limit:]:
            if line.strip():
                try:
                    activities.append(json.loads(line))
                except:
                    pass
        
        return activities

# Global instance for agents to use
activity_logger = AgentActivityLogger()

if __name__ == "__main__":
    # Example usage and testing
    logger = AgentActivityLogger()
    
    # Log some sample activities
    logger.log_activity("critic", "started", {"task": "TDS-1 review"})
    logger.log_activity("implementer", "completed", {"files": 3, "lines": 150})
    logger.log_activity("architect", "planning", {"complexity": "high"})
    
    # Show recent activity
    print("Recent Agent Activity:")
    for activity in logger.get_recent_activity(10):
        print(f"{activity['timestamp']} - {activity['agent_type']}: {activity['action']}")
        if activity['details']:
            print(f"  Details: {activity['details']}")