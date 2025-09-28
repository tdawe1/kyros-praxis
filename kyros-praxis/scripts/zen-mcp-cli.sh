#!/bin/bash

# Enhanced Zen MCP Management Interface

echo "🧘‍♀️  ZEN MCP MANAGEMENT INTERFACE"
echo "================================="

# Function to call Zen MCP tools
call_zen_tool() {
    local tool="$1"
    local args="$2"
    
    echo "📡 Calling zen tool: $tool"
    if [ ! -z "$args" ]; then
        echo "📋 Args: $args"
    fi
    
    # Create JSON-RPC call
    local request=$(cat <<EOF
{
  "jsonrpc": "2.0",
  "id": $(date +%s),
  "method": "tools/call",
  "params": {
    "name": "$tool",
    "arguments": $args
  }
}
EOF
)
    
    # Send to zen MCP server
    printf "%s" "$request" | tr -d '\n' | python integrations/zen-mcp/main.py | jq . 2>/dev/null || echo "⚠️  Error calling Zen MCP tool"
}

# Function to show usage
show_help() {
    echo ""
    echo "📖 Available Commands:"
    echo ""
    echo "  register     - Register a new agent"
    echo "  list         - List all registered agents"
    echo "  session      - Create a new session"
    echo "  context      - Add context to session"
    echo "  getctx       - Get session context"
    echo "  setkv        - Set key-value in session"
    echo "  getkv        - Get key-value from session"
    echo "  close        - Close a session"
    echo "  tools        - Show available tools"
    echo "  help         - Show this help"
    echo ""
    echo "🔧 Usage: $0 <command> [args...]"
    echo ""
}

# Main command handling
case "${1:-help}" in
    register)
        if [ -z "$2" ]; then
            echo "❌ Usage: $0 register <agent-name> [capabilities...]"
            exit 1
        fi
        name="$2"
        shift 2
        caps="$*"
        
        if [ -z "$caps" ]; then
            caps='["chat", "analyze"]'
        else
            # Convert space-separated to JSON array
            caps=$(echo "$caps" | sed 's/[^ ]*/\"&\"/g' | sed 's/ /, /g' | sed 's/^/[/; s/$/]/')
        fi
        
        call_zen_tool "zen/register_agent" "{\"name\": \"$name\", \"capabilities\": $caps}"
        ;;
        
    list)
        call_zen_tool "zen/list_agents" "{}"
        ;;
        
    session)
        agents="$2"
        tags="$3"
        ttl="$4"
        
        if [ -z "$agents" ]; then
            agents='[]'
        else
            # Convert comma-separated to JSON array
            agents=$(echo "$agents" | sed 's/[^,]*/\"&\"/g' | sed 's/, /, /g' | sed 's/^/[/; s/$/]/')
        fi
        
        if [ -z "$tags" ]; then
            tags='["test"]'
        else
            # Convert space-separated to JSON array
            tags=$(echo "$tags" | sed 's/[^ ]*/\"&\"/g' | sed 's/ /, /g' | sed 's/^/[/; s/$/]/')
        fi
        
        args="{\"agentIds\": $agents, \"tags\": $tags"
        if [ ! -z "$ttl" ]; then
            args="$args, \"ttlMs\": $ttl"
        fi
        args="$args}"
        
        call_zen_tool "zen/create_session" "$args"
        ;;
        
    context)
        if [ -z "$3" ]; then
            echo "❌ Usage: $0 context <session-id> <role> <content> [provider]"
            exit 1
        fi
        session_id="$2"
        role="$3"
        shift 3
        content="$*"
        # Provider optional; omit to avoid argument parsing ambiguity
        esc_content=$(printf '%s' "$content" | sed 's/"/\\"/g')
        args="{\"sessionId\": \"$session_id\", \"role\": \"$role\", \"content\": \"$esc_content\"}"
        
        call_zen_tool "zen/add_context" "$args"
        ;;
        
    getctx)
        if [ -z "$2" ]; then
            echo "❌ Usage: $0 getctx <session-id> [limit] [since-timestamp]"
            exit 1
        fi
        args="{\"sessionId\": \"$2\""
        if [ ! -z "$3" ]; then args="$args, \"limit\": $3"; fi
        if [ ! -z "$4" ]; then args="$args, \"sinceTs\": $4"; fi
        args="$args}"

        call_zen_tool "zen/get_context" "$args"
        ;;
        
    setkv)
        if [ -z "$4" ]; then
            echo "❌ Usage: $0 setkv <session-id> <key> <value>"
            exit 1
        fi
        
        call_zen_tool "zen/set_kv" "{\"sessionId\": \"$2\", \"key\": \"$3\", \"value\": \"$4\"}"
        ;;
        
    getkv)
        if [ -z "$3" ]; then
            echo "❌ Usage: $0 getkv <session-id> <key>"
            exit 1
        fi
        
        call_zen_tool "zen/get_kv" "{\"sessionId\": \"$2\", \"key\": \"$3\"}"
        ;;
        
    close)
        if [ -z "$2" ]; then
            echo "❌ Usage: $0 close <session-id>"
            exit 1
        fi
        
        call_zen_tool "zen/close_session" "{\"sessionId\": \"$2\"}"
        ;;
        
    tools)
        call_zen_tool "tools/list" ""
        ;;
        
    help|--help|-h)
        show_help
        ;;
        
    *)
        echo "❌ Unknown command: $1"
        show_help
        exit 1
        ;;
esac
