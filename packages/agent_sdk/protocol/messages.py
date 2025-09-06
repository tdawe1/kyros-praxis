from pydantic import BaseModel
from typing import List
class Artifact(BaseModel):
    kind: str; ref: str; summary: str
class AgentMessage(BaseModel):
    intent: str
    confidence: float|None = None
    rationale_summary: str
    artifacts: List[Artifact] = []
    next_actions: List[str] = []