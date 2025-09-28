"""
Comprehensive Logging Configuration for Kyros Praxis Orchestrator

This module provides comprehensive logging configuration for the Kyros Praxis Orchestrator service.
It implements structured JSON logging, request context logging, orchestrator event logging, and
Server-Sent Events (SSE) streaming capabilities for real-time monitoring.

The logging system includes:
- Structured JSON formatters for consistent log formatting
- Multiple log handlers (console, file) with rotation
- Request context logging with tracing identifiers
- Specialized orchestrator event logging for SSE consumption
- In-memory event storage for real-time streaming
- Environment-specific configuration

KEY FEATURES:
1. Structured Logging: JSON-formatted logs with consistent fields
2. Request Context: Per-request logging with tracing identifiers
3. Orchestrator Events: Specialized logging for task and run events
4. SSE Streaming: Real-time event streaming via Server-Sent Events
5. File Rotation: Automatic log file rotation to manage disk space
6. Environment Awareness: Different formatting for local vs production

The module automatically configures logging on import based on application settings.
"""

import json
import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from collections import defaultdict
import asyncio
import uuid

try:
    from .config import settings
except ImportError:
    # Fallback for environments where config is not available
    from pydantic_settings import BaseSettings
    class FallbackSettings(BaseSettings):
        ENVIRONMENT: str = "local"
        PROJECT_NAME: str = "kyros-praxis"
    settings = FallbackSettings()


# Global event store for SSE streaming
# Maps task_id/run_id to list of events for real-time streaming
_orchestrator_events = defaultdict(list)  # task_id/run_id -> list of events
_orchestrator_event_locks = defaultdict(asyncio.Lock)  # task_id/run_id -> lock


class StructuredFormatter(logging.Formatter):
    """
    Custom JSON formatter with additional fields.
    
    This formatter creates structured JSON log entries with consistent fields
    including timestamps, log levels, logger names, service information,
    environment context, and optional request context. It ensures logs
    are easily parseable and searchable in log aggregation systems.
    
    The formatted logs include:
    - Standard log metadata (timestamp, level, logger, message)
    - Service identification (name, environment, version)
    - Request context (request_id, user_id, client_ip)
    - Exception information when present
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        This method transforms a standard Python logging record into a
        structured JSON format with consistent fields for log aggregation
        and analysis. It includes service metadata, request context, and
        exception information when available.
        
        Args:
            record (logging.LogRecord): The log record to format
            
        Returns:
            str: JSON-formatted log entry as a string
        """
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': settings.PROJECT_NAME,
            'environment': settings.ENVIRONMENT,
            'version': getattr(settings, 'VERSION', 'unknown'),
        }

        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'client_ip'):
            log_entry['client_ip'] = record.client_ip

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class OrchestratorEventFormatter(logging.Formatter):
    """
    Specialized formatter for orchestrator events - newline-delimited JSON.
    
    This formatter creates newline-delimited JSON log entries specifically
    designed for orchestrator events that will be consumed via Server-Sent
    Events (SSE). It includes event metadata, task/run context, and structured
    fields for real-time monitoring and filtering.
    
    The formatted events include:
    - Standard event metadata (timestamp, level, logger)
    - Event type information for SSE consumption
    - Task and run context for filtering and correlation
    - Custom extra fields from the log record
    - Message content and exception information
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as newline-delimited JSON for SSE consumption.
        
        This method transforms a logging record into a newline-delimited JSON
        format suitable for Server-Sent Events streaming. It includes event
        type information, task/run context for filtering, custom fields,
        message content, and exception details when available.
        
        Args:
            record (logging.LogRecord): The log record to format
            
        Returns:
            str: Newline-delimited JSON-formatted event as a string
        """
        # Create the base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
        }

        # Add event field (required for SSE)
        if hasattr(record, 'event'):
            log_entry['event'] = record.event
        else:
            # Default event type if not specified
            log_entry['event'] = 'log'

        # Add task/run context for filtering
        if hasattr(record, 'task_id'):
            log_entry['task_id'] = record.task_id
        if hasattr(record, 'run_id'):
            log_entry['run_id'] = record.run_id

        # Add any extra fields from the record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Add the message
        if record.getMessage():
            log_entry['message'] = record.getMessage()

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def get_logging_config(log_level: str = "INFO", log_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive logging configuration.
    
    This function generates a complete logging configuration dictionary that
    can be used with Python's logging.config.dictConfig(). It supports
    different formatters for different environments, console and file
    handlers with rotation, and specialized loggers for various components.
    
    The configuration includes:
    - JSON and console formatters for structured vs readable logs
    - Console handler with environment-specific formatting
    - Optional rotating file handler
    - Pre-configured loggers for web framework components
    - Specialized orchestrator event logger
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (Optional[str]): Optional log file path for file output
        
    Returns:
        Dict[str, Any]: Logging configuration dictionary ready for dictConfig()
    """
    # Convert string log level to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Base configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': StructuredFormatter,
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            },
            'console': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'orchestrator_events': {
                '()': OrchestratorEventFormatter,
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'console' if settings.ENVIRONMENT == 'local' else 'json',
                'stream': sys.stdout,
                'level': numeric_level,
            },
        },
        'orchestrator_events_handlers': {},  # Will be populated by setup_orchestrator_logging
        'loggers': {
            '': {  # Root logger
                'handlers': ['console'],
                'level': numeric_level,
                'propagate': False,
            },
            'uvicorn': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'uvicorn.access': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'fastapi': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'sqlalchemy': {
                'handlers': ['console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'orchestrator_events': {
                'handlers': [],  # Will be populated by setup_orchestrator_logging
                'level': 'INFO',
                'propagate': False,
            },
            'orchestrator': {
                'handlers': ['console'],
                'level': numeric_level,
                'propagate': False,
            },
        },
    }

    # Add file handler if log file is specified
    if log_file:
        log_file_path = Path(log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'json',
            'filename': str(log_file_path),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'level': numeric_level,
        }

        # Add file handler to root logger
        config['loggers']['']['handlers'].append('file')

    return config


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Setup comprehensive logging configuration.
    
    This function configures the Python logging system using the comprehensive
    configuration generated by get_logging_config(). It applies the configuration
    using logging.config.dictConfig() and logs an informational message about
    the logging setup.
    
    The function should typically be called once during application startup
    to establish the logging configuration for the entire application lifecycle.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (Optional[str]): Optional log file path for file output
    """
    config = get_logging_config(log_level, log_file)
    logging.config.dictConfig(config)

    # Set up additional loggers for specific modules
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            'log_level': log_level,
            'log_file': log_file,
            'environment': settings.ENVIRONMENT,
        }
    )


