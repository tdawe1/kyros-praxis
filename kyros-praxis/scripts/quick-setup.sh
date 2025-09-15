#!/bin/bash
# Quick Setup Script for Kyros Praxis Development Environment
# This script handles the most common setup tasks quickly

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found. Please run from project root."
    exit 1
fi

print_status "Starting quick setup for Kyros Praxis development environment..."

# 1. Copy environment files if they don't exist
print_status "Setting up environment files..."
if [ ! -f "services/orchestrator/.env" ]; then
    cp services/orchestrator/.env.example services/orchestrator/.env
    print_status "Created services/orchestrator/.env"
fi

if [ ! -f "services/console/.env" ]; then
    cp services/console/.env.example services/console/.env
    print_status "Created services/console/.env"
fi

# Generate secrets if not already set
if grep -q "your_" services/orchestrator/.env; then
    print_status "Generating secure secrets..."
    JWT_SECRET=$(openssl rand -hex 32)
    SECRET_KEY=$(openssl rand -hex 32)

    sed -i "s/your_very_secure_jwt_secret.*/$JWT_SECRET/" services/orchestrator/.env
    sed -i "s/your_very_secure_app_secret.*/$SECRET_KEY/" services/orchestrator/.env
    print_success "Secrets generated"
fi

# 2. Create directories
print_status "Creating necessary directories..."
mkdir -p collaboration/state
mkdir -p collaboration/events
mkdir -p logs
print_success "Directories created"

# 3. Initialize tasks.json if it doesn't exist
if [ ! -f "collaboration/state/tasks.json" ]; then
    cat > collaboration/state/tasks.json << 'EOF'
{
  "tasks": [
    {
      "id": "TDS-1",
      "title": "Implement collab API steel thread",
      "status": "todo",
      "priority": "P0",
      "created_at": "2025-09-14T10:00:00Z"
    },
    {
      "id": "TDS-3",
      "title": "Implement Jobs vertical slice",
      "status": "todo",
      "priority": "P0",
      "created_at": "2025-09-14T10:00:00Z"
    }
  ]
}
EOF
    print_success "Initial tasks created"
fi

# 4. Initialize events file
touch collaboration/events/events.jsonl

# 5. Start Docker services if Docker is available
if command -v docker-compose &> /dev/null; then
    print_status "Starting Docker services..."
    docker-compose up -d postgres redis

    # Wait a moment for services to start
    sleep 5

    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        print_success "Docker services started"
    else
        print_warning "Docker services may not have started properly. Check with: docker-compose ps"
    fi
else
    print_warning "Docker Compose not found. Please start PostgreSQL and Redis manually."
fi

# 6. Install dependencies
print_status "Installing dependencies..."

# Python dependencies
if [ -f "services/orchestrator/requirements.txt" ]; then
    cd services/orchestrator
    if command -v pip &> /dev/null; then
        pip install -r requirements.txt
        print_success "Python dependencies installed"
    else
        print_warning "pip not found. Please install Python dependencies manually."
    fi
    cd ../..
fi

# Node.js dependencies
for service in console terminal-daemon; do
    if [ -d "services/$service" ] && [ -f "services/$service/package.json" ]; then
        cd services/$service
        if command -v npm &> /dev/null; then
            if [ ! -d "node_modules" ]; then
                print_status "Installing $service dependencies..."
                npm install
                print_success "$service dependencies installed"
            else
                print_success "$service dependencies already installed"
            fi
        else
            print_warning "npm not found. Please install $service dependencies manually."
        fi
        cd ../..
    fi
done

# 7. Copy MCP configuration
if [ ! -f "mcp.json" ] && [ -f "mcp.example.json" ]; then
    cp mcp.example.json mcp.json
    print_success "MCP configuration copied from template"
fi

# 8. Create startup scripts
print_status "Creating startup scripts..."

# Orchestrator startup script
cat > start-orchestrator.sh << 'EOF'
#!/bin/bash
cd services/orchestrator
PYTHONPATH=. uvicorn main:app --reload --port 8000
EOF
chmod +x start-orchestrator.sh

# Console startup script
cat > start-console.sh << 'EOF'
#!/bin/bash
cd services/console
npm run dev
EOF
chmod +x start-console.sh

# Terminal daemon startup script
cat > start-daemon.sh << 'EOF'
#!/bin/bash
cd services/terminal-daemon
npm start
EOF
chmod +x start-daemon.sh

print_success "Startup scripts created: start-orchestrator.sh, start-console.sh, start-daemon.sh"

# 9. Create development workflow script
cat > dev-workflow.sh << 'EOF'
#!/bin/bash
# Development workflow helper

case "$1" in
    "start")
        echo "Starting all services..."
        # Start in background
        ./start-orchestrator.sh > orchestrator.log 2>&1 &
        ./start-console.sh > console.log 2>&1 &
        ./start-daemon.sh > daemon.log 2>&1 &
        echo "Services started. Check logs in *.log files"
        ;;
    "stop")
        echo "Stopping services..."
        pkill -f "uvicorn main:app"
        pkill -f "npm run dev"
        pkill -f "npm start"
        echo "Services stopped"
        ;;
    "test")
        echo "Running tests..."
        cd services/orchestrator && python -m pytest
        cd ../services/console && npm test
        ;;
    "verify")
        echo "Running verification..."
        python scripts/verify-setup.py
        ;;
    *)
        echo "Usage: $0 {start|stop|test|verify}"
        exit 1
        ;;
esac
EOF
chmod +x dev-workflow.sh

print_success "Development workflow script created: dev-workflow.sh"

# Done!
echo ""
echo "=========================================="
print_success "Quick setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review environment files in services/*/.env"
echo "2. Start services:"
echo "   - Orchestrator: ./start-orchestrator.sh"
echo "   - Console: ./start-console.sh"
echo "   - Terminal Daemon: ./start-daemon.sh"
echo "   - Or use: ./dev-workflow.sh start"
echo ""
echo "3. Verify setup:"
echo "   python scripts/verify-setup.py"
echo ""
echo "4. Check service health:"
echo "   - Orchestrator: curl http://localhost:8000/healthz"
echo "   - Console: Open http://localhost:3001"
echo ""
echo "Happy coding! 🚀"