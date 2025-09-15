#!/bin/bash
# Corrected Setup Script for Kyros Praxis Development Environment

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
if [ ! -f "package.json" ]; then
    echo "Error: package.json not found. Please run from the project root."
    exit 1
fi

print_status "Setting up Kyros Praxis development environment..."

# 1. Check prerequisites
print_status "Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 20+"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    print_error "Node.js version 20+ is required. Current version: $(node --version)"
    exit 1
fi

print_success "Node.js $(node --version) is installed"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(echo $PYTHON_VERSION | cut -d'.' -f1)" -lt 3 ] || [ "$(echo $PYTHON_VERSION | cut -d'.' -f2)" -lt 11 ]; then
    print_error "Python 3.11+ is required. Current version: $(python3 --version)"
    exit 1
fi

print_success "Python $(python3 --version) is installed"

# Check Git
if command -v git &> /dev/null; then
    print_success "Git $(git --version) is installed"
else
    print_warning "Git is not installed"
fi

# 2. Install Node dependencies
print_status "Installing Node dependencies..."
npm ci --legacy-peer-deps
print_success "Node dependencies installed"

# 3. Install Python dependencies
print_status "Installing Python dependencies..."
if [ -f "services/orchestrator/requirements.txt" ]; then
    pip install -r services/orchestrator/requirements.txt
    print_success "Python dependencies installed"
else
    print_warning "services/orchestrator/requirements.txt not found"
fi

# 4. Install Terminal daemon dependencies
print_status "Installing Terminal daemon dependencies..."
if [ -d "services/terminal-daemon" ] && [ -f "services/terminal-daemon/package.json" ]; then
    cd services/terminal-daemon
    if [ ! -d "node_modules" ]; then
        npm install
        print_success "Terminal daemon dependencies installed"
    else
        print_success "Terminal daemon dependencies already installed"
    fi
    cd ../..
else
    print_warning "Terminal daemon directory not found"
fi

# 5. Create environment files
print_status "Setting up environment files..."

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32)

# Create orchestrator .env if it doesn't exist
if [ ! -f "services/orchestrator/.env" ]; then
    cat > services/orchestrator/.env << EOF
# JWT Configuration
JWT_SECRET=$JWT_SECRET
JWT_ISSUER=kyros-praxis
JWT_AUDIENCE=kyros-app

# Optional Basic Auth
# ORCH_AUTH_USER=admin
# ORCH_AUTH_PASS=password

# CORS Configuration
CORS_ALLOW_ORIGINS=http://localhost:3001,http://localhost:5000

# Database
DATABASE_URL=sqlite:///./orchestrator.db

# Environment
ENVIRONMENT=local
DEBUG=true
EOF
    print_success "Created services/orchestrator/.env"
fi

# Create terminal-daemon .env if it doesn't exist
if [ ! -f "services/terminal-daemon/.env" ]; then
    cat > services/terminal-daemon/.env << EOF
# JWT Secret (use same as orchestrator)
TERMINAL_JWT_SECRET=$JWT_SECRET

# Port Configuration
KYROS_DAEMON_PORT=8787
EOF
    print_success "Created services/terminal-daemon/.env"
fi

# 6. Create startup scripts
print_status "Creating startup scripts..."

# Create or update start-orchestrator.sh
cat > start-orchestrator.sh << 'EOF'
#!/bin/bash
cd services/orchestrator
PYTHONPATH=. uvicorn main:app --reload --port 8000
EOF
chmod +x start-orchestrator.sh

# Create or update start-console.sh
cat > start-console.sh << 'EOF'
#!/bin/bash
npm run dev
EOF
chmod +x start-console.sh

# Create or update start-daemon.sh
cat > start-daemon.sh << 'EOF'
#!/bin/bash
cd services/terminal-daemon
npm run dev
EOF
chmod +x start-daemon.sh

print_success "Startup scripts created"

# 7. Generate JWT token for development
print_status "Generating development JWT token..."
export JWT_SECRET=$JWT_SECRET
if npm run gen:jwt > dev.jwt 2>/dev/null; then
    print_success "Development JWT token generated in dev.jwt"
    print_warning "To use in browser: document.cookie = \"auth_token=$(cat dev.jwt); path=/\";"
else
    print_warning "Could not generate JWT token (gen:jwt script may not exist)"
fi

# 8. Create directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p .devlogs
print_success "Directories created"

# 9. Create quick workflow script
cat > quick-start.sh << 'EOF'
#!/bin/bash
# Quick start script for Kyros Praxis

echo "Starting Kyros Praxis development environment..."

# Start orchestrator in background
echo "Starting Orchestrator on port 8000..."
./start-orchestrator.sh > orchestrator.log 2>&1 &
ORCH_PID=$!
echo $ORCH_PID > .orchestrator.pid

# Start console in background
echo "Starting Console on port 5000..."
./start-console.sh > console.log 2>&1 &
CONSOLE_PID=$!
echo $CONSOLE_PID > .console.pid

# Start terminal daemon in background
echo "Starting Terminal Daemon on port 8787..."
./start-daemon.sh > daemon.log 2>&1 &
DAEMON_PID=$!
echo $DAEMON_PID > .daemon.pid

echo ""
echo "Services started in background:"
echo "  - Orchestrator: http://localhost:8000 (logs: tail -f orchestrator.log)"
echo "  - Console: http://localhost:5000 (logs: tail -f console.log)"
echo "  - Terminal Daemon: ws://localhost:8787 (logs: tail -f daemon.log)"
echo ""
echo "To stop services: ./stop-services.sh"

# Create stop script
cat > stop-services.sh << 'STOPEOF'
#!/bin/bash
echo "Stopping services..."

if [ -f .orchestrator.pid ]; then
    kill $(cat .orchestrator.pid) 2>/dev/null || true
    rm -f .orchestrator.pid
fi

if [ -f .console.pid ]; then
    kill $(cat .console.pid) 2>/dev/null || true
    rm -f .console.pid
fi

if [ -f .daemon.pid ]; then
    kill $(cat .daemon.pid) 2>/dev/null || true
    rm -f .daemon.pid
fi

# Kill any remaining processes
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

echo "Services stopped"
STOPEOF

chmod +x stop-services.sh
EOF

chmod +x quick-start.sh

print_success "Quick start script created: ./quick-start.sh"

# Done!
echo ""
echo "=========================================="
print_success "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review environment files:"
echo "   - services/orchestrator/.env"
echo "   - services/terminal-daemon/.env"
echo ""
echo "2. Start services:"
echo "   - Quick start: ./quick-start.sh"
echo "   - Individual: ./start-orchestrator.sh, ./start-console.sh, ./start-daemon.sh"
echo ""
echo "3. Access services:"
echo "   - Orchestrator API: http://localhost:8000"
echo "   - Console: http://localhost:5000"
echo "   - Terminal: ws://localhost:8787"
echo ""
echo "4. Run tests:"
echo "   - npm run test:python"
echo "   - npm run check"
echo ""
echo "5. For JWT auth in browser:"
echo "   document.cookie = \"auth_token=$(cat dev.jwt); path=/\";"
echo ""
echo "Happy coding! 🚀"