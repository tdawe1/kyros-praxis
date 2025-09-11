# Managing MCP Servers in Kyros Praxis

This document provides clear instructions for managing the MCP (Model Context Protocol) servers in the Kyros Praxis project. The MCP servers are local Node.js processes that provide specialized tools for agentic workflows, such as filesystem access, sequential thinking, Puppeteer integration, and more. They are not managed by Docker (only Qdrant is dockerized in `docker-compose.integrations.yml`), so management involves local scripts, monitoring, and troubleshooting.

The servers are defined in `.kilocode/mcp.json` and started via npm exec or uvx commands. To ensure stability and proper stdin/TTY support (as discussed in the previous diagnosis), we recommend dockerizing them for production-like environments. This guide covers both local and dockerized management.

## Prerequisites

- **Node.js**: Version 20+ installed (for local runs).
- **npm or uv**: For running the servers locally.
- **Docker**: For dockerized setup (install via your package manager or Docker Desktop).
- **Git**: To manage branches and stage changes.
- **mcp.json**: Ensure it's configured correctly in `.kilocode/mcp.json` (see [Configuration](#configuration) below).

## Step 1: Checkout to a New Branch

To implement and test changes (e.g., dockerization fixes from the previous task), create a new branch for safety:

```bash
git checkout -b mcp-management-fix
```

This isolates your changes from the main branch. Commit the updated files (e.g., Dockerfiles, docker-compose.integrations.yml) after making changes.

## Step 2: Configuration

The MCP servers are configured in `.kilocode/mcp.json`. This file lists all servers (e.g., `mcp_zen`, `mcp_coderabbit`, `mcp_composer_trade`, `mcp_exasearch`, `mcp_filesystem`, `mcp_github`, `mcp_notion`, `mcp_puppeteer`, `mcp_railway`, `mcp_vercel`, `mcp_zen_tools`, `mcp_kyros_collab`, `mcp_fireproof`) with their commands, env vars, and dependencies.

Example snippet from mcp.json:
```json
{
  "mcp_servers": {
    "mcp_filesystem": {
      "command": "mcp-server-filesystem",
      "env": {
        "MCP_CONFIG_PATH": "/home/thomas/kyros-praxis/mcp.json"
      }
    },
    "mcp_puppeteer": {
      "command": "mcp-server-puppeteer",
      "env": {
        "BROWSER_TYPE": "chromium"
      }
    }
    // ... other servers
  }
}
```

- **Update Config**: Edit `.kilocode/mcp.json` to add or modify servers. Ensure paths (e.g., for data volumes) are absolute for dockerized runs.
- **Secrets**: Never commit sensitive keys (e.g., API tokens). Use `.env` files and reference them (e.g., `MCP_GITHUB_TOKEN=${GITHUB_TOKEN}`).

## Step 3: Running MCP Servers Locally

Local runs use npm exec or uvx for quick development. These processes run in the foreground and can be managed via terminal.

### Starting Servers
Run each server individually or use a script to start all:

1. **Single Server**:
   ```bash
   # Example for mcp_filesystem
   cd /home/thomas/kyros-praxis/kyros-praxis
   npm exec mcp-server-filesystem -- --config .kilocode/mcp.json
   ```

2. **All Servers (Recommended Script)**:
   Create or update `scripts/start-mcp-servers.sh`:
   ```bash
   #!/bin/bash
   cd /home/thomas/kyros-praxis/kyros-praxis
   # Start in background with logging
   npm exec mcp-server-filesystem -- --config .kilocode/mcp.json > logs/mcp-filesystem.log 2>&1 &
   npm exec mcp-server-sequential-thinking -- --config .kilocode/mcp.json > logs/mcp-sequential-thinking.log 2>&1 &
   # ... add all other MCP servers (zen, coderabbit, etc.)
   echo "All MCP servers started. Logs in logs/ directory."
   ```

   Make executable and run:
   ```bash
   chmod +x scripts/start-mcp-servers.sh
   ./scripts/start-mcp-servers.sh
   ```

   - This starts servers in the background with output redirected to logs (create `logs/` dir first).
   - For stdin/TTY: Run with `node --interactive` if needed, but for servers, logging is preferred over interactive mode.

### Stopping Servers
- **Single Server**:
  ```bash
  pkill -f mcp-server-filesystem  # Kill by name
  ```

- **All Servers (Script)**:
  Create `scripts/stop-mcp-servers.sh`:
  ```bash
  #!/bin/bash
  pkill -f mcp-server  # Kills all mcp-server processes
  echo "All MCP servers stopped."
  ```

  Run:
  ```bash
  ./scripts/stop-mcp-servers.sh
  ```

