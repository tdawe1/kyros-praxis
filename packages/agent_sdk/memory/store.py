from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class InteractionRecord(BaseModel):
    """Record of an agent interaction."""

    agent_id: str
    task_id: str
    context: Dict[str, Any]
    result: Dict[str, Any]
    timestamp: datetime
    interaction_id: Optional[str] = None


class AgentMemoryStore(ABC):
    """Abstract base class for agent memory storage."""

    @abstractmethod
    async def store_interaction(
        self,
        agent_id: str,
        task_id: str,
        context: Dict[str, Any],
        result: Dict[str, Any],
    ) -> None:
        """Store an agent interaction."""
        pass

    @abstractmethod
    async def history(self, task_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get interaction history for a task."""
        pass
