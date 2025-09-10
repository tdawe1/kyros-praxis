from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Job
from ..auth import get_current_user, User
from ..utils.validation import JobCreate
import json
import hashlib


class JobResponse(BaseModel):
    id: str
    name: str
    status: str


class JobListResponse(BaseModel):
    jobs: List[JobResponse]


router = APIRouter()


@router.post("/jobs", response_model=JobResponse)
def create_job(
    job_input: JobCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = Job(name=job_input.title)
    db.add(job)
    db.commit()
    db.refresh(job)
    job_dict = {"job_id": str(job.id), "status": job.status}
    canonical = json.dumps(job_dict, sort_keys=True)
    etag = hashlib.sha256(canonical.encode()).hexdigest()
    response = JSONResponse(content=job_dict)
    response.headers["ETag"] = etag
    return response


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jobs = db.execute(select(Job)).scalars().all()
    items = []
    for j in jobs:
        items.append({
            "id": str(j.id),
            "name": j.name,
            "status": j.status
        })
    canonical = json.dumps(items, sort_keys=True)
    etag = hashlib.sha256(canonical.encode()).hexdigest()
    response = JSONResponse(content={"jobs": items})
    response.headers["ETag"] = etag
    return response


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_by_id(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job_dict = {"id": str(job.id), "name": job.name, "status": job.status}
    canonical = json.dumps(job_dict, sort_keys=True)
    etag = hashlib.sha256(canonical.encode()).hexdigest()
    response = JSONResponse(content=job_dict)
    response.headers["ETag"] = etag
    return response
