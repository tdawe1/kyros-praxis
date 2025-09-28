"""
Agentic Workflow API Endpoints

This module provides FastAPI endpoints for managing sophisticated agentic workflows
including ReAct loops, self-reflection, memory management, and multi-agent coordination.
These endpoints transform the basic orchestrator into an advanced agent coordination system.

The API supports:
- Agent definition and instance management
- ReAct loop execution and monitoring
- Memory storage and retrieval
- Self-reflection and critique
- Multi-agent coordination
- Performance analytics and insights
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

try:
    from database import get_db_session
    from auth import get_current_user
    from models import User
except ImportError:  # pragma: no cover
    from services.orchestrator.database import get_db_session  # type: ignore
    from services.orchestrator.auth import get_current_user  # type: ignore
    from services.orchestrator.models import User  # type: ignore

# Import agentic models and systems
from agentic.models import (
    AgentDefinition, AgentInstance, AgentRun, AgentMemory, TaskDelegation,
    AgentType, AgentStatus, RunStatus
)
from agentic.react_engine import ReActEngine, ReActConfig, AgentCoordinator
from agentic.memory_manager import MemoryManager, MemoryQuery, MemoryEntry, MemoryType, MemoryImportance
from agentic.reflection_system import ReflectionSystem, CriticGenerator, ReflectionScope, CritiqueLevel, ImprovementCategory

try:
    from app.core.logging import log_orchestrator_event
except ImportError:  # pragma: no cover
    # Fallback for environments where logging is not available
    def log_orchestrator_event(**kwargs):
        pass

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class AgentDefinitionCreate(BaseModel):
    """Model for creating agent definitions."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    agent_type: AgentType
    capabilities: Optional[List[str]] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    reasoning_prompt: Optional[str] = None
    action_prompt: Optional[str] = None
    observation_prompt: Optional[str] = None
    reflection_prompt: Optional[str] = None
    mcp_servers: Optional[List[str]] = Field(default_factory=list)
    tool_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    llm_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    max_iterations: int = Field(default=10, ge=1, le=100)
    reflection_frequency: int = Field(default=3, ge=1)
    delegation_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class AgentInstanceCreate(BaseModel):
    """Model for creating agent instances."""
    definition_id: str
    name: str = Field(..., min_length=1, max_length=255)
    config_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)
    max_concurrent_runs: int = Field(default=1, ge=1, le=10)
    priority: int = Field(default=5, ge=1, le=10)


class AgentRunCreate(BaseModel):
    """Model for starting agent runs."""
    agent_instance_id: str
    goal: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    config_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MemoryCreateRequest(BaseModel):
    """Model for creating agent memories."""
    content: str = Field(..., min_length=1)
    memory_type: MemoryType
    category: Optional[str] = None
    importance: MemoryImportance = Field(default=MemoryImportance.MEDIUM)
    tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    related_memory_ids: List[str] = Field(default_factory=list)
    source_run_id: Optional[str] = None


class MultiAgentTaskRequest(BaseModel):
    """Model for multi-agent task coordination."""
    task_description: str = Field(..., min_length=1)
    required_capabilities: List[str] = Field(..., min_items=1)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    coordination_strategy: str = Field(default="parallel_execution")


