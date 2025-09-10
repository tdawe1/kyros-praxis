from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import json

from database import get_db_session
from models import Task


router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    description: str | None = None


@router.post("/collab/tasks")
async def create_task_endpoint(
    task: TaskCreate,
    session: AsyncSession = Depends(get_db_session),
):
    obj = Task(title=task.title, description=task.description or "")
    session.add(obj)
    await session.commit()
    await session.refresh(obj)

    task_dict = {
        "id": obj.id,
        "title": obj.title,
        "description": obj.description,
        "version": obj.version,
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
    }
    etag = hashlib.sha256(json.dumps(task_dict, sort_keys=True).encode()).hexdigest()
    return JSONResponse(content=task_dict, headers={"ETag": etag})


@router.get("/collab/state/tasks")
async def list_tasks_endpoint(
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(select(Task))
    items = []
    for t in result.scalars().all():
        items.append(
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "version": t.version,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
        )

    payload = {"kind": "tasks", "items": items}
    etag = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return JSONResponse(content=payload, headers={"ETag": etag})

