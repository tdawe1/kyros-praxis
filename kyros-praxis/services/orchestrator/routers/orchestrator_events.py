"""
Orchestrator Events Streaming API Router Module

This module provides RESTful API endpoints for streaming and retrieving orchestrator events in the Kyros Orchestrator service.
It includes endpoints for real-time event streaming using Server-Sent Events (SSE) and for retrieving historical events. 
These endpoints are essential for monitoring task execution, debugging issues, and gaining insights into system behavior.

Orchestrator events provide detailed information about:
- Task execution progress and status changes
- System operations and internal processes
- Error conditions and exception handling
- Resource utilization and performance metrics
- Integration points and external service interactions

The router implements best practices for API design including:
- Proper error handling
- Authentication and authorization
- Input validation
- Real-time event streaming
- Fallback mechanisms for different environments

Key Features:
- Real-time event streaming with Server-Sent Events (SSE)
- Historical event retrieval for analysis and debugging
- Filtering capabilities by task ID or run ID
- Graceful handling of client disconnections
- Fallback mechanisms for environments without SSE support

ENDPOINTS:
1. GET /orchestrator/events/stream - Stream orchestrator events as Server-Sent Events
2. GET /orchestrator/events - Get orchestrator events for a specific task or run
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

try:
    from sse_starlette.sse import EventSourceResponse
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    EventSourceResponse = None

try:
    # When running as a package (e.g., tests in monorepo)
    from ..auth import get_current_user
    from ..app.core.logging import stream_orchestrator_events
except ImportError:
    # Fallback when running module directly
    from services.orchestrator.auth import get_current_user  # type: ignore
    from services.orchestrator.app.core.logging import stream_orchestrator_events  # type: ignore

# Create the API router for orchestrator event endpoints
router = APIRouter()


@router.get("/orchestrator/events/stream", summary="Stream orchestrator events as Server-Sent Events", description="Stream orchestrator events in real-time using Server-Sent Events for monitoring and debugging")
async def stream_events(
    request: Request,
    task_id: Optional[str] = None,
    run_id: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """
    Stream orchestrator events as Server-Sent Events.
    
    This endpoint streams orchestrator events in real-time using Server-Sent Events (SSE)
    for monitoring and debugging purposes. It allows clients to receive live updates about
    task or run progress, status changes, and other important events in the orchestrator.
    The stream can be filtered by either task ID or run ID.
    
    Args:
        request (Request): FastAPI request object for handling client disconnection
        task_id (Optional[str]): Filter events by task ID (either task_id or run_id must be provided)
        run_id (Optional[str]): Filter events by run ID (either task_id or run_id must be provided)
        current_user: Authenticated user (from get_current_user dependency)
        
    Returns:
        Union[EventSourceResponse, StreamingResponse, dict]: 
            - EventSourceResponse with SSE events if sse_starlette is available
            - StreamingResponse with plain text events as fallback
            - Error dictionary if neither task_id nor run_id is provided
            
    Raises:
        HTTPException: If authentication fails or other errors occur
    """
    if not task_id and not run_id:
        return {"error": "Either task_id or run_id must be provided"}
    
    async def event_generator():
        """
        Asynchronous generator that yields events from the orchestrator event stream.
        
        This generator continuously yields events from the orchestrator event stream,
        checking for client disconnection to properly terminate the stream when the
        client disconnects.
        
        Yields:
            dict: Orchestrator events as dictionaries
        """
        async for event in stream_orchestrator_events(task_id=task_id, run_id=run_id):
            yield event
            
            # Check if client disconnected
            if await request.is_disconnected():
                break
    
    if not SSE_AVAILABLE:
        return StreamingResponse(event_generator(), media_type="text/plain")
    return EventSourceResponse(event_generator())


@router.get("/orchestrator/events", summary="Get orchestrator events for a specific task or run", description="Retrieve historical orchestrator events for a specific task or run")
async def get_events(
    task_id: Optional[str] = None,
    run_id: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """
    Get orchestrator events for a specific task or run.
    
    This endpoint retrieves historical orchestrator events for a specific task or run.
    It allows clients to fetch past events for analysis, debugging, or audit purposes.
    The results can be filtered by either task ID or run ID.
    
    Args:
        task_id (Optional[str]): Filter events by task ID (either task_id or run_id must be provided)
        run_id (Optional[str]): Filter events by run ID (either task_id or run_id must be provided)
        current_user: Authenticated user (from get_current_user dependency)
        
    Returns:
        dict: Dictionary containing events list or error message
        
    Raises:
        HTTPException: If authentication fails or other errors occur
    """
    from ..app.core.logging import get_orchestrator_events
    
    if not task_id and not run_id:
        return {"error": "Either task_id or run_id must be provided"}
        
    events = await get_orchestrator_events(task_id=task_id, run_id=run_id)
    return {"events": events}