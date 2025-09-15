# ORCH_ID Logging Configuration for SSE Integration

## Overview

The orchestrator now supports ORCH_ID-based logging configuration that integrates with the SSE (Server-Sent Events) system. This allows multiple orchestrator instances to write to separate log files based on their ORCH_ID.

## Configuration

### Environment Variables

- **ORCH_ID**: Orchestrator identifier (default: "o-glm")
  - Supported values: o-glm, o-qwen, o-grok
  - Used to generate log file name: `.devlogs/orch-{ORCH_ID}.log`

- **ORCH_LOG_FILE**: Optional override for log file path
  - If not set, defaults to `.devlogs/orch-{ORCH_ID}.log`

- **LOG_LEVEL**: Logging level (default: "INFO")
  - Values: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Settings Configuration

The configuration is also available in `app/core/config.py`:

```python
# Logging
LOG_LEVEL: str = "INFO"
LOG_FILE: Optional[str] = None

# Orchestrator ID for log file naming
ORCH_ID: str = "o-glm"
```

## Implementation Details

### Files Modified

1. **main.py**: Added logging initialization with ORCH_ID support
2. **app/core/config.py**: Added ORCH_ID configuration setting
3. **app/core/logging.py**: Already supported file-based logging

### Log Format

Logs are written in newline-delimited JSON format:

```json
{"event":"task_executed","task_id":"abc123","status":"success","timestamp":"2025-01-14T10:00:00Z"}
```

### SSE Integration

The SSE endpoints read from the following log files:
- `.devlogs/orch-o-glm.log`
- `.devlogs/orch-o-qwen.log`
- `.devlogs/orch-o-grok.log`

## Usage

### Starting with Different ORCH_ID Values

```bash
# Default (o-glm)
ORCH_ID=o-glm python -m uvicorn main:app --reload

# For Qwen orchestrator
ORCH_ID=o-qwen python -m uvicorn main:app --reload

# For Grok orchestrator
ORCH_ID=o-grok python -m uvicorn main:app --reload
```

### Custom Log File

```bash
# Override log file location
ORCH_LOG_FILE=/custom/path/orchestrator.log python -m uvicorn main:app --reload
```

### Log Level

```bash
# Set debug logging
LOG_LEVEL=DEBUG python -m uvicorn main:app --reload
```

## Log File Management

- Log files are automatically created in `.devlogs/` directory
- Files rotate at 10MB with 5 backup files
- JSON format ensures structured logging for SSE consumption
- Directory is created automatically if it doesn't exist

## Integration Notes

- The SSE endpoints at `/api/sse/super/events` monitor the three standard ORCH_ID log files
- Events are filtered by `task_id` or `run_id` when using `/api/sse/super/run?run=<id>`
- The system is designed to work with the existing SSE infrastructure

This configuration ensures that orchestrator instances write to the correct log files for SSE streaming and monitoring.