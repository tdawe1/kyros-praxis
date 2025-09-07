# Kyros Orchestrator

The Kyros Orchestrator is a FastAPI-based service that manages agent runs and provides system configuration.

## Features

- **Versioned API**: RESTful API with `/v1` prefix
- **Health Endpoints**: `/healthz` and `/readyz` for health checks
- **Configuration Management**: `/v1/config` endpoint with pydantic-settings
- **Run Management**: `/v1/runs/plan` endpoint for starting planning runs
- **OpenAPI Specification**: Full API documentation at `/docs`

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. Test the API:
   ```bash
   python test_orchestrator.py
   ```

## API Endpoints

### Health Checks
- `GET /healthz` - Health status
- `GET /readyz` - Readiness status

### Configuration
- `GET /v1/config` - Get current configuration

### Runs
- `POST /v1/runs/plan` - Start a planning run

## Configuration

Configuration is loaded from YAML files in the `config/` directory:
- `base.yaml` - Base configuration
- `development.yaml` - Development overrides

Environment variables can also be used to override configuration values.

## Development

Run the development server:
```bash
npm run dev:orchestrator
```

Validate API specification:
```bash
npm run validate:api
```

## Testing

Run the test suite:
```bash
npm run test:orchestrator
```
