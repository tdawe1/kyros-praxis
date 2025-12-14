#!/bin/bash
# Local Development Startup Script
# Starts the Kyros Praxis API backend

set -e

API_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$API_DIR/../.." && pwd )"
VENV_PATH="$PROJECT_ROOT/.venv"

echo "============================================"
echo "Kyros Praxis API - Local Startup"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
    echo "Please create it: python -m venv $VENV_PATH"
    exit 1
fi

# Check database
echo -n "Checking PostgreSQL... "
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    echo -e "${YELLOW}PostgreSQL not running on localhost:5432${NC}"
    echo "Start it with: sudo systemctl start postgresql"
    exit 1
fi

# Check environment file
if [ ! -f "$API_DIR/.env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Copy from .env.example and configure:"
    echo "  cp .env.example .env"
    exit 1
fi

# Apply migrations
echo -n "Applying database migrations... "
cd "$API_DIR"
if $VENV_PATH/bin/alembic upgrade head > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌ Migration failed${NC}"
    exit 1
fi

# Kill existing server
if lsof -ti:8001 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port 8001 already in use, killing existing process...${NC}"
    kill $(lsof -ti:8001) 2>/dev/null || true
    sleep 2
fi

echo ""
echo "============================================"
echo "Starting API Server"
echo "============================================"
echo ""
echo "  URL: http://localhost:8001"
echo "  Health: http://localhost:8001/health"
echo "  Docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start server
cd "$API_DIR"
exec $VENV_PATH/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --reload \
    --log-level info
