FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install the official Zen MCP server from GitHub
RUN pip install -U pip \
 && pip install git+https://github.com/BeehiveInnovations/zen-mcp-server.git

# Default command launches the MCP server (stdio JSON-RPC)
ENTRYPOINT ["zen-mcp-server"]

