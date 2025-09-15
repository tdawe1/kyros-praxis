#!/bin/bash

# Notion MCP Server Setup Script
# This script helps configure the Notion MCP server for codex-cli

echo "Setting up Notion MCP Server..."

# Check if NOTION_TOKEN is set
if [ -z "$NOTION_TOKEN" ]; then
    echo "Error: NOTION_TOKEN environment variable not set"
    echo "Please set your Notion integration token:"
    echo "  export NOTION_TOKEN='your_notion_integration_token_here'"
    exit 1
fi

# Set NOTION_VERSION if not already set
if [ -z "$NOTION_VERSION" ]; then
    NOTION_VERSION="2022-06-28"
fi

# Create the JSON headers for Notion API
export NOTION_MCP_OPENAPI_HEADERS_JSON="{\"Authorization\":\"Bearer ${NOTION_TOKEN}\",\"Notion-Version\":\"${NOTION_VERSION}\"}"

echo "Notion MCP configuration:"
echo "  Token: ${NOTION_TOKEN:0:10}..."
echo "  Version: $NOTION_VERSION"
echo "  Headers JSON: $NOTION_MCP_OPENAPI_HEADERS_JSON"

echo ""
echo "To enable Notion MCP server in codex, uncomment the notion section in your config files:"
echo "  - ~/.codex/config.toml"
echo "  - /home/thomas/kyros-praxis/kyros-praxis/codex-old-setup-revise.toml"
echo ""
echo "Then restart codex-cli to load the new MCP server configuration."