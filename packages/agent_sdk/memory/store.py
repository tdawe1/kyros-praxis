from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
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
    async def store_interaction(self, agent_id: str, task_id: str, context: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Store an agent interaction and return interaction ID."""
        pass
    
    @abstractmethod
    async def get_interaction(self, interaction_id: str) -> Optional[InteractionRecord]:
        """Get a specific interaction by ID."""
        pass
    
    @abstractmethod
    async def history(self, task_id: str, limit: int = 100) -> List[InteractionRecord]:
        """Get interaction history for a task."""
        pass
    
    @abstractmethod
    async def search_interactions(self, agent_id: Optional[str] = None, task_id: Optional[str] = None, 
                                since: Optional[datetime] = None, limit: int = 100) -> List[InteractionRecord]:
        """Search interactions with optional filters."""
        pass
    
    @abstractmethod
    async def delete_interaction(self, interaction_id: str) -> bool:
        """Delete an interaction by ID."""
        pass