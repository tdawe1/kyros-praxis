#!/usr/bin/env python3
"""
Enhanced Zen MCP Task Monitor - Specifically for detecting handoff tasks
"""
import json
import subprocess
import time
import sys
from pathlib import Path

def call_zen_tool(tool, args):
    """Call a Zen MCP tool and return the result"""
    cmd = [
        'python', 'integrations/zen-mcp/main.py'
    ]
    
    request = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {
            "name": tool,
            "arguments": args
        }
    }
    
    try:
        result = subprocess.run(
            cmd,
            input=json.dumps(request) + '\n',
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Error calling {tool}: {result.stderr}")
            return None
    except Exception as e:
        print(f"Exception calling {tool}: {e}")
        return None

def check_handoff_sessions():
    """Check for handoff sessions that need attention"""
    # Get all sessions
    sessions_result = call_zen_tool("zen/list_agents", {})
    if not sessions_result:
        return
    
    # Get sessions data directly from the sessions file
    sessions_file = Path(__file__).parent.parent / "zen" / "state" / "sessions.json"
    if not sessions_file.exists():
        return
    
    try:
        with open(sessions_file, 'r') as f:
            sessions_data = json.load(f)
    except:
        return
    
    sessions = sessions_data.get('sessions', [])
    handoff_sessions = [s for s in sessions if 'handoff' in s.get('tags', [])]
    
    new_tasks = []
    for session in handoff_sessions:
        session_id = session['id']
        
        # Check if this session has content
        context_result = call_zen_tool("zen/get_context", {"sessionId": session_id})
        if not context_result or not context_result.get('result', {}).get('ok'):
            continue
            
        items = context_result['result']['items']
        
        # Look for handoff tasks that haven't been responded to
        user_messages = [item for item in items if item.get('role') == 'user' and item.get('provider') == 'codex-cli']
        assistant_responses = [item for item in items if item.get('role') == 'assistant' and item.get('provider') == 'claude-code-agent']
        
        # If there are user messages but no assistant responses, it's a new task
        if user_messages and not assistant_responses:
            task_content = user_messages[0]['content']
            print("\n🎯 NEW HANDOFF TASK DETECTED!")
            print(f"Session ID: {session_id}")
            print(f"Content:\n{task_content}")
            print("-" * 50)
            new_tasks.append((session_id, task_content))
    
    return new_tasks

def main():
    print("🎯 Zen Task Monitor - Starting up...")
    
    # Check once immediately
    tasks = check_handoff_sessions()
    if tasks:
        print(f"\n🚨 Found {len(tasks)} new handoff tasks!")
        for session_id, task in tasks:
            print(f"Task in session {session_id}: {task[:100]}...")
    else:
        print("\n✅ No new handoff tasks found")
    
    # If --once flag, exit after first check
    if '--once' in sys.argv:
        return
    
    # Otherwise monitor continuously
    interval = 10  # seconds
    if '--interval' in sys.argv:
        idx = sys.argv.index('--interval')
        if idx + 1 < len(sys.argv):
            interval = int(sys.argv[idx + 1])
    
    print(f"\n🔄 Monitoring every {interval} seconds... Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(interval)
            tasks = check_handoff_sessions()
            if tasks:
                print(f"\n🚨 Found {len(tasks)} new handoff tasks!")
                for session_id, task in tasks:
                    print(f"Task in session {session_id}: {task[:100]}...")
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitor...")

if __name__ == "__main__":
    main()