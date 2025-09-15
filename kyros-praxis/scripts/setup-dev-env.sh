#!/bin/bash
# Automated Development Environment Setup Script for Kyros Praxis
# Based on the development environment setup plan

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            echo "debian"
        elif [ -f /etc/redhat-release ]; then
            echo "redhat"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to install Docker
install_docker() {
    print_status "Installing Docker..."
    OS=$(detect_os)

    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y docker.io docker-compose
            ;;
        "redhat")
            sudo yum install -y docker docker-compose
            ;;
        "macos")
            print_warning "Please install Docker Desktop for Mac from https://www.docker.com/products/docker-desktop"
            return 1
            ;;
        "windows")
            print_warning "Please install Docker Desktop for Windows from https://www.docker.com/products/docker-desktop"
            return 1
            ;;
        *)
            print_error "Unsupported OS for automatic Docker installation"
            return 1
            ;;
    esac

    # Add user to docker group
    sudo usermod -aG docker $USER
    print_success "Docker installed successfully"
    print_warning "You may need to log out and log back in for group changes to take effect"
}

# Function to install Python
install_python() {
    print_status "Installing Python 3.11+..."
    OS=$(detect_os)

    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y python3.11 python3.11-venv python3-pip
            ;;
        "redhat")
            sudo yum install -y python3.11 python3.11-pip
            ;;
        "macos")
            if command_exists brew; then
                brew install python@3.11
            else
                print_error "Homebrew not found. Please install Homebrew first"
                return 1
            fi
            ;;
        *)
            print_error "Unsupported OS for automatic Python installation"
            return 1
            ;;
    esac

    print_success "Python 3.11+ installed successfully"
}

