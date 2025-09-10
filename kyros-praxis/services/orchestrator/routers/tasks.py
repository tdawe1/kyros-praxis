from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task
from ..auth import get_current_user, User
from ..utils.validation import validate_task_input, TaskCreate
import json
import hashlib

router = APIRouter()


@router.post("/collab/tasks")
async def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    validated_input = validate_task_input(task.dict())
    db_task = Task(**validated_input.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    task_dict = {
        "id": db_task.id,
        "title": db_task.title,
        "description": db_task.description,
        "version": db_task.version,
        "created_at": db_task.created_at.isoformat()
    }
    canonical = json.dumps(task_dict, sort_keys=True)
    etag = hashlib.sha256(canonical.encode()).hexdigest()
    response = JSONResponse(content=task_dict)
    response.headers["ETag"] = etag
    return response


@router.get("/collab/state/tasks")
async def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    items = []
    for t in tasks:
        items.append({
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "version": t.version,
            "created_at": t.created_at.isoformat()
        })
    canonical = json.dumps(items, sort_keys=True)
    etag = hashlib.sha256(canonical.encode()).hexdigest()
    response = JSONResponse(content={"kind": "tasks", "items": items})
    response.headers["ETag"] = etag
    return response
