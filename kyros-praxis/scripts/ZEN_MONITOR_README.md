# Zen MCP Monitoring Agent

A Python script that continuously monitors the Zen MCP system for changes and reports new activity.

## Features

- **Agent Monitoring**: Detects new agent registrations, capability updates, and agent removals
- **Session Monitoring**: Tracks new session creation, status changes, and session closures
- **Context Activity**: Monitors new messages and context additions to sessions
- **Change Detection**: Uses ETags and timestamps to only report actual changes
- **Concise Output**: Formats changes in readable, timestamped messages

## Usage

### Basic Monitoring (10-second intervals)
```bash
python scripts/zen-monitor-agent.py
```

### Custom Interval
```bash
python scripts/zen-monitor-agent.py --interval 5
```

### Single Check
```bash
python scripts/zen-monitor-agent.py --once
```

### Help
```bash
python scripts/zen-monitor-agent.py --help
```

## Output Format

The monitoring agent outputs changes in this format:

```
[2025-09-12 22:57:33] NEW_AGENT: claude-code-agent (ID: 55ea6d1d-143c-47e3-8431-b4e1bbfe9439) Capabilities: ['chat', 'analyze', 'review', 'implement', 'plan']
[2025-09-12 22:57:33] NEW_SESSION: Session 8cadbd4d-eb45-49d2-9049-549a837e67a3 (Tags: ['monitoring'], Status: open)
[2025-09-12 22:57:33] NEW_CONTEXT: Session 8cadbd4d-eb45-49d2-9049-549a837e67a3: user via monitor-agent - Test message from monitor agent
[2025-09-12 22:57:33] SESSION_STATUS_CHANGE: Session abc123: open -> closed
```

## Change Types

- **NEW_AGENT**: A new agent was registered
- **UPDATED_AGENT**: An existing agent's capabilities or metadata were updated
- **REMOVED_AGENT**: An agent was removed from the system
- **NEW_SESSION**: A new session was created
- **UPDATED_SESSION**: A session's metadata was updated
- **REMOVED_SESSION**: A session was removed
- **SESSION_STATUS_CHANGE**: A session's status changed (e.g., open -> closed)
- **NEW_CONTEXT**: New context was added to a session

## How It Works

1. **ETag Tracking**: Uses SHA256 hashes to detect changes in agents and sessions
2. **Timestamp Tracking**: Monitors context files for new entries based on timestamps
3. **Efficient Polling**: Only reads files when necessary and caches state between runs
4. **Error Handling**: Gracefully handles file access errors and continues monitoring

## Requirements

- Python 3.7+
- Access to Zen MCP state files in the `zen/` directory
- The `zen-mcp` integration module

## Integration

The monitor uses the existing Zen MCP integration at `integrations/zen-mcp/main.py` to read state files and utilities.

## Stopping

Press `Ctrl+C` to stop the continuous monitoring.