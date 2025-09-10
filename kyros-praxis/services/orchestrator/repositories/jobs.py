from sqlalchemy import select
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Job, Event

async def get_jobs(session: AsyncSession) -> List[Job]:
    result = await session.execute(select(Job))
    return result.scalars().all()

async def create_job(session: AsyncSession, name: str) -> Job:
    job = Job(name=name)
    session.add(job)
    try:
        await session.commit()
        await session.refresh(job)
        return job
    except Exception:
        await session.rollback()
        raise

async def add_event(
    session: AsyncSession,
    event_type: str,
    payload: dict
) -> Event:
    event = Event(type=event_type, payload=payload)
    session.add(event)
    try:
        await session.commit()
        await session.refresh(event)
        return event
    except Exception:
        await session.rollback()
        raise
