from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from ..auth import get_current_user
import json
from datetime import datetime
import os
import hashlib
from pathlib import Path
from sse_starlette.sse import EventSourceResponse

router = APIRouter()

class EventCreate(BaseModel):
    event: str
    target: str
    details: dict = {}

@router.post("/events")
def append_event(event: EventCreate, current_user = Depends(get_current_user)):
    # Path to events file relative to orchestrator/routers/events.py
    # Four parents up to root, then collaboration/events/events.jsonl
    events_file = Path(__file__).parent.parent.parent.parent / 'collaboration/events/events.jsonl'
    events_dir = events_file.parent
    if not events_dir.exists():
        events_dir.mkdir(parents=True)
    event_data = {
        "ts": datetime.now().isoformat(),
        "event": event.event,
        "actor": current_user.email,
        "target": event.target,
        "details": event.details
    }
    with open(events_file, 'a') as f:
        f.write(json.dumps(event_data) + '\n')
    # Compute ETag for the entire file
    with open(events_file, 'rb') as f:
        content = f.read()
    etag = hashlib.sha256(content).hexdigest()
    return {"ok": True}, {"ETag": etag}

@router.get("/events/tail")
async def events_tail(current_user = Depends(get_current_user), request: Request):
    events_file = Path(__file__).parent.parent.parent.parent / 'collaboration/events/events.jsonl'
    events = []
    if events_file.exists():
        with open(events_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line.strip()))
    async def event_generator():
        for event in events:
            yield {"data": json.dumps(event)}
        # Keep-alive loop
        while True:
            await asyncio.sleep(30)
            yield ": heartbeat\n\n"
    return EventSourceResponse(event_generator())
