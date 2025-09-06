from pydantic import BaseModel
from typing import Any, Dict, List
class ToolExample(BaseModel):
    name: str; input: Dict[str, Any]; output: Dict[str, Any]
class ToolSchema(BaseModel):
    name: str; description: str; parameters: Dict[str, Any]; returns: Dict[str, Any]; examples: List[ToolExample] = []
class ToolRegistry:
    def __init__(self): self._tools: dict[str, ToolSchema] = {}
    def register(self, tool: ToolSchema): self._tools[tool.name] = tool
    def get(self, name: str) -> ToolSchema|None: return self._tools.get(name)
    def discover(self, capabilities: List[str]) -> List[ToolSchema]: return list(self._tools.values())