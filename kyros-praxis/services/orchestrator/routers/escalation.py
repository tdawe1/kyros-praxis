"""
Escalation System API Integration Module

This module provides RESTful API endpoints for the escalation system, integrating
all components (trigger detection, context analysis, workflow automation,
and validation) into a cohesive service. It enables intelligent decision-making
on when to escalate tasks to more capable AI models based on complexity,
risk factors, and business impact.

The escalation system evaluates tasks based on multiple factors:
- Task complexity and technical challenges
- Business impact assessment
- Risk level analysis
- Cost impact estimation
- Historical performance data

ENDPOINTS:
1. POST /v1/escalation/submit - Submit a new escalation request
2. GET /v1/escalation/status/{workflow_id} - Get the status of an escalation workflow
3. GET /v1/escalation/statistics - Get escalation system statistics
4. POST /v1/escalation/validate - Validate an escalation trigger
5. POST /v1/escalation/analyze - Analyze task context for escalation decision
6. POST /v1/escalation/detect - Detect escalation triggers for a task
7. GET /v1/escalation/health - Health check for the escalation system
8. DELETE /v1/escalation/workflow/{workflow_id} - Cancel a running escalation workflow
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .escalation_triggers import (
    should_escalate_task
)
from .context_analysis import (
    analyze_task_context
)
from .escalation_workflow import (
    submit_escalation,
    get_escalation_status,
    get_escalation_stats
)
from .trigger_validation import (
    validate_escalation_trigger,
    get_validation_statistics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/escalation", tags=["escalation"])


# Request/Response Models
class EscalationRequest(BaseModel):
    task_description: str = Field(..., description="Description of the task to perform")
    files_to_modify: List[str] = Field(..., description="List of files that will be modified")
    current_files: Optional[List[str]] = Field(None, description="Current workspace files")
    task_type: str = Field(default="implementation", description="Type of task")
    requester: str = Field(default="system", description="Who requested the escalation")
    priority: str = Field(default="normal", description="Priority level")
    timeout_seconds: Optional[int] = Field(None, description="Custom timeout in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class EscalationResponse(BaseModel):
    workflow_id: str
    request_id: str
    status: str
    should_escalate: bool
    confidence: float
    recommended_model: str
    fallback_model: str
    message: str


class ValidationRequest(BaseModel):
    trigger_data: Dict[str, Any] = Field(..., description="Trigger data to validate")
    context: Dict[str, Any] = Field(..., description="Context information")
    assessment_data: Optional[Dict[str, Any]] = Field(None, description="Assessment data")
    context_analysis_data: Optional[Dict[str, Any]] = Field(None, description="Context analysis data")


class ValidationResponse(BaseModel):
    validation_id: str
    trigger_type: str
    overall_result: str
    overall_confidence: float
    checks_count: int
    recommendation: str


class AnalysisRequest(BaseModel):
    task_description: str = Field(..., description="Description of the task")
    files_to_modify: List[str] = Field(..., description="Files to be modified")
    file_contents: Optional[Dict[str, str]] = Field(None, description="File contents for analysis")
    task_type: str = Field(default="implementation", description="Type of task")


class AnalysisResponse(BaseModel):
    complexity_level: str
    business_impact: str
    risk_level: str
    overall_recommendation: str
    confidence_score: float
    key_factors: List[str]


# API Endpoints
@router.post("/submit", response_model=EscalationResponse)
async def submit_escalation_request(request: EscalationRequest):
    """
    Submit a new escalation request
    
    This endpoint initiates the escalation process by analyzing the task
    and determining if escalation to Claude 4.1 Opus is warranted. The escalation
    decision is based on multiple factors including task complexity, business impact,
    risk assessment, and historical performance data.
    
    The endpoint performs the following steps:
    1. Validates the escalation request parameters
    2. Analyzes the task context and complexity
    3. Determines if escalation is warranted based on predefined criteria
    4. Creates a new escalation workflow if escalation is recommended
    5. Returns the escalation decision and workflow information
    
    Args:
        request (EscalationRequest): The escalation request containing task details
            - task_description (str): Description of the task to perform
            - files_to_modify (List[str]): List of files that will be modified
            - current_files (Optional[List[str]]): Current workspace files
            - task_type (str): Type of task (default: "implementation")
            - requester (str): Who requested the escalation (default: "system")
            - priority (str): Priority level (default: "normal")
            - timeout_seconds (Optional[int]): Custom timeout in seconds
            - metadata (Optional[Dict[str, Any]]): Additional metadata
            
    Returns:
        EscalationResponse: The escalation decision and workflow information
            - workflow_id (str): Unique identifier for the escalation workflow
            - request_id (str): Unique identifier for the escalation request
            - status (str): Current status of the escalation workflow
            - should_escalate (bool): Whether the task should be escalated
            - confidence (float): Confidence level in the escalation decision (0.0-1.0)
            - recommended_model (str): Recommended AI model for the task
            - fallback_model (str): Fallback AI model if primary is unavailable
            - message (str): Human-readable message about the escalation decision
            
    Raises:
        HTTPException: If there's an error processing the escalation request
            - 400: Invalid request parameters
            - 500: Internal server error during escalation processing
    """
    try:
        # Submit escalation request
        workflow = await submit_escalation(
            task_description=request.task_description,
            files_to_modify=request.files_to_modify,
            current_files=request.current_files,
            task_type=request.task_type,
            requester=request.requester,
            priority=request.priority,
            timeout_seconds=request.timeout_seconds,
            metadata=request.metadata
        )
        
        return EscalationResponse(
            workflow_id=workflow.workflow_id,
            request_id=workflow.request.request_id,
            status=workflow.state.value,
            should_escalate=workflow.assessment.should_escalate if workflow.assessment else False,
            confidence=workflow.assessment.confidence if workflow.assessment else 0.0,
            recommended_model=workflow.assessment.recommended_model if workflow.assessment else "glm-4.5",
            fallback_model=workflow.assessment.fallback_model if workflow.assessment else "glm-4.5",
            message="Escalation request submitted successfully"
        )
    
    except Exception as e:
        logger.error(f"Error submitting escalation request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit escalation request: {str(e)}")


@router.get("/status/{workflow_id}")
async def get_escalation_workflow_status(workflow_id: str):
    """
    Get the status of an escalation workflow
    
    Returns the current state, progress, and results of an escalation workflow.
    This endpoint provides detailed information about the escalation process,
    including the workflow state, execution progress, and final outcome.
    
    Args:
        workflow_id (str): The unique identifier of the escalation workflow
        
    Returns:
        dict: The workflow status information
            - workflow_id (str): Unique identifier for the escalation workflow
            - state (str): Current state of the workflow (pending, analyzing, escalating, completed, failed)
            - current_step (int): Current step in the workflow process
            - total_steps (int): Total number of steps in the workflow
            - steps_completed (int): Number of steps completed
            - should_escalate (bool): Whether the task should be escalated
            - recommended_model (str): Recommended AI model for the task
            - outcome (str): Final outcome of the workflow (success, failure, cancelled)
            - error_message (str): Error message if the workflow failed
            - started_at (str): ISO format timestamp when the workflow started
            - completed_at (str): ISO format timestamp when the workflow completed
            - execution_log (List[str]): Last 5 log entries from the workflow execution
            
    Raises:
        HTTPException: If there's an error retrieving the workflow status
            - 404: Workflow not found
            - 500: Internal server error during status retrieval
    """
    try:
        workflow = get_escalation_status(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "workflow_id": workflow.workflow_id,
            "state": workflow.state.value,
            "current_step": workflow.current_step,
            "total_steps": workflow.total_steps,
            "steps_completed": workflow.steps_completed,
            "should_escalate": workflow.assessment.should_escalate if workflow.assessment else False,
            "recommended_model": workflow.assessment.recommended_model if workflow.assessment else "glm-4.5",
            "outcome": workflow.outcome.value if workflow.outcome else None,
            "error_message": workflow.error_message,
            "started_at": workflow.started_at.isoformat(),
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "execution_log": workflow.execution_log[-5:]  # Last 5 log entries
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")


@router.get("/statistics")
async def get_escalation_system_statistics():
    """
    Get escalation system statistics
    
    Returns comprehensive statistics about the escalation system performance.
    """
    try:
        escalation_stats = get_escalation_stats()
        validation_stats = get_validation_statistics()
        
        return {
            "escalation": escalation_stats,
            "validation": validation_stats,
            "system_status": "operational",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting system statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system statistics: {str(e)}")


@router.post("/validate", response_model=ValidationResponse)
async def validate_escalation_trigger(request: ValidationRequest):
    """
    Validate an escalation trigger
    
    This endpoint performs comprehensive validation of escalation triggers
    against business rules, technical constraints, and historical data.
    """
    try:
        # For now, we'll create a simple trigger from the request data
        # In a real implementation, this would be more sophisticated
        from .escalation_triggers import EscalationTrigger, EscalationReason
        
        # Create trigger (simplified for demo)
        trigger = EscalationTrigger(
            reason=EscalationReason.CRITICAL_SECURITY,  # Default
            priority=request.trigger_data.get("priority", "medium"),
            description=request.trigger_data.get("description", "Unknown trigger"),
            evidence=request.trigger_data.get("evidence", []),
            confidence=request.trigger_data.get("confidence", 0.5)
        )
        
        # Validate trigger
        validation_report = validate_escalation_trigger(
            trigger=trigger,
            context=request.context,
            assessment_data=request.assessment_data,
            context_analysis_data=request.context_analysis_data
        )
        
        return ValidationResponse(
            validation_id=validation_report.trigger_id,
            trigger_type=validation_report.trigger_type.value,
            overall_result=validation_report.overall_result.value,
            overall_confidence=validation_report.overall_confidence,
            checks_count=len(validation_report.checks),
            recommendation=validation_report.overall_result.value
        )
    
    except Exception as e:
        logger.error(f"Error validating trigger: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate trigger: {str(e)}")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_task_context(request: AnalysisRequest):
    """
    Analyze task context for escalation decision
    
    This endpoint provides deep analysis of task context, complexity,
    business impact, and risk factors to inform escalation decisions.
    """
    try:
        # Perform context analysis
        context_analysis = analyze_task_context(
            task_description=request.task_description,
            files_to_modify=request.files_to_modify,
            file_contents=request.file_contents,
            task_type=request.task_type
        )
        
        return AnalysisResponse(
            complexity_level=context_analysis.overall_complexity.value,
            business_impact=context_analysis.business_impact.overall_impact.value,
            risk_level=context_analysis.risk_assessment.overall_risk.value,
            overall_recommendation=context_analysis.escalation_recommendation,
            confidence_score=context_analysis.confidence_score,
            key_factors=context_analysis.key_factors
        )
    
    except Exception as e:
        logger.error(f"Error analyzing task context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze task context: {str(e)}")


@router.post("/detect")
async def detect_escalation_triggers(request: EscalationRequest):
    """
    Detect escalation triggers for a task
    
    This endpoint analyzes a task to identify triggers that might warrant
    escalation to Claude 4.1 Opus.
    """
    try:
        # Perform trigger detection
        assessment = should_escalate_task(
            task_description=request.task_description,
            files_to_modify=request.files_to_modify,
            current_files=request.current_files,
            task_type=request.task_type
        )
        
        return {
            "should_escalate": assessment.should_escalate,
            "confidence": assessment.confidence,
            "recommended_model": assessment.recommended_model,
            "fallback_model": assessment.fallback_model,
            "primary_reason": assessment.primary_reason,
            "triggers": [
                {
                    "reason": trigger.reason.value,
                    "priority": trigger.priority.value,
                    "description": trigger.description,
                    "confidence": trigger.confidence
                }
                for trigger in assessment.triggers
            ],
            "cost_impact_estimate": assessment.cost_impact_estimate,
            "risk_assessment": assessment.risk_assessment
        }
    
    except Exception as e:
        logger.error(f"Error detecting escalation triggers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to detect escalation triggers: {str(e)}")


@router.get("/health")
async def escalation_health_check():
    """
    Health check for the escalation system
    
    Returns the health status of all escalation system components.
    """
    try:
        # Check if escalation engine is available
        try:
            stats = get_escalation_stats()
            engine_status = "healthy"
        except Exception:
            engine_status = "unhealthy"
        
        # Check if validator is available
        try:
            val_stats = get_validation_statistics()
            validator_status = "healthy"
        except Exception:
            validator_status = "unhealthy"
        
        # Determine overall health
        overall_status = "healthy" if engine_status == "healthy" and validator_status == "healthy" else "degraded"
        
        return {
            "status": overall_status,
            "components": {
                "escalation_engine": engine_status,
                "trigger_validator": validator_status,
                "context_analyzer": "healthy",  # Stateless, always healthy
                "escalation_detector": "healthy"  # Stateless, always healthy
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error performing health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to perform health check: {str(e)}")


@router.delete("/workflow/{workflow_id}")
async def cancel_escalation_workflow(workflow_id: str):
    """
    Cancel a running escalation workflow
    
    This endpoint cancels a currently running escalation workflow.
    """
    try:
        engine = get_escalation_engine()
        success = engine.cancel_workflow(workflow_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found or already completed")
        
        return {
            "message": f"Workflow {workflow_id} cancelled successfully",
            "workflow_id": workflow_id,
            "cancelled_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {str(e)}")