# Legacy Agent model for backward compatibility
class Agent(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str = Field("active", pattern="^(active|paused|error|pending)$")
    model: Optional[str] = None
    owner: Optional[str] = None
    capabilities: List[str] = []
    successRate: Optional[float] = None
    lastRunAt: Optional[datetime] = None


class AgentListResponse(BaseModel):
    agents: List[Agent]
    total: int
    page: int
    pageSize: int


# Agent Definition Endpoints

@router.post("/definitions", response_model=Dict[str, Any])
async def create_agent_definition(
    definition: AgentDefinitionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new agent definition."""
    try:
        # Check if name already exists
        existing_result = await db.execute(
            select(AgentDefinition).where(AgentDefinition.name == definition.name)
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Agent definition name already exists")
            
        # Create agent definition
        agent_def = AgentDefinition(
            name=definition.name,
            description=definition.description,
            agent_type=definition.agent_type.value,
            capabilities=definition.capabilities,
            system_prompt=definition.system_prompt,
            reasoning_prompt=definition.reasoning_prompt,
            action_prompt=definition.action_prompt,
            observation_prompt=definition.observation_prompt,
            reflection_prompt=definition.reflection_prompt,
            mcp_servers=definition.mcp_servers,
            tool_config=definition.tool_config,
            llm_config=definition.llm_config,
            max_iterations=definition.max_iterations,
            reflection_frequency=definition.reflection_frequency,
            delegation_threshold=definition.delegation_threshold,
            created_by=current_user.id
        )
        
        db.add(agent_def)
        await db.commit()
        await db.refresh(agent_def)
        
        log_orchestrator_event(
            event="agent_definition_created",
            agent_definition_id=agent_def.id,
            name=agent_def.name,
            agent_type=agent_def.agent_type,
            created_by=current_user.id
        )
        
        return {
            "id": agent_def.id,
            "name": agent_def.name,
            "agent_type": agent_def.agent_type,
            "capabilities": agent_def.capabilities,
            "created_at": agent_def.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating agent definition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/definitions", response_model=List[Dict[str, Any]])
async def list_agent_definitions(
    agent_type: Optional[AgentType] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """List agent definitions with optional filtering."""
    try:
        query = select(AgentDefinition).order_by(desc(AgentDefinition.created_at))
        
        if agent_type:
            query = query.where(AgentDefinition.agent_type == agent_type.value)
            
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        definitions = result.scalars().all()
        
        return [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "agent_type": d.agent_type,
                "capabilities": d.capabilities or [],
                "max_iterations": d.max_iterations,
                "reflection_frequency": d.reflection_frequency,
                "created_at": d.created_at.isoformat(),
                "updated_at": d.updated_at.isoformat() if d.updated_at else None
            }
            for d in definitions
        ]
        
    except Exception as e:
        logger.error(f"Error listing agent definitions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Agent Instance Endpoints

@router.post("/instances", response_model=Dict[str, Any])
async def create_agent_instance(
    instance: AgentInstanceCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new agent instance."""
    try:
        # Verify agent definition exists
        def_result = await db.execute(
            select(AgentDefinition).where(AgentDefinition.id == instance.definition_id)
        )
        agent_def = def_result.scalar_one_or_none()
        if not agent_def:
            raise HTTPException(status_code=404, detail="Agent definition not found")
            
        # Create agent instance
        agent_instance = AgentInstance(
            definition_id=instance.definition_id,
            name=instance.name,
            status=AgentStatus.INACTIVE.value,
            config_overrides=instance.config_overrides,
            max_concurrent_runs=instance.max_concurrent_runs,
            priority=instance.priority,
            created_by=current_user.id
        )
        
        db.add(agent_instance)
        await db.commit()
        await db.refresh(agent_instance)
        
        log_orchestrator_event(
            event="agent_instance_created",
            agent_instance_id=agent_instance.id,
            definition_id=instance.definition_id,
            name=agent_instance.name,
            created_by=current_user.id
        )
        
        return {
            "id": agent_instance.id,
            "name": agent_instance.name,
            "definition_id": agent_instance.definition_id,
            "status": agent_instance.status,
            "priority": agent_instance.priority,
            "created_at": agent_instance.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating agent instance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances", response_model=List[Dict[str, Any]])
async def list_agent_instances(
    status: Optional[AgentStatus] = Query(None),
    definition_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """List agent instances with optional filtering."""
    try:
        query = select(AgentInstance).options(
            selectinload(AgentInstance.definition)
        ).order_by(desc(AgentInstance.created_at))
        
        if status:
            query = query.where(AgentInstance.status == status.value)
        if definition_id:
            query = query.where(AgentInstance.definition_id == definition_id)
            
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        instances = result.scalars().all()
        
        return [
            {
                "id": i.id,
                "name": i.name,
                "definition_id": i.definition_id,
                "definition_name": i.definition.name if i.definition else None,
                "status": i.status,
                "priority": i.priority,
                "max_concurrent_runs": i.max_concurrent_runs,
                "error_count": i.error_count,
                "success_count": i.success_count,
                "last_activity": i.last_activity.isoformat() if i.last_activity else None,
                "created_at": i.created_at.isoformat()
            }
            for i in instances
        ]
        
    except Exception as e:
        logger.error(f"Error listing agent instances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Agent Run Endpoints

@router.post("/runs", response_model=Dict[str, Any])
async def start_agent_run(
    run_request: AgentRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Start a new agent run with ReAct loop execution."""
    try:
        # Initialize ReAct engine
        react_engine = ReActEngine(db)
        
        # Start the agent run
        run_id = await react_engine.start_agent_run(
            agent_instance_id=run_request.agent_instance_id,
            goal=run_request.goal,
            context=run_request.context,
            config_overrides=run_request.config_overrides
        )
        
        log_orchestrator_event(
            event="agent_run_started",
            run_id=run_id,
            agent_instance_id=run_request.agent_instance_id,
            goal=run_request.goal[:100],
            started_by=current_user.id
        )
        
        return {
            "run_id": run_id,
            "status": "started",
            "goal": run_request.goal,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting agent run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}")
async def get_agent_run_status(
    run_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get detailed status of an agent run."""
    try:
        # Get run details
        result = await db.execute(
            select(AgentRun).options(
                selectinload(AgentRun.agent_instance),
                selectinload(AgentRun.thoughts),
                selectinload(AgentRun.actions),
                selectinload(AgentRun.observations),
                selectinload(AgentRun.reflections)
            ).where(AgentRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(status_code=404, detail="Agent run not found")
            
        return {
            "id": run.id,
            "agent_instance_id": run.agent_instance_id,
            "agent_instance_name": run.agent_instance.name if run.agent_instance else None,
            "goal": run.goal,
            "status": run.status,
            "current_iteration": run.current_iteration,
            "max_iterations": run.max_iterations,
            "current_phase": run.current_phase,
            "success": run.success,
            "error_message": run.error_message,
            "final_result": run.final_result,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "total_reasoning_time": run.total_reasoning_time,
            "total_action_time": run.total_action_time,
            "total_observation_time": run.total_observation_time,
            "thoughts_count": len(run.thoughts) if run.thoughts else 0,
            "actions_count": len(run.actions) if run.actions else 0,
            "observations_count": len(run.observations) if run.observations else 0,
            "reflections_count": len(run.reflections) if run.reflections else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting agent run status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Multi-Agent Coordination Endpoints

@router.post("/coordinate")
async def coordinate_multi_agent_task(
    task_request: MultiAgentTaskRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Coordinate a task across multiple agents."""
    try:
        coordinator = AgentCoordinator(db)
        
        coordination_run_id = await coordinator.coordinate_multi_agent_task(
            task_description=task_request.task_description,
            required_capabilities=task_request.required_capabilities,
            context=task_request.context
        )
        
        return {
            "coordination_run_id": coordination_run_id,
            "task_description": task_request.task_description,
            "required_capabilities": task_request.required_capabilities,
            "status": "started"
        }
        
    except Exception as e:
        logger.error(f"Error coordinating multi-agent task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Legacy endpoints for backward compatibility

@router.get("/agents", response_model=AgentListResponse, summary="List agents (legacy)")
async def list_agents(
    page: int = 1,
    pageSize: int = 20,
    status: Optional[str] = None,
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List agents with legacy format for backward compatibility."""
    try:
        # Map to agent instances for now
        query = select(AgentInstance).options(
            selectinload(AgentInstance.definition)
        ).order_by(desc(AgentInstance.created_at))
        
        # Apply status filter if provided
        if status and status in ["active", "paused", "error", "pending"]:
            status_mapping = {
                "active": AgentStatus.ACTIVE.value,
                "paused": AgentStatus.PAUSED.value,
                "error": AgentStatus.ERROR.value,
                "pending": AgentStatus.INACTIVE.value
            }
            query = query.where(AgentInstance.status == status_mapping.get(status))
            
        # Apply pagination
        offset = (page - 1) * pageSize
        query = query.offset(offset).limit(pageSize)
        
        result = await db.execute(query)
        instances = result.scalars().all()
        
        # Get total count
        count_result = await db.execute(select(func.count(AgentInstance.id)))
        total = count_result.scalar()
        
        # Convert to legacy format
        agents = []
        for instance in instances:
            # Map status to legacy format
            legacy_status = "active"
            if instance.status == AgentStatus.PAUSED.value:
                legacy_status = "paused"
            elif instance.status == AgentStatus.ERROR.value:
                legacy_status = "error"
            elif instance.status == AgentStatus.INACTIVE.value:
                legacy_status = "pending"
                
            # Calculate success rate
            total_runs = instance.success_count + instance.error_count
            success_rate = instance.success_count / total_runs if total_runs > 0 else None
            
            agents.append(Agent(
                id=instance.id,
                name=instance.name,
                description=instance.definition.description if instance.definition else None,
                status=legacy_status,
                model=instance.definition.llm_config.get("model_name") if instance.definition and instance.definition.llm_config else None,
                owner=instance.created_by or "system",
                capabilities=instance.definition.capabilities if instance.definition else [],
                successRate=success_rate,
                lastRunAt=instance.last_activity
            ))
        
        return AgentListResponse(
            agents=agents,
            total=total,
            page=page,
            pageSize=pageSize
        )
        
    except Exception as e:
        logger.error(f"Error listing agents (legacy): {e}", exc_info=True)
        # Return empty list on error for backward compatibility
        return AgentListResponse(agents=[], total=0, page=page, pageSize=pageSize)

