#!/bin/bash

# Single Agent Manager for Kyros Praxis
# Ensures only one agent instance runs for all users

AGENT_PID_FILE="/tmp/kyros-agent.pid"
MCP_CONFIG="$PWD/mcp.json"
LOG_FILE="/tmp/kyros-agent.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if agent is already running
check_running() {
    if [ -f "$AGENT_PID_FILE" ]; then
        PID=$(cat "$AGENT_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log "Agent is already running with PID $PID"
            return 0
        else
            warn "Stale PID file found, removing..."
            rm -f "$AGENT_PID_FILE"
        fi
    fi
    return 1
}

# Start the single agent instance
start_agent() {
    if check_running; then
        log "Agent is already running"
        return 0
    fi

    log "Starting single Kyros agent instance..."
    
    # Start codex with MCP configuration
    nohup codex --config "mcp_config=$MCP_CONFIG" > "$LOG_FILE" 2>&1 &
    AGENT_PID=$!
    
    echo "$AGENT_PID" > "$AGENT_PID_FILE"
    
    # Wait a moment and verify it started
    sleep 3
    if ps -p "$AGENT_PID" > /dev/null 2>&1; then
        log "Agent started successfully with PID $AGENT_PID"
        log "All users should connect to this agent instance"
        log "Log file: $LOG_FILE"
        return 0
    else
        error "Failed to start agent"
        rm -f "$AGENT_PID_FILE"
        return 1
    fi
}

# Stop the agent
stop_agent() {
    if [ -f "$AGENT_PID_FILE" ]; then
        PID=$(cat "$AGENT_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log "Stopping agent (PID $PID)..."
            kill "$PID"
            sleep 2
            
            if ps -p "$PID" > /dev/null 2>&1; then
                warn "Agent didn't stop gracefully, force killing..."
                kill -9 "$PID"
            fi
            
            rm -f "$AGENT_PID_FILE"
            log "Agent stopped"
        else
            warn "Agent was not running"
            rm -f "$AGENT_PID_FILE"
        fi
    else
        warn "No PID file found, agent may not be running"
    fi
}

# Show agent status
status() {
    if check_running; then
        PID=$(cat "$AGENT_PID_FILE")
        log "Agent status: RUNNING (PID $PID)"
        echo "Log file: $LOG_FILE"
        echo "MCP Config: $MCP_CONFIG"
        
        # Show connected users/processes
        echo ""
        echo "Connected processes:"
        ps aux | grep -E "(codex|mcp)" | grep -v grep | head -10
    else
        error "Agent is NOT running"
        return 1
    fi
}

# Clean up duplicate processes
cleanup_duplicates() {
    log "Cleaning up duplicate agent processes..."
    
    # Find all codex processes except the one in PID file
    if [ -f "$AGENT_PID_FILE" ]; then
        MAIN_PID=$(cat "$AGENT_PID_FILE")
        ps aux | grep codex | grep -v grep | grep -v "$MAIN_PID" | awk '{print $2}' | while read pid; do
            if [ ! -z "$pid" ]; then
                warn "Killing duplicate codex process: $pid"
                kill -9 "$pid" 2>/dev/null
            fi
        done
    else
        # No main PID, kill all codex processes
        ps aux | grep codex | grep -v grep | awk '{print $2}' | while read pid; do
            if [ ! -z "$pid" ]; then
                warn "Killing orphaned codex process: $pid"
                kill -9 "$pid" 2>/dev/null
            fi
        done
    fi
    
    # Clean up duplicate zen-mcp processes too
    ps aux | grep zen-mcp-server | grep -v grep | awk '{print $2}' | while read pid; do
        if [ ! -z "$pid" ]; then
            warn "Killing duplicate zen-mcp process: $pid"
            kill -9 "$pid" 2>/dev/null
        fi
    done
}

# Main command handling
case "${1:-start}" in
    start)
        cleanup_duplicates
        start_agent
        ;;
    stop)
        stop_agent
        ;;
    restart)
        stop_agent
        sleep 2
        start_agent
        ;;
    status)
        status
        ;;
    cleanup)
        cleanup_duplicates
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|cleanup}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the single agent instance"
        echo "  stop     - Stop the agent"
        echo "  restart - Restart the agent"
        echo "  status   - Show agent status"
        echo "  cleanup  - Clean up duplicate processes"
        exit 1
        ;;
esac