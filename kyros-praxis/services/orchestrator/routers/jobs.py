from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..utils.validation import validate_job_input, JobCreate
# Lazy wrapper to avoid importing asyncpg unless these endpoints are invoked
async def get_db_session_wrapper():
    from ..repositories.database import get_db_session as _inner
    async for s in _inner():
        yield s
from ..auth import get_current_user, User


async def _create_job(session: AsyncSession, title: str):
    # Map Day-1 JobCreate.title -> Job.name
    from ..models import Job
    job = Job(name=title)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job

router = APIRouter()

@router.post("/jobs")
async def create_job(
    job_input: JobCreate = Body(...),
    session: AsyncSession = Depends(get_db_session_wrapper),
    current_user: User = Depends(get_current_user),
):
    validated_input = validate_job_input(job_input.dict())
    try:
        job = await _create_job(session, validated_input.title)
        response = JSONResponse(
            content={"job_id": str(job.id), "status": "accepted"}
        )
        response.headers["ETag"] = str(job.id)
        return response
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Job creation failed")


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    session: AsyncSession = Depends(get_db_session_wrapper),
    current_user: User = Depends(get_current_user),
):
    # Day-1: not implemented; return 501 to clearly indicate not implemented
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/jobs")
async def get_jobs_endpoint(
    session: AsyncSession = Depends(get_db_session_wrapper),
    current_user: User = Depends(get_current_user),
):
    from ..repositories.jobs import get_jobs as _get_jobs
    jobs = await _get_jobs(session)
    response = JSONResponse(
        content={
            "jobs": [
                {"id": str(j.id), "name": j.name, "status": j.status}
                for j in jobs
            ]
        }
    )
    response.headers["ETag"] = "list-version-1"
    return response


@router.get("/jobs/{job_id}")
async def get_job_by_id(
    job_id: str,
    session: AsyncSession = Depends(get_db_session_wrapper),
    current_user: User = Depends(get_current_user),
):
    from ..models import Job
    obj = await session.get(Job, job_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Job not found")
    content = {"id": str(obj.id), "name": obj.name, "status": obj.status}
    response = JSONResponse(content=content)
    response.headers["ETag"] = str(obj.id)
    return response
