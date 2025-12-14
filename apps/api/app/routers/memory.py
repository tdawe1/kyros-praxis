"""API endpoints for shared memory system."""

import json
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user_required
from ..db.models import Project, User
from ..db.session import get_session
from ..memory.shared_memory import shared_memory
from ..models_multi_agent import MemoryEventPublish, MemoryGet, MemorySet


router = APIRouter(prefix="/memory", tags=["shared-memory"])


@router.post("/set", status_code=status.HTTP_201_CREATED)
async def set_memory(
    memory_data: MemorySet,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Set a value in shared memory. Requires authentication and project access."""
    # Verify project exists and user has access
    await _verify_project_access(memory_data.project_id, current_user.id, session)
    await shared_memory.set(
        project_id=memory_data.project_id,
        key=memory_data.key,
        value=memory_data.value,
        ttl=memory_data.ttl
    )
    
    return {"status": "ok", "key": memory_data.key}


@router.post("/get")
async def get_memory(
    memory_data: MemoryGet,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Get a value from shared memory. Requires authentication and project access."""
    # Verify project exists and user has access
    await _verify_project_access(memory_data.project_id, current_user.id, session)
    value = await shared_memory.get(
        project_id=memory_data.project_id,
        key=memory_data.key
    )
    
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key not found or expired"
        )
    
    return {"key": memory_data.key, "value": value}


@router.get("/{project_id}/all")
async def get_all_memory(
    project_id: str,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
) -> Dict:
    """Get all memory for a project. Requires authentication and project access."""
    # Verify project exists and user has access
    await _verify_project_access(project_id, current_user.id, session)
    values = await shared_memory.get_all(project_id)
    return values


@router.delete("/{project_id}/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    project_id: str,
    key: str,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Delete a key from shared memory. Requires authentication and project access."""
    # Verify project exists and user has access
    await _verify_project_access(project_id, current_user.id, session)
    deleted = await shared_memory.delete(project_id, key)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key not found"
        )


@router.post("/publish")
async def publish_event(
    event_data: MemoryEventPublish,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Publish an event to all subscribers. Requires authentication and project access."""
    # Verify project exists and user has access
    await _verify_project_access(event_data.project_id, current_user.id, session)
    await shared_memory.publish_event(
        project_id=event_data.project_id,
        event_type=event_data.event_type,
        payload=event_data.payload
    )
    
    return {"status": "published"}


@router.get("/{project_id}/events")
async def subscribe_events(
    project_id: str,
    since_id: int = 0,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Subscribe to memory events (SSE stream). Requires authentication and project access."""
    # Verify project exists and user has access
    await _verify_project_access(project_id, current_user.id, session)
    
    async def event_generator():
        async for event in shared_memory.subscribe(project_id, since_id):
            yield f"event: message\ndata: {json.dumps(event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


async def _verify_project_access(project_id: str, user_id: str, session: AsyncSession) -> None:
    """Verify that a project exists and user has access to it.
    
    Args:
        project_id: Project ID
        user_id: User ID
        session: Database session
        
    Raises:
        HTTPException: 404 if project not found, 403 if no access
    """
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership
    if project.created_by != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project's memory"
        )
