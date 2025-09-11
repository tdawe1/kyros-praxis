from fastapi import APIRouter, HTTPException, Depends, Body, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from ..auth import get_current_user, User
from ..database import get_db_session
from ..models import Job
from ..repositories.jobs import get_jobs
from ..utils.validation import JobCreate, validate_job_input
from ..utils.validation import validate_job_input, JobCreate
# Lazy wrapper to avoid importing database/session machinery unless endpoints are invoked
async def get_db_session_wrapper():
    from ..database import get_db_session as _inner
    async for s in _inner():
        yield s
from ..auth import get_current_user, User
from ..utils import generate_etag


async def _create_job(session: AsyncSession, title: str):
    # Map Day-1 JobCreate.title -> Job.name
    job = Job(name=title)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job

class JobResponse(BaseModel):
    id: str
    name: str
    status: str


router = APIRouter()


@router.post("/jobs", response_model=JobResponse)
async def create_job(
    job_input: JobCreate = Body(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    response: Response = None,
):
    validated_input = validate_job_input(job_input.model_dump())
    try:
        job = await _create_job(session, validated_input.title)
        content = {"id": str(job.id), "name": job.name, "status": job.status}
        if response is not None:
            response.headers["ETag"] = generate_etag(content)
        return content
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Job creation failed")


@router.delete("/jobs/{job_id}")
async def delete_job(
    _job_id: str,
    _session: AsyncSession = Depends(get_db_session),
    _current_user: User = Depends(get_current_user),
):
    # Day-1: not implemented; return 501 to clearly indicate not implemented
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/jobs")
async def get_jobs_endpoint(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    response: Response = None,
):
    jobs = await get_jobs(session)
    payload = {
        "jobs": [
            {"id": str(j.id), "name": j.name, "status": j.status}
            for j in jobs
        ]
    }
    from ..repositories.jobs import get_jobs as _get_jobs
    jobs = await _get_jobs(session)
    items = [
        {"id": str(j.id), "name": j.name, "status": j.status}
        for j in jobs
    ]
    payload = {"jobs": items}
    if response is not None:
        response.headers["ETag"] = generate_etag(items)
    return payload


@router.get("/jobs/{job_id}")
async def get_job_by_id(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    response: Response = None,
):
    obj = await session.get(Job, job_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Job not found")
    content = {"id": str(obj.id), "name": obj.name, "status": obj.status}
    if response is not None:
        response.headers["ETag"] = generate_etag(content)
    return content
