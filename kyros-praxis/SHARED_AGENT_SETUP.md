# Shared Agent Configuration

## Current Status
✅ **MCP Servers**: Running and accessible
✅ **Agent Cleanup**: Duplicate processes removed
🔄 **Shared Agent**: Being configured

## For All Users

### Connecting to the Shared Agent

Instead of starting individual agent instances, all users should connect to the shared agent:

```bash
# Check if shared agent is running
./scripts/agent-manager.sh status

# If not running, start it:
./scripts/agent-manager.sh start
```

### Configuration Updates

Update your individual configurations to use the shared MCP servers:

1. **VSCode/Claude Code**: Already configured to use MCP servers from `mcp.json`
2. **Terminal/Codex**: Use `codex --config "mcp_config=$PWD/mcp.json"`
3. **Other interfaces**: Point to the shared Redis instance on port 6379

### Agent Management Commands

```bash
# Start shared agent
./scripts/agent-manager.sh start

# Stop shared agent  
./scripts/agent-manager.sh stop

# Restart shared agent
./scripts/agent-manager.sh restart

# Check status
./scripts/agent-manager.sh status

# Clean up duplicates
./scripts/agent-manager.sh cleanup
```

## MCP Server Access

All users now have access to these shared MCP servers:

- **filesystem**: File operations across the workspace
- **memory**: Shared knowledge graph
- **redis**: Shared caching and state management (port 6379)
- **github**: Repository operations
- **notion**: Documentation access
- **exa**: Web search capabilities
- **puppeteer**: Browser automation
- **zen**: Code analysis and optimization
- **time**: Timestamp services
- **sequential-thinking**: Advanced reasoning

## Benefits

1. **Single Source of Truth**: All agents share the same context
2. **Resource Efficiency**: No duplicate processes
3. **Consistent State**: Shared memory and caching
4. **Easier Coordination**: Agents can see each other's work
5. **Centralized Logging**: All agent activity in one place

## Next Steps

1. ✅ Cleaned up duplicate agent processes
2. ✅ Created agent management scripts
3. 🔄 Set up shared agent instance
4. ⏳ Verify all users can connect
5. ⏳ Test multi-agent coordination