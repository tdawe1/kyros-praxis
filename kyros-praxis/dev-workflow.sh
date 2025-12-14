#!/bin/bash
# Development workflow helper script for Kyros Praxis

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[WORKFLOW]${NC} $1"
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

# Function to check if a service is running
is_service_running() {
    local port=$1
    local service_name=$2
    if curl -s "http://localhost:${port}/healthz" > /dev/null 2>&1 || \
       curl -s "http://localhost:${port}/" > /dev/null 2>&1 || \
       ss -tlnp | grep -q ":${port}"; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local port=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    print_status "Waiting for ${service_name} to start..."

    while [ $attempt -le $max_attempts ]; do
        if is_service_running $port "$service_name"; then
            print_success "${service_name} is running!"
            return 0
        fi

        echo "Attempt ${attempt}/${max_attempts}..."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_error "${service_name} failed to start within expected time"
    return 1
}

# Function to show service status
show_status() {
    echo ""
    echo "=== Service Status ==="

    # Check Docker services
    if command -v docker-compose &> /dev/null; then
        echo -e "\nDocker Services:"
        docker-compose ps 2>/dev/null | grep -E "(postgres|redis)" | while read line; do
            echo "  $line"
        done
    fi

    # Check application services
    echo -e "\nApplication Services:"

    if is_service_running 8000 "Orchestrator"; then
        echo -e "  ${GREEN}✓${NC} Orchestrator (port 8000)"
    else
        echo -e "  ${RED}✗${NC} Orchestrator (port 8000)"
    fi

    if is_service_running 3001 "Console"; then
        echo -e "  ${GREEN}✓${NC} Console (port 3001)"
    else
        echo -e "  ${RED}✗${NC} Console (port 3001)"
    fi

    if ss -tlnp | grep -q ":8787"; then
        echo -e "  ${GREEN}✓${NC} Terminal Daemon (port 8787)"
    else
        echo -e "  ${RED}✗${NC} Terminal Daemon (port 8787)"
    fi

    echo ""
}

