# Zen MCP Server — Local Dev Setup

This project can use the official Zen MCP Server for multi‑agent orchestration and cross‑provider context.

## Docker (project‑preferred)

- Set keys in `.env` at repo root (copy from `.env.integrations.example`): `OPENAI_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY` (at least one).
- From your MCP client, configure the `zen` server to spawn via the repo helper:

```
{
  "mcpServers": {
    "zen": {
      "command": "bash",
      "args": ["kyros-praxis/scripts/mcp-run.sh", "mcp_zen"]
    }
  }
}
```

The wrapper attaches stdio to `docker compose run --rm -T mcp_zen`, which executes the official Zen MCP inside a container via `uvx`.

## Prerequisites
- Python 3.10+ (3.11+ recommended)
- Git
- `uv` / `uvx` (installed via `pip install uv` or system package manager)
- At least one API key: OpenAI, Gemini, or OpenRouter
- Windows: WSL2 recommended (PowerShell or Ubuntu shell)

## Option A — Clone + Script (recommended)

```
git clone https://github.com/BeehiveInnovations/zen-mcp-server.git
cd zen-mcp-server
```

Linux & macOS:
```
./run-server.sh
```
Windows (WSL/PowerShell):
```
./run-server.ps1
```

Create or edit `.env` in the repo root:
```
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
OPENROUTER_API_KEY=your-openrouter-key
```
At least one key is required.

Start the server:
```
./run-server.sh
```
The script also re‑configures on updates (`git pull`).

## Option B — UVX one‑liner

```
exec $(which uvx || echo uvx) --from git+https://github.com/BeehiveInnovations/zen-mcp-server.git zen-mcp-server
```

## Configure your MCP client
Add this to your client config (Claude Desktop / Claude Code, etc.):

```
{
  "mcpServers": {
    "zen": {
      "command": "sh",
      "args": [
        "-c",
        "exec $(which uvx || echo uvx) --from git+https://github.com/BeehiveInnovations/zen-mcp-server.git zen-mcp-server"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_key_here",
        "GEMINI_API_KEY": "your_gemini_key_here"
      }
    }
  }
}
```

Typical locations:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

## Project integration
This repo’s example config already points Zen MCP to the uvx command:
- `mcp-servers.local.json.example` → `zen` entry
- Environment keys in `.env.integrations.example`: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`

## Troubleshooting
- Restart your MCP client after changing config.
- Update Zen MCP: `git pull` then re‑run `./run-server.sh`.
- For local models (e.g., Ollama), see the upstream repo’s advanced config.
