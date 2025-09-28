#!/usr/bin/env python3

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class AgentStatusDashboard:
    def __init__(self):
        self.status_file = Path("/tmp/kyros-agent-status.json")
        self.activity_file = Path("/tmp/kyros-agent-activity.jsonl")
    
    def update_agent_status(self, agent_id, status, details=None):
        """Update agent status"""
        status_data = {
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "agents": {}
        }
        
        # Load existing status
        if self.status_file.exists():
            try:
                existing = json.loads(self.status_file.read_text())
                status_data["agents"] = existing.get("agents", {})
            except:
                pass
        
        # Update this agent
        status_data["agents"][agent_id] = {
            "status": status,
            "details": details or {},
            "last_seen": datetime.utcnow().isoformat() + "Z"
        }
        
        # Write back
        self.status_file.write_text(json.dumps(status_data, indent=2))
    
    def get_agent_status(self):
        """Get current status of all agents"""
        if not self.status_file.exists():
            return {"agents": {}, "last_updated": datetime.utcnow().isoformat() + "Z"}
        
        try:
            return json.loads(self.status_file.read_text())
        except:
            return {"agents": {}, "last_updated": datetime.utcnow().isoformat() + "Z"}
    
    def get_activity_summary(self, minutes=30):
        """Get activity summary for last N minutes"""
        if not self.activity_file.exists():
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        activities = []
        
        try:
            lines = self.activity_file.read_text().strip().split("\n")
            for line in lines:
                if line.strip():
                    try:
                        activity = json.loads(line)
                        activity_time = datetime.fromisoformat(activity["timestamp"].replace("Z", "+00:00"))
                        if activity_time >= cutoff_time:
                            activities.append(activity)
                    except:
                        pass
        except:
            pass
        
        return activities
    
    def display_status(self):
        """Display current status in terminal"""
        status = self.get_agent_status()
        recent_activity = self.get_activity_summary(10)
        
        print("\n" + "="*60)
        print("🤖 KYROS AGENT STATUS DASHBOARD")
        print("="*60)
        print(f"📅 Last Updated: {status['last_updated']}")
        print(f"🔢 Active Agents: {len(status['agents'])}")
        print()
        
        # Agent statuses
        if status['agents']:
            print("📋 AGENT STATUS:")
            for agent_id, agent_info in status['agents'].items():
                status_icon = "🟢" if agent_info['status'] == 'active' else "🟡" if agent_info['status'] == 'busy' else "⚪"
                print(f"  {status_icon} {agent_id}: {agent_info['status']}")
                if agent_info.get('details'):
                    print(f"      📝 {agent_info['details']}")
                print(f"      ⏰ Last seen: {agent_info['last_seen']}")
                print()
        
        # Recent activity
        if recent_activity:
            print("📈 RECENT ACTIVITY (last 10 minutes):")
            for activity in recent_activity[-10:]:
                timestamp = activity['timestamp'][:19]  # Remove Z and microseconds
                icon = "🚀" if activity['action'] in ['started', 'completed'] else "⚙️" if activity['action'] in ['processing', 'working'] else "📝"
                print(f"  {timestamp} - {icon} {activity['agent_type']}: {activity['action']}")
                if activity.get('details'):
                    details_str = str(activity['details'])[:60] + "..." if len(str(activity['details'])) > 60 else str(activity['details'])
                    print(f"      💬 {details_str}")
            print()
        
        print("="*60)

if __name__ == "__main__":
    dashboard = AgentStatusDashboard()
    
    # Example: Update some status
    dashboard.update_agent_status("critic", "active", {"current_task": "Reviewing TDS-1"})
    dashboard.update_agent_status("implementer", "busy", {"files_modified": 5})
    dashboard.update_agent_status("architect", "idle")
    
    # Display dashboard
    dashboard.display_status()