# Main command handler
case "${1:-help}" in
    "setup")
        print_status "Running quick setup..."
        ./scripts/quick-setup.sh
        print_success "Setup complete!"
        ;;

    "start")
        print_status "Starting all services..."

        # Start Docker services if available
        if command -v docker-compose &> /dev/null; then
            print_status "Starting Docker services..."
            docker-compose up -d postgres redis 2>/dev/null || print_warning "Docker services failed to start"
        fi

        # Start application services in background
        print_status "Starting Orchestrator..."
        ./start-orchestrator.sh > orchestrator.log 2>&1 &
        ORCH_PID=$!

        print_status "Starting Console..."
        ./start-console.sh > console.log 2>&1 &
        CONSOLE_PID=$!

        print_status "Starting Terminal Daemon..."
        ./start-daemon.sh > daemon.log 2>&1 &
        DAEMON_PID=$!

        # Save PIDs for later
        echo $ORCH_PID > .orchestrator.pid
        echo $CONSOLE_PID > .console.pid
        echo $DAEMON_PID > .daemon.pid

        # Wait for services
        wait_for_service 8000 "Orchestrator"
        wait_for_service 3001 "Console"

        # Show status
        show_status

        print_success "All services started!"
        echo ""
        echo "Service logs:"
        echo "  - Orchestrator: tail -f orchestrator.log"
        echo "  - Console: tail -f console.log"
        echo "  - Terminal Daemon: tail -f daemon.log"
        echo ""
        echo "To stop services: ./dev-workflow.sh stop"
        ;;

    "stop")
        print_status "Stopping all services..."

        # Stop application services
        if [ -f .orchestrator.pid ]; then
            ORCH_PID=$(cat .orchestrator.pid)
            if ps -p $ORCH_PID > /dev/null; then
                kill $ORCH_PID 2>/dev/null || true
                print_success "Orchestrator stopped"
            fi
            rm -f .orchestrator.pid
        fi

        if [ -f .console.pid ]; then
            CONSOLE_PID=$(cat .console.pid)
            if ps -p $CONSOLE_PID > /dev/null; then
                kill $CONSOLE_PID 2>/dev/null || true
                print_success "Console stopped"
            fi
            rm -f .console.pid
        fi

        if [ -f .daemon.pid ]; then
            DAEMON_PID=$(cat .daemon.pid)
            if ps -p $DAEMON_PID > /dev/null; then
                kill $DAEMON_PID 2>/dev/null || true
                print_success "Terminal Daemon stopped"
            fi
            rm -f .daemon.pid
        fi

        # Kill any remaining processes
        pkill -f "uvicorn main:app" 2>/dev/null || true
        pkill -f "npm run dev" 2>/dev/null || true
        pkill -f "npm start" 2>/dev/null || true

        # Stop Docker services
        if command -v docker-compose &> /dev/null; then
            print_status "Stopping Docker services..."
            docker-compose stop 2>/dev/null || print_warning "Failed to stop Docker services"
        fi

        print_success "All services stopped"
        ;;

    "restart")
        print_status "Restarting all services..."
        ./dev-workflow.sh stop
        sleep 2
        ./dev-workflow.sh start
        ;;

    "status")
        show_status
        ;;

    "logs")
        case "${2:-all}" in
            "orchestrator")
                tail -f orchestrator.log
                ;;
            "console")
                tail -f console.log
                ;;
            "daemon")
                tail -f daemon.log
                ;;
            "all")
                echo "Showing logs for all services (Ctrl+C to exit)..."
                tail -f orchestrator.log console.log daemon.log
                ;;
            *)
                echo "Usage: $0 logs {orchestrator|console|daemon|all}"
                exit 1
                ;;
        esac
        ;;

    "test")
        print_status "Running tests..."

        # Backend tests
        if [ -d "services/orchestrator" ]; then
            print_status "Running backend tests..."
            cd services/orchestrator
            if [ -f "requirements.txt" ]; then
                python -m pytest -v 2>/dev/null || print_warning "Some backend tests failed"
            else
                print_warning "No requirements.txt found"
            fi
            cd ../..
        fi

        # Frontend tests
        if [ -d "services/console" ]; then
            print_status "Running frontend tests..."
            cd services/console
            if [ -f "package.json" ]; then
                npm test 2>/dev/null || print_warning "Some frontend tests failed"
            else
                print_warning "No package.json found"
            fi
            cd ../..
        fi

        print_success "Tests complete"
        ;;

    "verify")
        print_status "Running environment verification..."
        if [ -f "scripts/verify-setup.py" ]; then
            python scripts/verify-setup.py
        else
            print_error "Verification script not found"
        fi
        ;;

    "update-task")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 update-task <task_id> <status> [--user <username>]"
            exit 1
        fi

        TASK_ID=$2
        STATUS=$3
        USER=${4:-developer}

        if [ -f "scripts/state_update.py" ]; then
            print_status "Updating task $TASK_ID to status: $STATUS"
            python scripts/state_update.py "$TASK_ID" "$STATUS" --user "$USER"
            print_success "Task updated"
        else
            print_error "State update script not found"
        fi
        ;;

    "list-tasks")
        if [ -f "scripts/state_update.py" ]; then
            python scripts/state_update.py --list
        else
            print_error "State update script not found"
        fi
        ;;

    "clean")
        print_warning "This will clean up temporary files and logs. Continue? [y/N]"
        read -r response
        if [[ $response =~ ^[Yy]$ ]]; then
            print_status "Cleaning up..."

            # Remove log files
            rm -f orchestrator.log console.log daemon.log
            rm -f *.pid

            # Clean node modules (optional)
            if [ "$2" = "--deep" ]; then
                print_status "Deep clean - removing node_modules..."
                find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
                find . -name "package-lock.json" -delete 2>/dev/null || true

                # Clean Python cache
                find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
                find . -name "*.pyc" -delete 2>/dev/null || true
            fi

            print_success "Cleanup complete"
        else
            print_status "Cleanup cancelled"
        fi
        ;;

    "help"|"-h"|"--help")
        echo "Kyros Praxis Development Workflow Helper"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  setup           - Run quick setup for new development environment"
        echo "  start           - Start all services (Docker, Orchestrator, Console, Daemon)"
        echo "  stop            - Stop all running services"
        echo "  restart         - Restart all services"
        echo "  status          - Show status of all services"
        echo "  logs [service]  - Show logs (orchestrator|console|daemon|all)"
        echo "  test            - Run all tests"
        echo "  verify          - Run environment verification"
        echo "  update-task     - Update task status (usage: update-task <id> <status>)"
        echo "  list-tasks      - List all tasks"
        echo "  clean [--deep]  - Clean up temporary files"
        echo "  help            - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 start                 # Start all services"
        echo "  $0 logs orchestrator     # Show orchestrator logs"
        echo "  $0 update-task TDS-1 in_progress  # Update task status"
        echo "  $0 clean --deep          # Deep clean all caches"
        ;;

    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' to see available commands"
        exit 1
        ;;
esac