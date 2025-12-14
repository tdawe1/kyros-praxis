"""Shared memory system for agent coordination."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import MemoryEvent, SharedMemory
from ..db.session import AsyncSessionLocal


class SharedMemoryService:
    """Service for managing shared memory between agents."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
    
    async def set(
        self, 
        project_id: str, 
        key: str, 
        value: Dict[str, Any],
        created_by: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> SharedMemory:
        """
        Store or update a value in shared memory.
        
        Uses atomic upsert to prevent race conditions.
        
        Args:
            project_id: Project ID
            key: Memory key
            value: JSON-serializable value
            created_by: ID of creator (run_id or user_id)
            ttl: Time to live in seconds
            
        Returns:
            SharedMemory object
        """
        from uuid import uuid4
        from sqlalchemy.dialects.postgresql import insert
        
        async with AsyncSessionLocal() as session:
            expires_at = None
            if ttl:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            
            now = datetime.now(timezone.utc)
            
            # Use PostgreSQL's INSERT ... ON CONFLICT UPDATE (atomic upsert)
            stmt = insert(SharedMemory).values(
                id=str(uuid4()),
                project_id=project_id,
                key=key,
                value=value,
                created_by=created_by,
                created_at=now,
                expires_at=expires_at
            )
            
            # On conflict (duplicate project_id, key), update the values
            stmt = stmt.on_conflict_do_update(
                constraint='uq_shared_memory_project_key',
                set_=dict(
                    value=stmt.excluded.value,
                    created_by=stmt.excluded.created_by,
                    created_at=stmt.excluded.created_at,
                    expires_at=stmt.excluded.expires_at
                )
            )
            
            await session.execute(stmt)
            await session.commit()
            
            # Retrieve the memory object
            result = await session.execute(
                select(SharedMemory).where(
                    SharedMemory.project_id == project_id,
                    SharedMemory.key == key
                )
            )
            memory = result.scalars().first()
            
            # Publish event
            await self.publish_event(
                project_id=project_id,
                event_type="memory_updated",
                payload={"key": key, "created_by": created_by}
            )
            
            return memory
    
    async def get(
        self, 
        project_id: str, 
        key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a value from shared memory.
        
        Args:
            project_id: Project ID
            key: Memory key
            
        Returns:
            Value if found and not expired, None otherwise
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SharedMemory).where(
                    SharedMemory.project_id == project_id,
                    SharedMemory.key == key
                )
            )
            memory = result.scalars().first()
            
            if not memory:
                return None
            
            # Check expiration
            if memory.expires_at and memory.expires_at < datetime.now(timezone.utc):
                # Expired - delete it
                await session.delete(memory)
                await session.commit()
                return None
            
            return memory.value
    
    async def get_all(
        self, 
        project_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all memory values for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Dictionary of key-value pairs
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SharedMemory).where(
                    SharedMemory.project_id == project_id
                )
            )
            memories = result.scalars().all()
            
            now = datetime.now(timezone.utc)
            output = {}
            
            for memory in memories:
                # Skip expired
                if memory.expires_at and memory.expires_at < now:
                    continue
                output[memory.key] = memory.value
            
            return output
    
    async def delete(
        self, 
        project_id: str, 
        key: str
    ) -> bool:
        """
        Delete a key from shared memory.
        
        Args:
            project_id: Project ID
            key: Memory key
            
        Returns:
            True if deleted, False if not found
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                delete(SharedMemory).where(
                    SharedMemory.project_id == project_id,
                    SharedMemory.key == key
                )
            )
            await session.commit()
            return result.rowcount > 0
    
    async def publish_event(
        self, 
        project_id: str, 
        event_type: str, 
        payload: Dict[str, Any]
    ):
        """
        Publish an event to all subscribers.
        
        Args:
            project_id: Project ID
            event_type: Type of event
            payload: Event data
        """
        # Store in database
        async with AsyncSessionLocal() as session:
            event = MemoryEvent(
                project_id=project_id,
                event_type=event_type,
                payload=payload
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
        
        # Notify in-memory subscribers
        if project_id in self._subscribers:
            event_data = {
                "id": event.id,
                "project_id": project_id,
                "event_type": event_type,
                "payload": payload,
                "published_at": event.published_at.isoformat()
            }
            
            for queue in self._subscribers[project_id]:
                try:
                    queue.put_nowait(event_data)
                except asyncio.QueueFull:
                    pass  # Skip if queue is full
    
    async def subscribe(
        self, 
        project_id: str,
        since_id: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Subscribe to events for a project (SSE).
        
        Args:
            project_id: Project ID
            since_id: Only get events after this ID
            
        Yields:
            Event dictionaries
        """
        # Create queue for this subscriber
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        
        if project_id not in self._subscribers:
            self._subscribers[project_id] = []
        self._subscribers[project_id].append(queue)
        
        try:
            # First, yield historical events if since_id is provided
            if since_id is not None:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(MemoryEvent)
                        .where(
                            MemoryEvent.project_id == project_id,
                            MemoryEvent.id > since_id
                        )
                        .order_by(MemoryEvent.id)
                    )
                    events = result.scalars().all()
                    
                    for event in events:
                        yield {
                            "id": event.id,
                            "project_id": event.project_id,
                            "event_type": event.event_type,
                            "payload": event.payload,
                            "published_at": event.published_at.isoformat()
                        }
            
            # Then yield new events as they arrive
            while True:
                event = await queue.get()
                yield event
        
        finally:
            # Cleanup on disconnect
            if project_id in self._subscribers:
                try:
                    self._subscribers[project_id].remove(queue)
                except ValueError:
                    pass
                
                if not self._subscribers[project_id]:
                    del self._subscribers[project_id]
    
    async def cleanup_expired(self) -> int:
        """Remove expired memory entries.
        
        Returns the number of rows deleted.
        """
        async with AsyncSessionLocal() as session:
            now = datetime.now(timezone.utc)
            result = await session.execute(
                delete(SharedMemory).where(
                    SharedMemory.expires_at < now
                )
            )
            await session.commit()
            # In SQLAlchemy 2.x, rowcount may be -1 for some dialects; normalize to 0 minimum.
            try:
                count = int(getattr(result, 'rowcount', 0) or 0)
            except Exception:
                count = 0
            return count


# Global instance
shared_memory = SharedMemoryService()
