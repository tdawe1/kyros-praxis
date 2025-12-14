"""API endpoints for batch crew runs."""

import asyncio
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user_required
from ..db.models import Project, Task, User
from ..db.session import get_session
from ..memory.shared_memory import shared_memory
from ..models_multi_agent import BatchRunCreate, BatchRunResponse, TaskResponse
from ..storage import store
from ..workflows.pipeline import workflow_pipeline


router = APIRouter(prefix="/batch", tags=["batch-runs"])


def _create_workflow_task(task_id: str, project_id: str, task_input: dict):
    """Create async task for workflow execution in background."""
    asyncio.create_task(
        workflow_pipeline.execute_task(
            task_id=task_id,
            project_id=project_id,
            task_input=task_input
        )
    )


@router.post("/runs", response_model=BatchRunResponse, status_code=status.HTTP_201_CREATED)
async def create_batch_runs(
    batch_data: BatchRunCreate,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """
    Create multiple crew runs at once for parallel execution.
    
    Requires authentication. Only the project owner can create batch runs.
    This creates a task for each item and immediately starts execution.
    """
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == batch_data.project_id)
    )
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create batch runs for this project"
        )
    
    # Create all tasks
    tasks = []
    crew_runs = []
    
    for task_data in batch_data.tasks:
        task = Task(
            id=str(uuid4()),
            project_id=batch_data.project_id,
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority.value,
            status="queued",
            dependencies=task_data.dependencies,
        )
        session.add(task)
        tasks.append(task)
    
    await session.commit()
    
    # Refresh all tasks to get IDs
    for task in tasks:
        await session.refresh(task)
    
    # Start workflow for each task in background
    batch_id = str(uuid4())
    
    for task in tasks:
        # Create async task for workflow execution
        _create_workflow_task(
            task_id=task.id,
            project_id=batch_data.project_id,
            task_input={"prompt": task.description or task.title}
        )
        
        crew_runs.append({
            "task_id": task.id,
            "status": "queued"
        })
    
    # Update project status
    project.status = "executing"
    await session.commit()
    
    # Publish event
    await shared_memory.publish_event(
        project_id=batch_data.project_id,
        event_type="batch_started",
        payload={
            "batch_id": batch_id,
            "task_count": len(tasks)
        }
    )
    
    return BatchRunResponse(
        batch_id=batch_id,
        project_id=batch_data.project_id,
        tasks=[TaskResponse.from_orm(t) for t in tasks],
        crew_runs=crew_runs
    )


@router.get("/runs/{batch_id}/status")
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Get status of all runs in a batch. Requires authentication."""
    # For now, batch_id is not stored, so we return project-wide status
    # In a full implementation, you'd track batch_id
    
    return {
        "batch_id": batch_id,
        "status": "Check project dashboard for task status"
    }


@router.post("/cancel/{batch_id}")
async def cancel_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Cancel all runs in a batch. Requires authentication."""
    # TODO: Implement batch cancellation
    
    return {
        "batch_id": batch_id,
        "status": "cancellation_requested"
    }