def setup_orchestrator_logging(orch_id: str, log_file: str) -> None:
    """
    Setup orchestrator event logging with newline-delimited JSON format.
    
    This function configures specialized logging for orchestrator events
    using the OrchestratorEventFormatter. It creates a rotating file handler
    specifically for orchestrator events and configures the 'orchestrator_events'
    logger to use this handler. This enables separate logging of orchestrator
    events in a format suitable for Server-Sent Events (SSE) streaming.
    
    The function ensures the log directory exists, creates a rotating file
    handler with appropriate size limits, and configures the specialized
    orchestrator event logger with the correct formatter and level.
    
    Args:
        orch_id (str): Orchestrator ID (o-glm, o-qwen, o-grok) for identification
        log_file (str): Path to the log file for orchestrator events
    """
    # Ensure the log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create the file handler for orchestrator events
    handler_name = f'orchestrator_events_file_{orch_id}'
    handler_config = {
        'class': 'logging.handlers.RotatingFileHandler',
        'formatter': 'orchestrator_events',
        'filename': str(log_path),
        'maxBytes': 10 * 1024 * 1024,  # 10MB
        'backupCount': 5,
        'level': 'INFO',
    }

    # Create and configure the file handler
    handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path),
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    handler.setFormatter(OrchestratorEventFormatter())
    handler.setLevel(logging.INFO)

    # Configure the orchestrator_events logger to use this handler
    orch_logger = logging.getLogger('orchestrator_events')
    orch_logger.setLevel(logging.INFO)
    orch_logger.addHandler(handler)
    orch_logger.propagate = False

    logger = logging.getLogger(__name__)
    logger.info(f"Orchestrator event logging configured for {orch_id} -> {log_file}")


def get_request_logger(request_id: Optional[str] = None, user_id: Optional[str] = None, client_ip: Optional[str] = None):
    """
    Get a logger with request context.
    
    This function creates a logger with request-specific context information
    including request ID for tracing, user ID for audit logging, and client
    IP address for security monitoring. It uses LoggerAdapter to inject
    context into log records automatically.
    
    The context information is added to all log records produced by the
    returned logger, enabling traceability and audit capabilities.
    
    Args:
        request_id (Optional[str]): Request ID for distributed tracing
        user_id (Optional[str]): User ID for audit logging
        client_ip (Optional[str]): Client IP address for security monitoring
        
    Returns:
        Logger: Logger instance with request context injected
    """
    logger = logging.getLogger('request')

    # Add context to logger
    if request_id:
        logger = logging.LoggerAdapter(logger, {'request_id': request_id})
    if user_id:
        logger = logging.LoggerAdapter(logger, {'user_id': user_id})
    if client_ip:
        logger = logging.LoggerAdapter(logger, {'client_ip': client_ip})

    return logger


