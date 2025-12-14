#!/bin/bash
# Startup script for Console service

cd services/console

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the service
PORT=${PORT:-3001}
export NEXTAUTH_URL=${NEXTAUTH_URL:-http://localhost:$PORT}
export NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000/api/v1}
export NEXT_PUBLIC_WS_URL=${NEXT_PUBLIC_WS_URL:-ws://localhost:8000/ws}

echo "Starting Console on http://localhost:$PORT"
echo "Press Ctrl+C to stop"
npm run dev -- -p "$PORT"
