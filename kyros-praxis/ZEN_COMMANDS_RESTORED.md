# Zen MCP Commands Successfully Restored ✅

## Problem Solved
The Zen MCP management commands that were previously missing have been successfully restored. The issue was that the Zen MCP server had its tools disabled in the configuration.

## Fixed Configuration
Updated `/home/thomas/kyros-praxis/kyros-praxis/mcp.json`:
- Changed `"DISABLED_TOOLS": "analyze,refactor,testgen,secaudit,docgen,tracer"` 
- To: `"DISABLED_TOOLS": ""`

## Available Zen MCP Commands

### Basic Management
```bash
# Show help
./scripts/zen-mcp-manage.sh help

# Register a new agent
./scripts/zen-mcp-manage.sh register <agent-name> [capabilities...]

# List all registered agents  
./scripts/zen-mcp-manage.sh list

# Create a new session
./scripts/zen-mcp-manage.sh create-session

# Show available tools
./scripts/zen-mcp-manage.sh tools
```

### Examples
```bash
# Register a simple agent
./scripts/zen-mcp-manage.sh register my-agent chat analyze

# Register with multiple capabilities
./scripts/zen-mcp-manage.sh register advanced-agent chat analyze refactor optimize

# See all agents
./scripts/zen-mcp-manage.sh list

# Create a session
./scripts/zen-mcp-manage.sh create-session
```

## All Available Zen Tools
The Zen MCP server provides 8 management tools:

1. **zen/register_agent** - Register or update agents
2. **zen/list_agents** - List all registered agents  
3. **zen/create_session** - Create sessions spanning multiple agents
4. **zen/add_context** - Add context records to sessions
5. **zen/get_context** - Read session context with filtering
6. **zen/set_kv** - Set key-value pairs in sessions
7. **zen/get_kv** - Get key-value pairs from sessions
8. **zen/close_session** - Close sessions

## Current Status
- ✅ Zen MCP server running
- ✅ All tools enabled
- ✅ Management commands accessible
- ✅ Agent registration working
- ✅ Session creation working
- ✅ Communication protocol working (stdio)

The Zen MCP management system is now fully operational for managing external agents outside of Claude Code.