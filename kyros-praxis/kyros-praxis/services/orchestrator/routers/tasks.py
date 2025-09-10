from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Task

router = APIRouter()

class TaskCreate(BaseModel):
    title: str
    description: str

class Task(BaseModel):
    id: str
    title: str
    description: str
    version: int
    created_at: str

@router.post("/collab/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/collab/state/tasks")
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return tasks
