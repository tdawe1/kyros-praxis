#!/bin/bash

# Simple Shared Agent Startup Script

echo "Starting shared Kyros agent..."
echo "All users will connect to this single instance"

# Start the agent in the background with proper output
codex --config "mcp_config=$PWD/mcp.json" > /tmp/kyros-shared-agent.log 2>&1 &
AGENT_PID=$!

echo $AGENT_PID > /tmp/kyros-shared-agent.pid
echo "Agent PID: $AGENT_PID"
echo "Log file: /tmp/kyros-shared-agent.log"

# Wait and check if it started
sleep 5
if ps -p $AGENT_PID > /dev/null 2>&1; then
    echo "✅ Shared agent started successfully"
    echo "All users should now connect to this shared instance"
else
    echo "❌ Failed to start shared agent"
    cat /tmp/kyros-shared-agent.log
    exit 1
fi