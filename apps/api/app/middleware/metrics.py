"""Prometheus metrics middleware."""

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

tasks_total = Counter(
    'tasks_total',
    'Total tasks created',
    ['project_id', 'status']
)

crew_runs_total = Counter(
    'crew_runs_total',
    'Total crew runs',
    ['crew_id', 'status']
)

crew_run_duration_seconds = Histogram(
    'crew_run_duration_seconds',
    'Crew run duration in seconds',
    ['crew_id'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

active_terminals = Gauge(
    'active_terminals',
    'Number of active terminal WebSocket connections'
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total WebSocket messages',
    ['direction', 'endpoint']  # direction: sent/received
)


class MetricsMiddleware:
    """Middleware to collect Prometheus metrics."""
    
    async def __call__(
        self, 
        request: Request, 
        call_next: Callable
    ) -> Response:
        """
        Process request and collect metrics.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from handler
        """
        # Skip metrics for /metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        # Track in-progress requests
        http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).inc()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()
        
        return response


def get_metrics() -> Response:
    """
    Get Prometheus metrics.
    
    Returns:
        Response with metrics in Prometheus format
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Helper functions to track application-specific metrics

def track_task_created(project_id: str, status: str = "queued"):
    """Track task creation."""
    tasks_total.labels(project_id=project_id, status=status).inc()


def track_crew_run_started(crew_id: str):
    """Track crew run start."""
    crew_runs_total.labels(crew_id=crew_id, status="started").inc()


def track_crew_run_completed(crew_id: str, status: str, duration: float):
    """Track crew run completion."""
    crew_runs_total.labels(crew_id=crew_id, status=status).inc()
    crew_run_duration_seconds.labels(crew_id=crew_id).observe(duration)


def track_terminal_connected():
    """Track terminal connection."""
    active_terminals.inc()


def track_terminal_disconnected():
    """Track terminal disconnection."""
    active_terminals.dec()


def track_websocket_message(direction: str, endpoint: str = "/ws/terminal"):
    """Track WebSocket message."""
    websocket_messages_total.labels(direction=direction, endpoint=endpoint).inc()
