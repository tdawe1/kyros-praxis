"""Pydantic models for multi-agent orchestration API."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Enums
class ProjectStatus(str, Enum):
    """Project status values."""
    planning = "planning"
    executing = "executing"
    reviewing = "reviewing"
    completed = "completed"
    failed = "failed"


class TaskStatus(str, Enum):
    """Task status values."""
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    blocked = "blocked"
    cancelled = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels."""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class WorkflowStageType(str, Enum):
    """Workflow pipeline stages."""
    orchestrator = "orchestrator"
    implementer = "implementer"
    critic = "critic"


class CriticStatus(str, Enum):
    """Critic feedback status."""
    approved = "approved"
    changes_requested = "changes_requested"
    rejected = "rejected"


class ArtifactType(str, Enum):
    """Artifact types."""
    file = "file"
    snippet = "snippet"
    config = "config"
    documentation = "documentation"


# Project models
class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    """Response model for project."""
    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Task models
class TaskCreate(BaseModel):
    """Request model for creating a task."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.P1
    dependencies: Optional[List[str]] = None  # List of task IDs


class TaskUpdate(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    dependencies: Optional[List[str]] = None


class TaskResponse(BaseModel):
    """Response model for task."""
    id: str
    project_id: str
    title: str
    description: Optional[str]
    priority: TaskPriority
    status: TaskStatus
    crew_run_id: Optional[str]
    dependencies: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Batch run models
class BatchRunCreate(BaseModel):
    """Request model for creating batch runs."""
    project_id: str
    tasks: List[TaskCreate]
    crew_id: str = "spec_to_tasks"


class BatchRunResponse(BaseModel):
    """Response model for batch run."""
    batch_id: str
    project_id: str
    tasks: List[TaskResponse]
    crew_runs: List[Dict[str, str]]  # [{"task_id": "...", "run_id": "..."}]


# Shared memory models
class MemorySet(BaseModel):
    """Request model for setting shared memory."""
    project_id: str
    key: str = Field(..., min_length=1, max_length=255)
    value: Dict[str, Any]
    ttl: Optional[int] = None  # Time to live in seconds


class MemoryGet(BaseModel):
    """Request model for getting shared memory."""
    project_id: str
    key: str


class MemoryResponse(BaseModel):
    """Response model for shared memory."""
    id: str
    project_id: str
    key: str
    value: Dict[str, Any]
    created_by: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Memory event models
class MemoryEventPublish(BaseModel):
    """Request model for publishing memory event."""
    project_id: str
    event_type: str = Field(..., min_length=1, max_length=50)
    payload: Dict[str, Any]


class MemoryEventResponse(BaseModel):
    """Response model for memory event."""
    id: int
    project_id: str
    event_type: str
    payload: Dict[str, Any]
    published_at: datetime
    
    class Config:
        from_attributes = True


# Workflow models
class WorkflowStageResponse(BaseModel):
    """Response model for workflow stage."""
    id: str
    crew_run_id: str
    stage: WorkflowStageType
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    output: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class WorkflowStatusResponse(BaseModel):
    """Response model for complete workflow status."""
    crew_run_id: str
    current_stage: WorkflowStageType
    stages: List[WorkflowStageResponse]
    overall_status: str


# Critic models
class CriticFeedbackSubmit(BaseModel):
    """Request model for submitting critic feedback."""
    crew_run_id: str
    status: CriticStatus
    feedback: Optional[str] = None
    iteration: int = 1


class CriticFeedbackResponse(BaseModel):
    """Response model for critic feedback."""
    id: str
    crew_run_id: str
    iteration: int
    status: CriticStatus
    feedback: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Artifact models
class ArtifactCreate(BaseModel):
    """Request model for creating artifact."""
    project_id: str
    task_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    type: ArtifactType
    content: str
    meta: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class ArtifactUpdate(BaseModel):
    """Request model for updating artifact."""
    integrated: Optional[bool] = None
    content: Optional[str] = None
    meta: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class ArtifactResponse(BaseModel):
    """Response model for artifact."""
    id: str
    project_id: str
    task_id: Optional[str]
    name: str
    type: ArtifactType
    content: str
    meta: Optional[Dict[str, Any]] = Field(None, alias="metadata")
    integrated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


# Dashboard models
class ProjectDashboard(BaseModel):
    """Dashboard view of project with all details."""
    project: ProjectResponse
    tasks: List[TaskResponse]
    active_runs: int
    completed_tasks: int
    total_tasks: int
    artifacts: List[ArtifactResponse]


class AgentStatus(BaseModel):
    """Status of an individual agent/run."""
    run_id: str
    task_id: str
    task_title: str
    status: str
    current_stage: Optional[WorkflowStageType]
    progress: int  # 0-100
    dependencies_met: bool
    started_at: Optional[datetime]


class MultiAgentDashboard(BaseModel):
    """Complete dashboard for multi-agent system."""
    project: ProjectResponse
    agents: List[AgentStatus]
    shared_memory_keys: List[str]
    recent_events: List[MemoryEventResponse]
    pending_artifacts: int
