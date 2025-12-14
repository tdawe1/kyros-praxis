"""API endpoints for multi-agent projects."""

from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, get_current_user_required
from ..db.models import Artifact, Project, Task, User
from ..db.session import get_session
from ..memory.shared_memory import shared_memory
from ..models_multi_agent import (
    ArtifactResponse,
    ProjectCreate,
    ProjectDashboard,
    ProjectResponse,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from ..workflows.pipeline_refactored import workflow_pipeline
from pydantic import BaseModel

# Import cache utilities
try:
    from ..cache.redis_cache import cache, cache_key_project_dashboard, invalidate_project_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


router = APIRouter(prefix="/projects", tags=["multi-agent-projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new multi-agent project."""
    project = Project(
        id=str(uuid4()),
        name=project_data.name,
        description=project_data.description,
        status="planning",
        created_by=current_user.id if current_user else None,
    )
    
    session.add(project)
    await session.commit()
    await session.refresh(project)
    
    # Invalidate cache for this project
    if CACHE_AVAILABLE:
        await invalidate_project_cache(project.id)
    
    return project


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all projects.
    
    If authenticated, shows only user's projects.
    If not authenticated, shows all projects (public access).
    """
    query = select(Project).order_by(Project.created_at.desc())
    
    if current_user:
        query = query.where(Project.created_by == current_user.id)
    
    result = await session.execute(query)
    projects = result.scalars().all()
    
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific project."""
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_required),
):
    """Update a project and invalidate cache.
    
    Requires authentication. Only the project owner can update it.
    """
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership - always enforce
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this project"
        )
    
    # Update fields
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.status is not None:
        project.status = project_data.status.value
    
    await session.commit()
    await session.refresh(project)
    
    # Invalidate cache
    if CACHE_AVAILABLE:
        await invalidate_project_cache(project.id)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_required),
):
    """Delete a project and all its tasks.
    
    Requires authentication. Only the project owner can delete it.
    """
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership - always enforce
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this project"
        )
    
    await session.delete(project)
    await session.commit()


@router.post("/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: str,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Create a new task in a project. Requires authentication and project ownership."""
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == project_id)
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
            detail="Not authorized to create tasks in this project"
        )
    
    task = Task(
        id=str(uuid4()),
        project_id=project_id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority.value,
        status="queued",
        dependencies=task_data.dependencies,
    )
    
    session.add(task)
    await session.commit()
    await session.refresh(task)
    
    # Invalidate project cache
    if CACHE_AVAILABLE:
        await invalidate_project_cache(project_id)
    
    # Publish event
    await shared_memory.publish_event(
        project_id=project_id,
        event_type="task_created",
        payload={"task_id": task.id, "title": task.title}
    )
    
    return task


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(
    project_id: str,
    session: AsyncSession = Depends(get_session),
):
    """List all tasks in a project."""
    result = await session.execute(
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.created_at)
    )
    tasks = result.scalars().all()
    
    return tasks


@router.get("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    project_id: str,
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific task."""
    result = await session.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id
        )
    )
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task


@router.patch("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    project_id: str,
    task_id: str,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Update a task. Requires authentication and project ownership."""
    # First verify project ownership
    result_project = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result_project.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify tasks in this project"
        )
    
    # Now get the task
    result = await session.execute(
        select(Task).where(
            Task.id == task_id,
            Task.project_id == project_id
        )
    )
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.priority is not None:
        task.priority = task_data.priority.value
    if task_data.status is not None:
        task.status = task_data.status.value
    if task_data.dependencies is not None:
        task.dependencies = task_data.dependencies
    
    await session.commit()
    await session.refresh(task)
    
    # Invalidate project cache
    if CACHE_AVAILABLE:
        await invalidate_project_cache(project_id)
    
    return task