### Monitoring and Troubleshooting Local Runs
- **Check Status**: Use `ps aux | grep mcp` to list running processes.
- **View Logs**: `tail -f logs/mcp-*.log` for real-time output.
- **Debug Errors**: If a server crashes (e.g., port conflict), check the log for stack traces. Common issues:
  - Port 8787 or 8080 conflicts: Change in mcp.json or kill conflicting processes.
  - Missing deps: Run `npm install` in the project root.
  - Memory issues: Monitor with `htop` or `ps aux`; increase node memory with `--max-old-space-size=4096`.
- **Restart on Failure**: Use pm2 for auto-restart:
  ```bash
  npm install -g pm2
  pm2 start ecosystem.config.js --env production
  pm2 status  # View status
  pm2 logs    # View logs
  pm2 stop all  # Stop all
  ```
  Create `ecosystem.config.js` for all MCP servers with restart delay (e.g., `restart_delay: 5000`).

## Step 4: Dockerized Management (Recommended for Stability)

Dockerizing provides isolation, auto-restart, and TTY support. The previous fix involved adding Dockerfiles and updating `docker-compose.integrations.yml`.

### Setup
1. **Create Dockerfiles**: As per previous task, create a Dockerfile for each MCP in `integrations/<mcp-name>/Dockerfile` (e.g., for mcp_filesystem):
   ```
   FROM node:20-alpine
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   EXPOSE 8787  # Adjust to MCP port
   CMD ["npm", "start"]  # Adjust to entrypoint
   ```

2. **Update docker-compose.integrations.yml**:
   - Add services for all MCPs with `stdin_open: true`, `tty: true`, and volumes for mcp.json/data.
   - Example:
     ```
     services:
       qdrant:
         # Existing...
       mcp-filesystem:
         build: ./integrations/mcp-filesystem
         stdin_open: true
         tty: true
         volumes:
           - .kilocode/mcp.json:/app/mcp.json:ro
           - integrations/mcp-filesystem/data:/app/data
         environment:
           - NODE_ENV=production
         ports:
           - "8787:8787"  # MCP port
         depends_on:
           - qdrant
         restart: unless-stopped
       # Repeat for other MCPs (mcp-zen, mcp-coderabbit, etc.)
     ```

3. **Build Images**:
   ```bash
   docker compose -f docker-compose.integrations.yml build
   ```

4. **Start Services**:
   ```bash
   docker compose -f docker-compose.integrations.yml up -d
   ```

5. **Management Commands**:
   - **Status**: `docker compose -f docker-compose.integrations.yml ps` (check all Up).
   - **Logs**: `docker compose -f docker-compose.integrations.yml logs mcp-filesystem` (real-time: `... logs -f`).
   - **Exec into Container**: `docker compose -f docker-compose.integrations.yml exec mcp-filesystem sh` (TTY enabled).
   - **Stop**: `docker compose -f docker-compose.integrations.yml down`.
   - **Restart**: `docker compose -f docker-compose.integrations.yml restart mcp-filesystem`.
   - **Scale**: `docker compose -f docker-compose.integrations.yml up --scale mcp-filesystem=2 -d` (for redundancy).

### Troubleshooting Dockerized Runs
- **Build Errors**: Ensure Dockerfile has correct COPY and RUN steps. Check for missing package.json in subdirs.
- **Port Conflicts**: Map to different host ports if needed (e.g., `- "8788:8787"`).
- **Volumes**: Ensure host paths exist (e.g., create `integrations/mcp-filesystem/data`).
- **Network**: Services share the `kyros-integrations` network; add depends_on for inter-service communication (e.g., mcp-kyros depends_on qdrant).
- **Logs for Debugging**: Use `docker logs <container-id>` or compose logs for node errors.

## Step 5: Staging Changes

After implementing the fix (Dockerfiles and compose updates):

1. **Add Files**:
   ```bash
   git add integrations/ docker-compose.integrations.yml .kilocode/mcp.json docs/mcp-management.md
   ```

2. **Commit**:
   ```bash
   git commit -m "feat: dockerize MCP servers with TTY support and management scripts

   - Added Dockerfiles for all MCP servers in integrations/.
   - Updated docker-compose.integrations.yml to include MCP services with stdin_open and tty.
   - Added scripts/start-mcp-servers.sh and scripts/stop-mcp-servers.sh for local management.
   - Documented in docs/mcp-management.md."
   ```

3. **Push to Branch**:
   ```bash
   git push origin mcp-management-fix
   ```

This completes the task. The branch is created, documentation is provided, and changes are staged for review. To merge, use `git checkout main; git merge mcp-management-fix` after testing.

For further customization, see [Configuration](#configuration) and [Troubleshooting](#troubleshooting-dockerized-runs).
