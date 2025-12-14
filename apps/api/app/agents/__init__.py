"""
Multi-agent system for prompt-driven code generation.

This package contains specialized agents for different stages of code generation:
- Planner: Analyzes prompts and creates structured specifications
- Coder: Generates code from specifications
- Tester: Reviews code and creates tests
- Documenter: Generates documentation (future)
"""

from .planner import create_planner_agent, create_planning_task, run_planner
from .coder import create_coder_agent, create_coding_task, run_coder
from .tester import create_tester_agent, create_testing_task, run_tester


__all__ = [
    "create_planner_agent",
    "create_planning_task", 
    "run_planner",
    "create_coder_agent",
    "create_coding_task",
    "run_coder",
    "create_tester_agent",
    "create_testing_task",
    "run_tester",
]
