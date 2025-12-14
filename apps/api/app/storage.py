from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from .db.models import CrewEvent, CrewRun
from .db.session import AsyncSessionLocal
from .models import Run, RunStatus


@dataclass
class RunRecord:
    run: Run
    created_at: datetime
    updated_at: datetime
    events: List[Dict[str, Any]] = field(default_factory=list)
    canceled: bool = False


class PostgresStore:
    async def create_run(self, crew_id: str, payload: Dict[str, Any]) -> Run:
        async with AsyncSessionLocal() as session:
            run_id = str(uuid4())
            run_row = CrewRun(id=run_id, crew_id=crew_id, status=RunStatus.queued.value, input=payload)
            session.add(run_row)
            await session.flush()
            await self._add_event(session, run_id, "state", {"status": RunStatus.queued.value})
            await session.commit()
            return Run(id=run_id, crew_id=crew_id, status=RunStatus.queued, input=payload)

    async def get_run(self, run_id: str) -> Optional[RunRecord]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CrewRun)
                .options(selectinload(CrewRun.events))
                .where(CrewRun.id == run_id)
            )
            run_row = result.scalar_one_or_none()
            if not run_row:
                return None
            run = Run(
                id=run_row.id,
                crew_id=run_row.crew_id,
                status=RunStatus(run_row.status),
                input=run_row.input,
                result=run_row.result,
            )
            events = [self._event_to_dict(ev) for ev in run_row.events]
            return RunRecord(run=run, created_at=run_row.created_at, updated_at=run_row.updated_at, events=events, canceled=run_row.canceled)

    async def update_status(self, run_id: str, status: RunStatus, result: Optional[Dict[str, Any]] = None) -> None:
        async with AsyncSessionLocal() as session:
            stmt = (
                update(CrewRun)
                .where(CrewRun.id == run_id)
                .values(status=status.value, result=result, updated_at=datetime.now(timezone.utc))
                .returning(CrewRun.id)
            )
            res = await session.execute(stmt)
            if res.scalar_one_or_none() is None:
                await session.rollback()
                return
            await self._add_event(session, run_id, "state", {"status": status.value})
            await session.commit()

    async def add_event(self, run_id: str, event: Dict[str, Any]) -> None:
        async with AsyncSessionLocal() as session:
            await self._add_event(session, run_id, event.get("type", "message"), event)
            await session.commit()

    async def cancel(self, run_id: str) -> bool:
        async with AsyncSessionLocal() as session:
            stmt = (
                update(CrewRun)
                .where(CrewRun.id == run_id)
                .values(canceled=True, status=RunStatus.canceled.value, updated_at=datetime.now(timezone.utc))
                .returning(CrewRun.id)
            )
            res = await session.execute(stmt)
            run_pk = res.scalar_one_or_none()
            if run_pk is None:
                await session.rollback()
                return False
            await self._add_event(session, run_id, "state", {"status": RunStatus.canceled.value})
            await session.commit()
            return True

    async def list_events_since(self, run_id: str, last_id: int = 0) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CrewEvent)
                .where(CrewEvent.run_id == run_id, CrewEvent.id > last_id)
                .order_by(CrewEvent.id)
            )
            events = result.scalars().all()
            return [self._event_to_dict(ev) for ev in events]

    async def get_status(self, run_id: str) -> Optional[RunStatus]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(CrewRun.status).where(CrewRun.id == run_id))
            status = result.scalar_one_or_none()
            if status is None:
                return None
            return RunStatus(status)

    async def _add_event(self, session, run_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        normalized = {k: v for k, v in payload.items() if k != "type"}
        event = CrewEvent(run_id=run_id, type=event_type, payload=normalized, message=normalized.get("message"))
        session.add(event)

    @staticmethod
    def _event_to_dict(event: CrewEvent) -> Dict[str, Any]:
        data = {"id": event.id, "type": event.type, "ts": event.ts.isoformat()}
        normalized_payload = event.payload or {}
        data.update(normalized_payload)
        if event.message and "message" not in data:
            data["message"] = event.message
        return data


store = PostgresStore()

