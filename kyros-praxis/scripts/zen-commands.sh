#!/bin/bash

# Simple Zen MCP Commands

echo "🧘‍♀️  ZEN MCP TOOLS"
echo "================="

# Test the Zen MCP integration directly
case "$1" in
    "register")
        echo "📝 Registering agent: ${2:-test-agent}"
        # Create a simple JSON-RPC call
        cat <<EOF | nc localhost 8080 2>/dev/null | jq .
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"zen/register_agent","arguments":{"name":"${2:-test-agent}","capabilities":["chat","analyze"]}}}
EOF
        ;;
        
    "list")
        echo "📋 Listing agents..."
        cat <<EOF | nc localhost 8080 2>/dev/null | jq .
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"zen/list_agents","arguments":{}}}
EOF
        ;;
        
    "create-session")
        echo "🔧 Creating session..."
        cat <<EOF | nc localhost 8080 2>/dev/null | jq .
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"zen/create_session","arguments":{"agentIds":[],"tags":["test"],"ttlMs":3600000}}}
EOF
        ;;
        
    "status")
        echo "🔍 Server status:"
        curl -s http://localhost:8080/health | jq .
        ;;
        
    *)
        echo "Usage: $0 {register|list|create-session|status} [args]"
        echo ""
        echo "Examples:"
        echo "  $0 register my-agent"
        echo "  $0 list"
        echo "  $0 create-session" 
        echo "  $0 status"
        ;;
esac