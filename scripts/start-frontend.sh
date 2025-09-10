#!/bin/bash

# Script to start the Kyros Console frontend development server
# Usage: ./scripts/start-frontend.sh
# Assumes the script is run from the project root (/home/thomas/kyros-praxis)

set -e  # Exit on any error for idempotency

FRONTEND_DIR="kyros-praxis/services/console"

echo "Starting Kyros Console frontend setup..."

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "Error: Directory $FRONTEND_DIR not found. Ensure the repo is cloned correctly."
  exit 1
fi

cd "$FRONTEND_DIR"

echo "Installing dependencies..."
npm install

echo "Starting development server on http://localhost:3000..."
npm run dev

# The script will keep running the dev server; use Ctrl+C to stop