# Function to install Node.js
install_nodejs() {
    print_status "Installing Node.js 18+..."

    # Use NodeSource repository for Debian/Ubuntu
    if [[ "$(detect_os)" == "debian" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt install -y nodejs
    elif [[ "$(detect_os)" == "macos" ]]; then
        if command_exists brew; then
            brew install node@18
        else
            print_error "Homebrew not found. Please install Homebrew first"
            return 1
        fi
    else
        print_error "Unsupported OS for automatic Node.js installation"
        return 1
    fi

    print_success "Node.js 18+ installed successfully"
}

# Function to verify installations
verify_installations() {
    print_status "Verifying installations..."

    # Check Docker
    if command_exists docker; then
        DOCKER_VERSION=$(docker --version)
        print_success "Docker: $DOCKER_VERSION"
    else
        print_error "Docker not found"
    fi

    # Check Docker Compose
    if command_exists docker-compose; then
        COMPOSE_VERSION=$(docker-compose --version)
        print_success "Docker Compose: $COMPOSE_VERSION"
    else
        print_error "Docker Compose not found"
    fi

    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python: $PYTHON_VERSION"
    else
        print_error "Python 3 not found"
    fi

    # Check Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js: $NODE_VERSION"
    else
        print_error "Node.js not found"
    fi

    # Check npm
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        print_success "npm: $NPM_VERSION"
    else
        print_error "npm not found"
    fi

    # Check Git
    if command_exists git; then
        GIT_VERSION=$(git --version)
        print_success "Git: $GIT_VERSION"
    else
        print_error "Git not found"
    fi
}

# Function to setup environment files
setup_environment_files() {
    print_status "Setting up environment configuration files..."

    # Copy example environment files if they don't exist
    if [ ! -f "services/orchestrator/.env" ]; then
        cp services/orchestrator/.env.example services/orchestrator/.env
        print_status "Created services/orchestrator/.env"
    fi

    if [ ! -f "services/console/.env" ]; then
        cp services/console/.env.example services/console/.env
        print_status "Created services/console/.env"
    fi

    if [ ! -f "services/terminal-daemon/.env" ]; then
        cp services/terminal-daemon/.env.example services/terminal-daemon/.env
        print_status "Created services/terminal-daemon/.env"
    fi

    # Generate secure secrets
    print_status "Generating secure secrets..."
    JWT_SECRET=$(openssl rand -hex 32)
    NEXTAUTH_SECRET=$(openssl rand -hex 32)
    CSRF_SECRET=$(openssl rand -hex 32)

    # Update environment files with generated secrets
    sed -i "s/^JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" services/orchestrator/.env
    sed -i "s/^NEXTAUTH_SECRET=.*/NEXTAUTH_SECRET=$NEXTAUTH_SECRET/" services/console/.env
    sed -i "s/^CSRF_SECRET=.*/CSRF_SECRET=$CSRF_SECRET/" services/console/.env

    print_success "Environment files configured with secure secrets"
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."

    # Install uv
    if ! command_exists uv; then
        pip install uv
    fi

    # Install Python requirements
    if [ -f "services/orchestrator/requirements.txt" ]; then
        cd services/orchestrator
        pip install -r requirements.txt
        cd ../..
    fi

    print_success "Python dependencies installed"
}

# Function to install Node dependencies
install_node_deps() {
    print_status "Installing Node.js dependencies..."

    # Install npx globally
    npm install -g npx

    # Install Node dependencies for each service
    if [ -d "services/console" ]; then
        cd services/console
        npm install
        cd ../..
    fi

    if [ -d "services/terminal-daemon" ]; then
        cd services/terminal-daemon
        npm install
        cd ../..
    fi

    print_success "Node.js dependencies installed"
}

# Function to setup initial state
setup_initial_state() {
    print_status "Setting up initial state..."

    # Create collaboration directories
    mkdir -p collaboration/state
    mkdir -p collaboration/events

    # Create initial tasks.json if it doesn't exist
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
        print_status "Created collaboration/state/tasks.json"
    fi

    # Initialize events.jsonl if it doesn't exist
    if [ ! -f "collaboration/events/events.jsonl" ]; then
        touch collaboration/events/events.jsonl
        print_status "Created collaboration/events/events.jsonl"
    fi

    print_success "Initial state setup complete"
}

# Function to start infrastructure
start_infrastructure() {
    print_status "Starting core infrastructure..."

    # Start PostgreSQL and Redis
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d postgres redis

        # Wait for services to be healthy
        print_status "Waiting for services to be healthy..."
        sleep 10

        # Check service status
        docker-compose ps

        print_success "Infrastructure started successfully"
    else
        print_error "docker-compose.yml not found"
    fi
}

# Function to run setup verification
run_verification() {
    print_status "Running setup verification..."

    # Test PR gate script
    if [ -f "scripts/pr_gate_minimal.py" ]; then
        print_status "Testing PR gate script..."
        python scripts/pr_gate_minimal.py --show-help
    fi

    # Test state management
    if [ -f "scripts/state_update.py" ]; then
        print_status "Testing state management..."
        python scripts/state_update.py --list
    fi

    # Test MCP servers
    print_status "Testing MCP servers..."

    # Test filesystem MCP
    if command_exists npx; then
        print_status "Testing filesystem MCP..."
        npx -y @modelcontextprotocol/server-filesystem . --help || true
    fi

    # Test time MCP
    if command_exists uvx; then
        print_status "Testing time MCP..."
        uvx mcp-server-time --help || true
    fi

    print_success "Setup verification complete"
}

# Main setup function
main() {
    echo "=========================================="
    echo "Kyros Praxis Development Environment Setup"
    echo "=========================================="
    echo ""

    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found. Please run this script from the project root."
        exit 1
    fi

    # Ask what to install
    echo "What would you like to install?"
    echo "1) All prerequisites (Docker, Python, Node.js, Git)"
    echo "2) Skip prerequisites, only configure environment"
    echo "3) Custom selection"

    read -p "Enter your choice (1-3): " choice

    case $choice in
        1)
            print_status "Installing all prerequisites..."

            # Install Docker if not present
            if ! command_exists docker; then
                install_docker
            fi

            # Install Python if not present
            if ! command_exists python3 || ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
                install_python
            fi

            # Install Node.js if not present
            if ! command_exists node || ! node -e "process.exit(process.version.split('.')[0] >= 18 ? 0 : 1)"; then
                install_nodejs
            fi

            # Install Git if not present
            if ! command_exists git; then
                if [[ "$(detect_os)" == "debian" ]]; then
                    sudo apt install -y git
                else
                    print_error "Please install Git manually"
                fi
            fi
            ;;
        2)
            print_status "Skipping prerequisite installation..."
            ;;
        3)
            print_status "Custom selection..."
            # Add custom selection logic here
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    # Verify installations
    verify_installations
    echo ""

    # Setup environment files
    setup_environment_files
    echo ""

    # Install dependencies
    install_python_deps
    install_node_deps
    echo ""

    # Setup initial state
    setup_initial_state
    echo ""

    # Start infrastructure
    start_infrastructure
    echo ""

    # Run verification
    run_verification
    echo ""

    print_success "Development environment setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Review and update environment files in services/*/.env"
    echo "2. Start the development services:"
    echo "   - Orchestrator: cd services/orchestrator && uvicorn main:app --reload"
    echo "   - Console: cd services/console && npm run dev"
    echo "   - Terminal Daemon: cd services/terminal-daemon && npm start"
    echo "3. Run tests to verify everything works:"
    echo "   - Backend: cd services/orchestrator && python -m pytest"
    echo "   - Frontend: cd services/console && npm test"
    echo ""
    echo "Happy coding! 🚀"
}

# Run main function
main "$@"