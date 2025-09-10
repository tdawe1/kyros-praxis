from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session, sessionmaker
import json
import hashlib
from fastapi.responses import JSONResponse
from models import engine, Task
from pydantic import BaseModel


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TaskCreate(BaseModel):
    title: str
    description: str


app = FastAPI()


@app.post("/collab/tasks")
def create_task(task: TaskCreate = Body(...), db: Session = Depends(get_db)):
    task_model = Task(title=task.title, description=task.description)
    db.add(task_model)
    db.commit()
    db.refresh(task_model)
    task_dict = {
        "id": task_model.id,
        "title": task_model.title,
        "description": task_model.description,
        "version": task_model.version
    }
    etag = hashlib.sha256(
        json.dumps(task_dict, sort_keys=True).encode()
    ).hexdigest()
    return JSONResponse(content=task_dict, headers={"ETag": etag})


@app.get("/collab/state/tasks")
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    task_dicts = []
    for task in tasks:
        task_dicts.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "version": task.version
        })
    payload = {"kind": "tasks", "items": task_dicts}
    etag = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()
    return JSONResponse(content=payload, headers={"ETag": etag})


@app.get("/healthz")
async def healthz(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database unavailable")