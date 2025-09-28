"""
Agentic Workflow System for Sophisticated Agent Coordination

This package implements advanced agentic workflow patterns including:
- ReAct loops (Reason → Act → Observe)
- Self-reflection and critique capabilities  
- Critic-generator loops for iterative improvement
- Manager-worker hierarchies for task delegation
- Persistent memory and context management

The system transforms the basic orchestrator into a sophisticated agent coordination
platform that can manage complex, multi-step workflows with adaptive behavior.
"""

from .models import (
    AgentDefinition,
    AgentInstance, 
    AgentRun,
    Thought,
    Action,
    Observation,
    Reflection,
    AgentMemory,
    TaskDelegation,
    AgentType,
    AgentStatus,
    RunStatus,
    ThoughtType,
    ActionType,
    ReflectionType,
)

from .react_engine import (
    ReActEngine,
    ReActLoop,
    AgentCoordinator,
)

from .memory_manager import (
    MemoryManager,
    MemoryType,
)

from .reflection_system import (
    ReflectionSystem,
    CriticGenerator,
)

__all__ = [
    # Models
    "AgentDefinition",
    "AgentInstance", 
    "AgentRun",
    "Thought",
    "Action", 
    "Observation",
    "Reflection",
    "AgentMemory",
    "TaskDelegation",
    # Enums
    "AgentType",
    "AgentStatus", 
    "RunStatus",
    "ThoughtType",
    "ActionType",
    "ReflectionType",
    # Core Engine
    "ReActEngine",
    "ReActLoop",
    "AgentCoordinator",
    # Memory Management
    "MemoryManager",
    "MemoryType",
    # Reflection System
    "ReflectionSystem", 
    "CriticGenerator",
]