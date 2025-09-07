"""
Kyros Agent SDK

A comprehensive SDK for building and managing AI agents in the Kyros system.
"""

from .contracts import AgentBase, AgentContext
from .protocol.messages import AgentMessage, Artifact
from .tools.protocol import ToolRegistry, ToolSchema, ToolExecutor
from .memory.store import AgentMemoryStore, InteractionRecord
from .memory.sqlite_store import SQLiteMemoryStore
from .sandbox.executor import SandboxExecutor, ExecutionResult
from .sandbox.subprocess_executor import SubprocessSandbox
from .capabilities.negotiator import CapabilityNegotiator, TaskRequirements, AgentCapability

__version__ = "0.1.0"
__all__ = [
    "AgentBase",
    "AgentContext", 
    "AgentMessage",
    "Artifact",
    "ToolRegistry",
    "ToolSchema", 
    "ToolExecutor",
    "AgentMemoryStore",
    "InteractionRecord",
    "SQLiteMemoryStore",
    "SandboxExecutor",
    "ExecutionResult",
    "SubprocessSandbox",
    "CapabilityNegotiator",
    "TaskRequirements",
    "AgentCapability"
]