@router.get("/{project_id}/dashboard", response_model=ProjectDashboard)
async def get_project_dashboard(
    project_id: str,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """Get complete dashboard view of a project. Requires authentication and project access."""
    # Get project
    result = await session.execute(
        select(Project).where(Project.id == project_id)
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
            detail="Not authorized to access this project"
        )
    
    # Get tasks
    result = await session.execute(
        select(Task).where(Task.project_id == project_id)
    )
    tasks = result.scalars().all()
    
    # Get artifacts
    result = await session.execute(
        select(Artifact).where(Artifact.project_id == project_id)
    )
    artifacts = result.scalars().all()
    
    # Calculate stats
    active_runs = sum(1 for task in tasks if task.status == "running")
    completed_tasks = sum(1 for task in tasks if task.status == "completed")
    total_tasks = len(tasks)
    
    return ProjectDashboard(
        project=project,
        tasks=tasks,
        active_runs=active_runs,
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        artifacts=artifacts,
    )


# ============================================================================
# WORKFLOW ENDPOINTS (PRD Multi-Agent)
# ============================================================================

class WorkflowGenerateRequest(BaseModel):
    """Request to start workflow generation."""
    prompt: str


class WorkflowApproveRequest(BaseModel):
    """Request to approve specification and continue."""
    approved: bool = True
    specification: dict


class WorkflowRefineRequest(BaseModel):
    """Request to refine and regenerate."""
    refinement_notes: str


@router.post("/{project_id}/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_project(
    project_id: str,
    request: WorkflowGenerateRequest,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate project code using multi-agent workflow. Requires authentication and project ownership.
    
    PRD: User submits detailed prompt → Planner creates spec → Awaits approval
    
    Returns:
        Workflow status with specification awaiting approval
    """
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == project_id)
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
            detail="Not authorized to generate code for this project"
        )
    
    # Update project status
    project.status = "generating"
    await session.commit()
    
    # Execute workflow (will pause at approval gate)
    workflow_result = await workflow_pipeline.execute_workflow(
        project_id=project_id,
        user_prompt=request.prompt
    )
    
    return {
        "project_id": project_id,
        "workflow_id": workflow_result.get("workflow_id"),
        "status": workflow_result.get("status"),
        "stage": workflow_result.get("stage"),
        "specification": workflow_result.get("specification"),
        "message": workflow_result.get("message"),
        "validation_score": workflow_result.get("validation_score")
    }


@router.post("/{project_id}/approve")
async def approve_specification(
    project_id: str,
    request: WorkflowApproveRequest,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """
    Approve specification and continue workflow. Requires authentication and project ownership.
    
    PRD: User reviews spec → Approves → Coder + Tester run
    
    Returns:
        Complete workflow result with generated code
    """
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == project_id)
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
            detail="Not authorized to approve this project"
        )
    
    if not request.approved:
        project.status = "planning"
        await session.commit()
        return {
            "project_id": project_id,
            "status": "rejected",
            "message": "Specification rejected by user"
        }
    
    # Continue workflow with approved spec
    workflow_result = await workflow_pipeline.execute_workflow(
        project_id=project_id,
        user_prompt="",  # Not needed, using approved spec
        approved_spec=request.specification
    )
    
    # Update project status based on result
    if workflow_result.get("status") == "completed":
        project.status = "completed"
    elif workflow_result.get("status") == "failed":
        project.status = "failed"
    
    await session.commit()
    
    return {
        "project_id": project_id,
        "workflow_id": workflow_result.get("workflow_id"),
        "status": workflow_result.get("status"),
        "code_files": workflow_result.get("code_files"),
        "test_files": workflow_result.get("test_files"),
        "review": workflow_result.get("review"),
        "message": workflow_result.get("message")
    }


@router.post("/{project_id}/regenerate")
async def regenerate_project(
    project_id: str,
    request: WorkflowRefineRequest,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """
    Regenerate project with refinements. Requires authentication and project ownership.
    
    PRD: User provides refinement notes → Workflow re-runs with updates
    
    Returns:
        New workflow result
    """
    # Verify project exists
    result = await session.execute(
        select(Project).where(Project.id == project_id)
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
            detail="Not authorized to regenerate this project"
        )
    
    # Get previous artifacts to find original prompt
    # (In real implementation, store original prompt in project)
    # For now, use refinement notes as full prompt
    
    project.status = "generating"
    await session.commit()
    
    # Execute workflow with iteration
    workflow_result = await workflow_pipeline.execute_workflow(
        project_id=project_id,
        user_prompt=request.refinement_notes,
        iteration=2  # Increment based on stored iteration count
    )
    
    if workflow_result.get("status") == "completed":
        project.status = "completed"
    elif workflow_result.get("status") == "failed":
        project.status = "failed"
    
    await session.commit()
    
    return {
        "project_id": project_id,
        "workflow_id": workflow_result.get("workflow_id"),
        "status": workflow_result.get("status"),
        "iteration": workflow_result.get("iteration"),
        "message": workflow_result.get("message")
    }


@router.get("/{project_id}/specification")
async def get_specification(
    project_id: str,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """
    Get project specification (planner output). Requires authentication and project access.
    
    Returns:
        Specification created by planner agent
    """
    # Verify project ownership first
    result_project = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result_project.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    # Get most recent workflow stage for planner FOR THIS PROJECT
    from ..db.models import WorkflowStage, CrewRun
    
    # Join through CrewRun since WorkflowStage doesn't have project_id
    result = await session.execute(
        select(WorkflowStage)
        .join(CrewRun, WorkflowStage.crew_run_id == CrewRun.id)
        .join(Task, CrewRun.id == Task.crew_run_id)
        .where(
            Task.project_id == project_id,
            WorkflowStage.stage == "planner"
        )
        .order_by(WorkflowStage.started_at.desc())
        .limit(1)
    )
    stage = result.scalars().first()
    
    if not stage or not stage.output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No specification found"
        )
    
    return {
        "project_id": project_id,
        "specification": stage.output,
        "created_at": stage.created_at,
        "status": stage.status
    }


@router.get("/{project_id}/code")
async def get_generated_code(
    project_id: str,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """
    Get generated code files. Requires authentication and project access.
    
    Returns:
        All code and test files generated by workflow
    """
    # Verify project ownership
    result_project = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result_project.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check ownership
    if project.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    # Get artifacts for this project
    result = await session.execute(
        select(Artifact)
        .where(Artifact.project_id == project_id)
        .order_by(Artifact.created_at.desc())
    )
    artifacts = result.scalars().all()
    
    if not artifacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No code files found"
        )
    
    # Separate by type
    code_files = [
        {
            "id": str(art.id),
            "name": art.name,
            "content": art.content,
            "metadata": art.metadata,
            "created_at": art.created_at
        }
        for art in artifacts if art.type == "code"
    ]
    
    test_files = [
        {
            "id": str(art.id),
            "name": art.name,
            "content": art.content,
            "metadata": art.metadata,
            "created_at": art.created_at
        }
        for art in artifacts if art.type == "test"
    ]
    
    return {
        "project_id": project_id,
        "code_files": code_files,
        "test_files": test_files,
        "total_files": len(artifacts)
    }


@router.get("/{project_id}/status")
async def get_workflow_status(
    project_id: str,
    current_user: User = Depends(get_current_user_required),
    session: AsyncSession = Depends(get_session),
):
    """
    Get current workflow status. Requires authentication and project access.
    
    Returns:
        Current stage, status, and progress information
    """
    # Get project
    result = await session.execute(
        select(Project).where(Project.id == project_id)
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
            detail="Not authorized to access this project"
        )
    
    # Get workflow stages FOR THIS PROJECT (fix cross-project leakage)
    from ..db.models import WorkflowStage, CrewRun
    
    # Join through CrewRun and Task since WorkflowStage doesn't have project_id  
    result = await session.execute(
        select(WorkflowStage)
        .join(CrewRun, WorkflowStage.crew_run_id == CrewRun.id)
        .join(Task, CrewRun.id == Task.crew_run_id)
        .where(Task.project_id == project_id)
        .order_by(WorkflowStage.started_at.desc())
    )
    stages = result.scalars().all()
    
    # Build status response
    stages_status = [
        {
            "stage": stage.stage,
            "status": stage.status,
            "started_at": stage.started_at,
            "completed_at": stage.completed_at
        }
        for stage in stages
    ]
    
    return {
        "project_id": project_id,
        "project_status": project.status,
        "stages": stages_status
    }
