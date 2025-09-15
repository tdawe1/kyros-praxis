#!/bin/bash

# Quick status check for CLI users

echo "🔍 Checking Kyros agent status..."
echo ""

# Check agent processes
echo "📊 Agent Processes:"
ps aux | grep -E "(codex|mcp)" | grep -v grep | head -5 | while read line; do
    echo "  $line"
done
echo ""

# Check Redis connectivity
echo "🔗 Redis Status:"
if redis-cli ping > /dev/null 2>&1; then
    echo "  ✅ Connected (port 6379)"
    # Show connected clients
    echo "  👥 Clients: $(redis-cli info clients | grep connected_clients | cut -d: -f2)"
else
    echo "  ❌ Not connected"
fi
echo ""

# Check recent activity
echo "📈 Recent Activity:"
if [ -f "/tmp/kyros-agent-activity.jsonl" ]; then
    tail -5 /tmp/kyros-agent-activity.jsonl | while read line; do
        if [ ! -z "$line" ]; then
            echo "  $line" | jq -r '"\(.timestamp[:19]) - \(.agent_type): \(.action)"' 2>/dev/null || echo "  $line"
        fi
    done
else
    echo "  No activity log found"
fi
echo ""

# Show running MCP servers
echo "🧩 MCP Servers:"
ps aux | grep "mcp-server" | grep -v grep | wc -l | xargs echo "  Total servers running:"
echo ""

# Quick commands reminder
echo "🛠️  Useful Commands:"
echo "  ./scripts/agent-dashboard.py     # Full dashboard"
echo "  ./scripts/agent-monitor.sh       # Live updates"
echo "  tail -f /tmp/kyros-agent-activity.jsonl  # Activity stream"
echo "  redis-cli publish agent:status 'update'  # Manual status update"