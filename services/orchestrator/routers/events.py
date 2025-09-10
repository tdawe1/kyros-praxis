from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from repositories.jobs import add_event
from database import get_db_session
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from auth import get_current_user


router = APIRouter()


class EventCreate(BaseModel):
    type: str = Field(..., min_length=1)
    payload: dict = Field(..., max_length=1000)  # Limit payload size


@router.post("/events")
async def create_event_endpoint(
    event_create: EventCreate,
    if_match: str = Header(None),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user),
):
    if if_match is None:
        raise HTTPException(
            status_code=412,
            detail="If-Match header required for append-only"
        )
    # For append-only, log mismatch but proceed as new event
    if if_match != "append-only":
        print(f"ETag mismatch: expected 'append-only', got {if_match}")
    event = await add_event(
        session,
        event_create.type,
        event_create.payload
    )
    # Emit event for event creation
    print(f"Event emitted: Event created with id {event.id}")
    response = JSONResponse(
        content={"id": str(event.id), "type": event.type}
    )
    response.headers["ETag"] = str(event.id)
    return response
