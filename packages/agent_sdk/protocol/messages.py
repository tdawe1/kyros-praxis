from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Artifact(BaseModel):
    """Represents a piece of work or output from an agent."""

    kind: str = Field(
        ..., description="Type of artifact (e.g., 'code', 'document', 'data')"
    )
    ref: str = Field(..., description="Reference or identifier for the artifact")
    summary: str = Field(..., description="Brief summary of the artifact")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class AgentMessage(BaseModel):
    """Message from an agent containing intent, rationale, and artifacts."""

    intent: str = Field(..., description="What the agent intends to do")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence level (0-1)"
    )
    rationale_summary: str = Field(
        ..., description="Summary of reasoning (no raw chain-of-thought)"
    )
    artifacts: List[Artifact] = Field(
        default_factory=list, description="Artifacts produced"
    )
    next_actions: List[str] = Field(
        default_factory=list, description="Planned next actions"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When message was created"
    )
    agent_id: Optional[str] = Field(
        None, description="ID of the agent that created this message"
    )
    task_id: Optional[str] = Field(
        None, description="ID of the task this message relates to"
    )
