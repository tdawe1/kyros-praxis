#!/bin/bash

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Kyros Praxis - Local Production Test${NC}"
echo "================================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Use local env file
if [ -f .env.local ]; then
    cp .env.local .env
    echo -e "${GREEN}✅ Using local test environment${NC}"
else
    echo -e "${RED}❌ .env.local not found${NC}"
    exit 1
fi

# Stop any existing containers
echo -e "${YELLOW}Cleaning up existing containers...${NC}"
docker-compose -f docker-compose.local.yml down 2>/dev/null || true

# Start infrastructure services
echo -e "${BLUE}Starting PostgreSQL and Redis...${NC}"
docker-compose -f docker-compose.local.yml up -d

# Wait for services
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 5

# Check PostgreSQL
if docker-compose -f docker-compose.local.yml exec -T postgres pg_isready -U kyros_user &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
else
    echo -e "${YELLOW}⚠️  PostgreSQL may still be starting${NC}"
fi

# Check Redis
if docker-compose -f docker-compose.local.yml exec -T redis redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis is ready${NC}"
else
    echo -e "${YELLOW}⚠️  Redis may still be starting${NC}"
fi

# Install backend dependencies
echo -e "${BLUE}Setting up backend...${NC}"
cd services/orchestrator
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -q

# Run migrations
echo -e "${BLUE}Running database migrations...${NC}"
alembic upgrade head 2>/dev/null || echo -e "${YELLOW}⚠️  Migrations may need manual setup${NC}"

# Start backend
echo -e "${BLUE}Starting backend API...${NC}"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd ../..

# Install frontend dependencies
echo -e "${BLUE}Setting up frontend...${NC}"
cd services/console
npm install --silent

# Build frontend
echo -e "${BLUE}Building frontend...${NC}"
npm run build

# Start frontend
echo -e "${BLUE}Starting frontend...${NC}"
nohup npm start > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ../..

# Wait for services to start
echo -e "${BLUE}Waiting for services to start...${NC}"
sleep 10

# Check services
echo -e "${BLUE}Checking service health...${NC}"

# Check backend
if curl -f -s http://localhost:8000/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API is running${NC}"
else
    echo -e "${YELLOW}⚠️  Backend API may still be starting${NC}"
fi

# Check frontend
if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend may still be starting${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Local production test environment is running!${NC}"
echo ""
echo "Access URLs:"
echo "  Frontend:     http://localhost:3000"
echo "  Backend API:  http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo ""
echo "Database:"
echo "  PostgreSQL:   localhost:5432 (kyros_user/localpass123)"
echo "  Redis:        localhost:6379"
echo ""
echo "Process PIDs:"
echo "  Backend:      $BACKEND_PID"
echo "  Frontend:     $FRONTEND_PID"
echo ""
echo "To stop all services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  docker-compose -f docker-compose.local.yml down"
echo ""
echo "Logs:"
echo "  Backend:      services/orchestrator/backend.log"
echo "  Frontend:     services/console/frontend.log"
echo ""

# Save PIDs to file for easy cleanup
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

echo -e "${GREEN}✅ Local test environment ready!${NC}"
echo -e "${YELLOW}Note: MSW mocks are active for API calls${NC}"