# Orchestrator Event Logging

This document explains how to use the structured logging system for orchestrator events in the Kyros Praxis system.

## Overview

The orchestrator event logging system provides:

1. Structured, newline-delimited JSON logging for all orchestrator events
2. Server-Sent Events (SSE) streaming endpoints for real-time event monitoring
3. Rotating file handlers for log management
4. Task and run ID filtering for targeted event tracking

## Logging Format

All orchestrator events are logged in newline-delimited JSON format with the following structure:

```json
{
  "timestamp": "2023-06-15T10:30:45.123456",
  "level": "INFO",
  "logger": "orchestrator_events",
  "event": "task_started",
  "task_id": "task-123",
  "run_id": "run-456",
  "message": "Task started successfully",
  "status": "running"
}
```

## Using the Logging System

### 1. Logging Events

To log an orchestrator event, use the `log_orchestrator_event` function:

```python
from services.orchestrator.app.core.logging import log_orchestrator_event

# Log a simple event
log_orchestrator_event(
    event="task_started",
    task_id="task-123",
    status="running"
)

# Log an event with additional fields
log_orchestrator_event(
    event="job_completed",
    task_id="job-456",
    run_id="run-789",
    duration_ms=1500,
    result="success",
    message="Job completed successfully"
)
```

### 2. Streaming Events via SSE

The system provides SSE endpoints to stream events in real-time:

#### Get Events (REST API)
```
GET /api/v1/orchestrator/events?task_id=task-123
```

#### Stream Events (SSE)
```
GET /api/v1/orchestrator/events/stream?task_id=task-123
```

### 3. Filtering Events

Events can be filtered by `task_id` or `run_id`:

```python
# Stream events for a specific task
async for event in stream_orchestrator_events(task_id="task-123"):
    print(event)

# Get all events for a specific run
events = await get_orchestrator_events(run_id="run-456")
```

## Configuration

The logging system is configured through environment variables:

- `ORCH_ID`: Orchestrator ID (default: "o-glm")
- `ORCH_LOG_FILE`: Path to the orchestrator log file (default: ".devlogs/orch-{ORCH_ID}.log")
- `LOG_LEVEL`: Logging level (default: "INFO")
- `LOG_FILE`: General application log file (optional)

## Log Rotation

Log files are automatically rotated when they reach 10MB, with up to 5 backup files retained.

## Example Usage

Here's a complete example of how to use the orchestrator event logging in a job processing workflow:

```python
from services.orchestrator.app.core.logging import log_orchestrator_event

def process_job(job_id):
    # Log job start
    log_orchestrator_event(
        event="job_started",
        task_id=job_id,
        status="running"
    )
    
    try:
        # Process the job
        result = do_work(job_id)
        
        # Log job completion
        log_orchestrator_event(
            event="job_completed",
            task_id=job_id,
            status="success",
            result=result,
            duration_ms=calculate_duration()
        )
        
        return result
    except Exception as e:
        # Log job failure
        log_orchestrator_event(
            event="job_failed",
            task_id=job_id,
            status="failed",
            error=str(e)
        )
        
        raise
```

## Testing

To test the orchestrator event logging system, run:

```bash
python test_orchestrator_logging.py
```

This will verify that:
1. Events are properly logged in JSON format
2. Log files are created and rotated correctly
3. SSE streaming functionality works as expected