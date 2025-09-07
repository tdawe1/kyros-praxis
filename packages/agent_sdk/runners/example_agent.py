"""
Example agent implementation demonstrating the Agent SDK usage.
"""

from datetime import datetime
from typing import Any, Dict, List

from ..contracts import AgentBase, AgentContext
from ..memory.store import AgentMemoryStore
from ..protocol.messages import AgentMessage, Artifact
from ..sandbox.executor import SandboxExecutor
from ..tools.protocol import ToolExecutor, ToolRegistry, ToolSchema


class ExampleToolExecutor(ToolExecutor):
    """Example tool executor for demonstration."""

    async def execute(self, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with parameters."""
        if name == "echo":
            return {
                "result": parameters.get("message", ""),
                "timestamp": datetime.utcnow().isoformat(),
            }
        elif name == "add":
            a = parameters.get("a", 0)
            b = parameters.get("b", 0)
            return {"result": a + b, "operation": "addition"}
        elif name == "get_time":
            return {"result": datetime.utcnow().isoformat(), "timezone": "UTC"}
        else:
            raise ValueError(f"Unknown tool: {name}")


class ExampleAgent(AgentBase):
    """Example agent that demonstrates basic functionality."""

    def __init__(self, memory_store: AgentMemoryStore, sandbox: SandboxExecutor):
        self.memory_store = memory_store
        self.sandbox = sandbox
        self.tool_registry = ToolRegistry()
        self._setup_tools()

    def _setup_tools(self):
        """Set up available tools for this agent."""
        # Register echo tool
        echo_tool = ToolSchema(
            name="echo",
            description="Echo back a message",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo"}
                },
                "required": ["message"],
            },
            returns={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "timestamp": {"type": "string"},
                },
            },
            capabilities=["communication"],
        )

        # Register math tool
        add_tool = ToolSchema(
            name="add",
            description="Add two numbers",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
            returns={
                "type": "object",
                "properties": {
                    "result": {"type": "number"},
                    "operation": {"type": "string"},
                },
            },
            capabilities=["math", "calculation"],
        )

        # Register time tool
        time_tool = ToolSchema(
            name="get_time",
            description="Get current time",
            parameters={"type": "object", "properties": {}},
            returns={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "timezone": {"type": "string"},
                },
            },
            capabilities=["time", "utility"],
        )

        executor = ExampleToolExecutor()
        self.tool_registry.register(echo_tool, executor)
        self.tool_registry.register(add_tool, executor)
        self.tool_registry.register(time_tool, executor)

    def capabilities(self) -> List[str]:
        """Return list of capabilities this agent supports."""
        return [
            "communication",
            "math",
            "calculation",
            "time",
            "utility",
            "code_execution",
        ]

    async def execute(self, ctx: AgentContext) -> Dict[str, Any]:
        """Execute the agent with the given context."""
        task = ctx.task
        task_id = task.get("id", "unknown")
        agent_id = self.get_name()

        # Create agent message
        message = AgentMessage(
            intent=f"Process task: {task.get('description', 'Unknown task')}",
            confidence=0.8,
            rationale_summary="Analyzing task requirements and executing appropriate tools",
            agent_id=agent_id,
            task_id=task_id,
        )

        try:
            # Process the task based on its type
            result = await self._process_task(task, ctx)

            # Add artifacts if any were created
            if "artifacts" in result:
                for artifact_data in result["artifacts"]:
                    artifact = Artifact(
                        kind=artifact_data.get("kind", "output"),
                        ref=artifact_data.get("ref", "unknown"),
                        summary=artifact_data.get("summary", "Generated output"),
                        metadata=artifact_data.get("metadata", {}),
                    )
                    message.artifacts.append(artifact)

            # Store interaction in memory
            await self.memory_store.store_interaction(
                agent_id=agent_id, task_id=task_id, context=ctx.dict(), result=result
            )

            # Update message with results
            message.next_actions = result.get("next_actions", [])

            return {"status": "success", "message": message.dict(), "result": result}

        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "message": message.dict(),
            }

            # Store error interaction
            await self.memory_store.store_interaction(
                agent_id=agent_id,
                task_id=task_id,
                context=ctx.dict(),
                result=error_result,
            )

            return error_result

    async def _process_task(
        self, task: Dict[str, Any], ctx: AgentContext
    ) -> Dict[str, Any]:
        """Process a specific task."""
        task_type = task.get("type", "unknown")

        if task_type == "echo":
            return await self._handle_echo_task(task)
        elif task_type == "math":
            return await self._handle_math_task(task)
        elif task_type == "code":
            return await self._handle_code_task(task, ctx)
        elif task_type == "time":
            return await self._handle_time_task(task)
        else:
            return await self._handle_generic_task(task)

    async def _handle_echo_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle echo task."""
        message = task.get("message", "Hello, World!")
        result = await self.tool_registry.execute_tool("echo", {"message": message})
        return {
            "output": result["result"],
            "next_actions": ["Task completed successfully"],
        }

    async def _handle_math_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle math task."""
        a = task.get("a", 0)
        b = task.get("b", 0)
        result = await self.tool_registry.execute_tool("add", {"a": a, "b": b})
        return {
            "output": result["result"],
            "operation": result["operation"],
            "next_actions": ["Math operation completed"],
        }

    async def _handle_code_task(
        self, task: Dict[str, Any], ctx: AgentContext
    ) -> Dict[str, Any]:
        """Handle code execution task."""
        code = task.get("code", "")
        language = task.get("language", "python")
        timeout = task.get("timeout", 30)

        # Execute code in sandbox
        execution_result = await self.sandbox.execute(
            code=code, language=language, timeout=timeout
        )

        artifacts = []
        if execution_result.stdout:
            artifacts.append(
                {
                    "kind": "output",
                    "ref": f"stdout_{datetime.utcnow().timestamp()}",
                    "summary": f"Code output ({language})",
                    "metadata": {
                        "language": language,
                        "execution_time": execution_result.execution_time,
                        "exit_code": execution_result.exit_code,
                    },
                }
            )

        return {
            "output": execution_result.stdout,
            "error": execution_result.stderr,
            "exit_code": execution_result.exit_code,
            "execution_time": execution_result.execution_time,
            "artifacts": artifacts,
            "next_actions": ["Code execution completed"],
        }

    async def _handle_time_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle time task."""
        result = await self.tool_registry.execute_tool("get_time", {})
        return {
            "output": result["result"],
            "timezone": result["timezone"],
            "next_actions": ["Time retrieved successfully"],
        }

    async def _handle_generic_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generic task."""
        description = task.get("description", "Generic task")
        return {
            "output": f"Processed: {description}",
            "next_actions": ["Generic task completed"],
        }