def log_orchestrator_event(event: str, task_id: Optional[str] = None, run_id: Optional[str] = None, **extra_fields):
    """
    Log an orchestrator event in the format required for SSE consumption.
    Also stores events in memory for real-time streaming.
    
    This function logs orchestrator events using the specialized
    'orchestrator_events' logger with the OrchestratorEventFormatter.
    It creates structured log entries with event type, task/run context,
    and custom fields. Additionally, it stores events in an in-memory
    data structure for real-time Server-Sent Events (SSE) streaming.
    
    The function supports filtering events by task ID or run ID and
    includes memory management to prevent unbounded growth of the
    event store.
    
    Args:
        event (str): Event type (required for SSE event categorization)
        task_id (Optional[str]): Task ID for event filtering and correlation
        run_id (Optional[str]): Run ID for event filtering and correlation
        **extra_fields: Additional fields to include in the log entry
    """
    logger = logging.getLogger('orchestrator_events')

    # Create a log record with the required fields
    extra = {
        'event': event,
        'extra_fields': extra_fields
    }

    if task_id:
        extra['task_id'] = task_id
    if run_id:
        extra['run_id'] = run_id

    # Log the event
    logger.info(f"Event: {event}", extra=extra)

    # Store event for SSE streaming (if task_id or run_id provided)
    if task_id or run_id:
        key = task_id or run_id
        event_data = {
            'id': str(uuid.uuid4()),
            'event': event,
            'timestamp': datetime.utcnow().isoformat(),
            'task_id': task_id,
            'run_id': run_id,
            **extra_fields
        }
        
        # Store in memory for streaming
        _orchestrator_events[key].append(event_data)
        
        # Keep only the last 1000 events per key to prevent memory issues
        if len(_orchestrator_events[key]) > 1000:
            _orchestrator_events[key] = _orchestrator_events[key][-1000:]


async def get_orchestrator_events(task_id: Optional[str] = None, run_id: Optional[str] = None) -> list:
    """
    Get orchestrator events for a specific task or run ID.
    
    This asynchronous function retrieves stored orchestrator events for
    a specific task or run ID from the in-memory event store. It uses
    async locks to ensure thread-safe access to the shared event data.
    
    The function returns a copy of the event list to prevent external
    modification of the internal event store. If neither task_id nor
    run_id is provided, it returns an empty list.
    
    Args:
        task_id (Optional[str]): Task ID to filter events
        run_id (Optional[str]): Run ID to filter events
        
    Returns:
        list: List of events for the specified task or run ID
    """
    key = task_id or run_id
    if not key:
        return []
    
    async with _orchestrator_event_locks[key]:
        return list(_orchestrator_events.get(key, []))


async def stream_orchestrator_events(task_id: Optional[str] = None, run_id: Optional[str] = None):
    """
    Stream orchestrator events as Server-Sent Events.

    This asynchronous generator function streams orchestrator events
    as Server-Sent Events (SSE) for real-time monitoring and visualization.
    It first sends all existing events for the specified task or run ID,
    then continuously polls for new events and streams them as they occur.

    The function uses async locks to ensure thread-safe access to the
    shared event store and implements efficient polling with a 1-second
    interval to balance responsiveness with resource usage.

    Args:
        task_id (Optional[str]): Task ID to filter events
        run_id (Optional[str]): Run ID to filter events

    Yields:
        str: SSE formatted event data as newline-delimited JSON
    """
    key = task_id or run_id
    if not key:
        return
    
    last_event_id = 0
    async with _orchestrator_event_locks[key]:
        events = list(_orchestrator_events.get(key, []))
    
    # Send initial events
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"
        last_event_id = max(last_event_id, len(events))
    
    # Keep streaming new events
    while True:
        await asyncio.sleep(1)  # Check for new events every second
        async with _orchestrator_event_locks[key]:
            events = list(_orchestrator_events.get(key, []))
        
        # Send new events
        if len(events) > last_event_id:
            for event in events[last_event_id:]:
                yield f"data: {json.dumps(event)}\n\n"
            last_event_id = len(events)


# Setup logging on import
# Automatically configure logging when the module is imported
# using settings from the application configuration
setup_logging(
    log_level=getattr(settings, 'LOG_LEVEL', 'INFO'),
    log_file=getattr(settings, 'LOG_FILE', None),
)
