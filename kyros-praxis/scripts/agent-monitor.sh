#!/bin/bash

# Agent Status Monitor - Subscribe to Redis channels for real-time updates

REDIS_HOST="localhost"
REDIS_PORT="6379"

echo "🔗 Connecting to Redis for real-time agent updates..."
echo "📡 Listening for agent activity..."

# Subscribe to agent activity channels
redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --csv subscribe \
    "agent:activity" \
    "agent:status" \
    "agent:tasks" \
    "agent:errors" \
    "agent:coordination"