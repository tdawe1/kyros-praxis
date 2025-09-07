# Kyros Orchestrator API

The Kyros Orchestrator provides a versioned API for managing agent runs and system configuration.

## Features

- **Versioned API**: `/v1` prefix for all API endpoints
- **Health Checks**: `/healthz` and `/readyz` endpoints for monitoring
- **Configuration Management**: `/v1/config` endpoint for system settings
- **Agent Runs**: Support for plan (implement, critic coming soon)
- **Pydantic Settings**: Type-safe configuration management
- **OpenAPI Specification**: Full API documentation in `api-specs/orchestrator-v1.yaml`
## Quick Start

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or use the npm script
npm run dev:orchestrator
```

### Configuration

Configuration is loaded from YAML files in the `config/` directory:

- `config/base.yaml` - Base configuration
- `config/development.yaml` - Development overrides

Environment variables can override any configuration value.

### API Endpoints

#### Health Checks
- `GET /healthz` - Health check
- `GET /readyz` - Readiness check

#### Configuration
- `GET /v1/config` - Get current configuration
  
  ⚠️ **Security Warning**: This endpoint returns raw merged YAML configuration which may expose sensitive data including tokens, secrets, passwords, keys, and private_* entries. The server currently returns the full configuration without redaction. Consider implementing access control or sensitive key redaction before production deployment. See the handler implementation in `apps/adk-orchestrator/main.py:66` (`cfg()` function) for current behavior.

#### Agent Runs
- `POST /v1/runs/plan` - Start a planning run
- `POST /v1/runs/implement` - Start an implementation run
- `POST /v1/runs/critic` - Start a critique run

#### Agent Management
- `GET /v1/agents/status` - Get agent status

## Validation

The API specification is validated against the OpenAPI spec:

```bash
# Validate locally
npm run validate-api

# Or run the script directly
python scripts/validate-api.py
```

## Example Usage

### Start a Plan Run

```bash
curl -X POST "http://localhost:8000/v1/runs/plan" \
  -H "Content-Type: application/json" \
  -d '{
    "pr": {
      "repo": "owner/repo",
      "pr_number": 123,
      "branch": "feature/new-feature",
      "head_sha": "abc123def456"
    },
    "mode": "plan",
    "labels": ["needs:deep-refactor"],
    "extra": {"priority": "high"}
  }'
```

### Get Configuration

```bash
curl "http://localhost:8000/v1/config"
```

## Architecture

The orchestrator integrates with the Kyros Agent SDK to:

- Manage agent lifecycle
- Route tasks to appropriate agents
- Handle capability negotiation
- Provide sandboxed execution environments
- Maintain agent memory and state

## Development

### Adding New Endpoints

1. Add the endpoint to the API router in `main.py`
2. Update the OpenAPI specification in `api-specs/orchestrator-v1.yaml`
3. Add tests to the validation script
4. Run validation to ensure everything works

### Configuration Schema

The configuration uses Pydantic models for type safety:

- `ServicesConfig` - Service-level settings
- `AgentsConfig` - Agent configuration
- `LogConfig` - Logging settings

All configuration is validated at startup and can be overridden via environment variables.