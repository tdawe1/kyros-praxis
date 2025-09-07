from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

class AgentContext(BaseModel):
    task: Dict[str, Any]
    tools: List[Dict[str, Any]]
    memory: Dict[str, Any]
    telemetry: Dict[str, Any]
    tenant_id: Optional[str] = None

class AgentBase(ABC):
    """Base class for all agents in the Kyros system."""
    
    @abstractmethod
    def capabilities(self) -> List[str]:
        """Return list of capabilities this agent supports."""
        pass
    
    @abstractmethod
    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        """Execute the agent with the given context."""
        pass
    
    def get_name(self) -> str:
        """Get the agent's name. Defaults to class name."""
        return self.__class__.__name__