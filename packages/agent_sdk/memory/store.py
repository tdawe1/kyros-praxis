from abc import ABC, abstractmethod
from typing import List, Dict, Any
class AgentMemoryStore(ABC):
    @abstractmethod
    async def store_interaction(self, agent_id: str, task_id: str, context: Dict[str,Any], result: Dict[str,Any]): ...
    @abstractmethod
    async def history(self, task_id: str, limit: int=100) -> List[Dict[str,Any]]: ...