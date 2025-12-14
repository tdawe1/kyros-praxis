#!/bin/bash
# Startup script for Terminal Daemon service

cd services/terminal-daemon

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the service
echo "Starting Terminal Daemon on ws://localhost:8787"
echo "Press Ctrl+C to stop"
npm start