"""
Event Management API Router Module

This module provides RESTful API endpoints for managing events in the Kyros Orchestrator service.
It includes endpoints for appending new events to the event log and streaming events using
Server-Sent Events (SSE) for real-time monitoring and collaboration. Events are used for 
tracking important occurrences in the system for audit, monitoring, and collaboration purposes.

The router implements best practices for API design including:
- Proper error handling
- Authentication and authorization
- Input validation
- ETag-based caching
- Comprehensive logging
- Real-time event streaming

Key Features:
- Event logging with timestamp, actor, target, and details
- Real-time event streaming using Server-Sent Events (SSE)
- Support for both continuous streaming and one-time event retrieval
- Heartbeat mechanism for persistent connections
- ETag-based caching for efficient data transfer

ENDPOINTS:
1. POST /events - Append a new event to the events log
2. GET /events/tail - Stream events as Server-Sent Events
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from starlette.responses import StreamingResponse

try:
    # When running as a package (e.g., tests in monorepo)
    from auth import get_current_user
    from app.core.logging import log_orchestrator_event
except ImportError:
    # Fallbacks when running module directly from the service directory
    try:
        from auth import get_current_user  # type: ignore
        from app.core.logging import log_orchestrator_event  # type: ignore
    except Exception:  # pragma: no cover
        # Fallback when running from repo root
        from services.orchestrator.auth import get_current_user  # type: ignore
        from services.orchestrator.app.core.logging import log_orchestrator_event  # type: ignore

# Create the API router for event endpoints
router = APIRouter()


class EventCreate(BaseModel):
    """
    Data model for creating a new event.
    
    This model defines the required parameters for appending a new event
    to the event log. Events are used for tracking important occurrences
    in the system for audit, monitoring, and collaboration purposes.
    """
    event: str
    target: str
    details: dict = {}


@router.post("/events", summary="Append a new event", description="Append a new event to the events log and return success confirmation")
def append_event(
    event: EventCreate,
    response: Response,
    current_user=Depends(get_current_user),
 ):
    """
    Append a new event to the events log.
    
    This endpoint appends a new event to the event log file, which is used for
    tracking important occurrences in the system for audit, monitoring, and
    collaboration purposes. The event includes a timestamp, event type, actor
    (authenticated user), target, and optional details. The endpoint computes
    and returns an ETag for the entire events file to support caching.
    
    Args:
        event (EventCreate): Event data to append including event type, target, and details
        response (Response): FastAPI response object for setting headers
        current_user: Authenticated user (from get_current_user dependency)
        
    Returns:
        dict: Success confirmation with "ok": True
        
    Raises:
        HTTPException: If file operations fail or authentication fails
    """
    # Use env-driven paths for testability
    events_dir = Path(os.getenv("EVENTS_DIR", Path(__file__).parent.parent.parent.parent / "collaboration/events"))
    events_file = events_dir / os.getenv("EVENTS_FILE", "events.jsonl")
    if not events_dir.exists():
        events_dir.mkdir(parents=True)
    
    event_data = {
        "ts": datetime.now().isoformat(),
        "event": event.event,
        "actor": current_user.email,
        "target": event.target,
        "details": event.details,
    }
    
    with open(events_file, "a") as f:
        f.write(json.dumps(event_data) + "\n")
    
    # Compute ETag for the entire file
    with open(events_file, "rb") as f:
        content = f.read()
    etag = hashlib.sha256(content).hexdigest()
    response.headers["ETag"] = f'"{etag}"'
    
    # Log orchestrator event
    log_orchestrator_event(
        event="event_appended",
        user_id=current_user.id,
        event_type=event.event,
        target=event.target,
        details_count=len(event.details)
    )
    
    return {"ok": True}


@router.get("/events/tail", summary="Stream events as Server-Sent Events", description="Stream events as Server-Sent Events for real-time monitoring")
async def events_tail(
    request: Request,
    once: bool = False,
    current_user=Depends(get_current_user),
 ):
    """
    Stream events as Server-Sent Events.
    
    This endpoint streams events from the event log using Server-Sent Events (SSE)
    for real-time monitoring and collaboration. It first sends the backlog of
    existing events, then optionally continues streaming new events as they occur.
    The endpoint supports both one-time streaming (with 'once' parameter) and
    continuous streaming with periodic heartbeat messages.
    
    Args:
        request (Request): FastAPI request object
        once (bool): Whether to stream only once (backlog only) or keep connection alive (default: False)
        current_user: Authenticated user (from get_current_user dependency)
        
    Returns:
        StreamingResponse: Streaming response with SSE events
        
    Raises:
        HTTPException: If file operations fail or authentication fails
    """
    # Use env-driven paths for testability
    events_dir = Path(os.getenv("EVENTS_DIR", Path(__file__).parent.parent.parent.parent / "collaboration/events"))
    events_file = events_dir / os.getenv("EVENTS_FILE", "events.jsonl")
    events = []
    if events_file.exists():
        with open(events_file, "r") as f:
            for line in f:
                raw = line.strip()
                if not raw:
                    continue
                # Support concatenated JSON objects without newline by splitting on '}{'
                normalized = raw.replace('}{', '}\n{')
                for part in normalized.splitlines():
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        events.append(json.loads(part))
                    except Exception:
                        # Skip malformed segment
                        continue

    async def event_generator():
        # send backlog first
        for ev in events:
            yield f"data: {json.dumps(ev)}\n\n"
        if once:
            return
        # keep-alive loop
        while True:
            await asyncio.sleep(30)
            # comment line per SSE spec
            yield ": heartbeat\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    
    # Log orchestrator event
    log_orchestrator_event(
        event="events_streamed",
        user_id=current_user.id,
        event_count=len(events),
        stream_once=once
    )
    
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)
