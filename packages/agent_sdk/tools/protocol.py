from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolExample(BaseModel):
    """Example of tool usage with input and expected output."""

    name: str = Field(..., description="Name of the tool")
    input: Dict[str, Any] = Field(..., description="Example input parameters")
    output: Dict[str, Any] = Field(..., description="Example output")


class ToolSchema(BaseModel):
    """Schema definition for a tool."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(..., description="JSON schema for parameters")
    returns: Dict[str, Any] = Field(..., description="JSON schema for return value")
    examples: List[ToolExample] = Field(
        default_factory=list, description="Usage examples"
    )
    capabilities: List[str] = Field(
        default_factory=list, description="Required capabilities"
    )


class ToolExecutor(ABC):
    """Abstract base class for tool execution."""

    @abstractmethod
    async def execute(self, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        pass


class ToolRegistry:
    """Registry for managing tools and their execution."""

    def __init__(self):
        self._tools: Dict[str, ToolSchema] = {}
        self._executors: Dict[str, ToolExecutor] = {}

    def register(self, tool: ToolSchema, executor: Optional[ToolExecutor] = None):
        """Register a tool schema and optionally its executor."""
        self._tools[tool.name] = tool
        if executor:
            self._executors[tool.name] = executor

    def get(self, name: str) -> Optional[ToolSchema]:
        """Get tool schema by name."""
        return self._tools.get(name)

    def get_executor(self, name: str) -> Optional[ToolExecutor]:
        """Get tool executor by name."""
        return self._executors.get(name)

    def discover(self, capabilities: List[str]) -> List[ToolSchema]:
        """Discover tools that match given capabilities."""
        if not capabilities:
            return list(self._tools.values())

        matching_tools = []
        for tool in self._tools.values():
            if not tool.capabilities or all(
                cap in capabilities for cap in tool.capabilities
            ):
                matching_tools.append(tool)
        return matching_tools

    def list_all(self) -> List[ToolSchema]:
        """List all registered tools."""
        return list(self._tools.values())

    async def execute_tool(
        self, name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool by name with parameters."""
        executor = self.get_executor(name)
        if not executor:
            raise ValueError(f"No executor found for tool: {name}")

        return await executor.execute(name, parameters)
