from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..contracts import AgentBase


@dataclass
class TaskRequirements:
    """Requirements for a task."""

    labels: List[str]
    capabilities: List[str]
    priority: int = 1
    timeout: Optional[int] = None
    memory_limit: Optional[int] = None


@dataclass
class AgentCapability:
    """Agent capability information."""

    agent: AgentBase
    capabilities: List[str]
    load: float = 0.0  # Current load (0-1)
    priority: int = 1


class CapabilityNegotiator:
    """Negotiates agent assignment based on task requirements and agent capabilities."""

    def __init__(self):
        self._agent_capabilities: Dict[str, AgentCapability] = {}

    def register_agent(
        self, agent: AgentBase, capabilities: List[str], priority: int = 1
    ):
        """Register an agent with its capabilities."""
        agent_id = agent.get_name()
        self._agent_capabilities[agent_id] = AgentCapability(
            agent=agent, capabilities=capabilities, priority=priority
        )

    def unregister_agent(self, agent_id: str):
        """Unregister an agent."""
        self._agent_capabilities.pop(agent_id, None)

    def update_agent_load(self, agent_id: str, load: float):
        """Update an agent's current load."""
        if agent_id in self._agent_capabilities:
            self._agent_capabilities[agent_id].load = max(0.0, min(1.0, load))

    def match(
        self, task: Dict[str, Any], agents: Optional[List[AgentBase]] = None
    ) -> Tuple[Optional[AgentBase], List[str]]:
        """
        Match a task to the best available agent.

        Args:
            task: Task dictionary with requirements
            agents: Optional list of agents to consider (if None, uses all registered)

        Returns:
            Tuple of (best_agent, missing_capabilities)
        """
        # Extract task requirements
        requirements = self._extract_requirements(task)

        # Get candidate agents
        if agents is None:
            candidate_agents = [cap.agent for cap in self._agent_capabilities.values()]
        else:
            candidate_agents = agents

        if not candidate_agents:
            return None, requirements.capabilities

        # Score each agent
        best_agent = None
        best_score = -1.0
        missing_capabilities = requirements.capabilities.copy()

        for agent in candidate_agents:
            agent_id = agent.get_name()
            agent_cap = self._agent_capabilities.get(agent_id)

            if not agent_cap:
                # If agent not registered, get capabilities directly
                agent_capabilities = agent.capabilities()
            else:
                agent_capabilities = agent_cap.capabilities

            # Calculate capability match score
            score, missing = self._calculate_match_score(
                requirements, agent_capabilities, agent_cap
            )

            if score > best_score:
                best_score = score
                best_agent = agent
                missing_capabilities = missing

        return best_agent, missing_capabilities

    def _extract_requirements(self, task: Dict[str, Any]) -> TaskRequirements:
        """Extract requirements from task dictionary."""
        labels = task.get("labels", [])
        capabilities = task.get("capabilities", [])
        priority = task.get("priority", 1)
        timeout = task.get("timeout")
        memory_limit = task.get("memory_limit")

        return TaskRequirements(
            labels=labels,
            capabilities=capabilities,
            priority=priority,
            timeout=timeout,
            memory_limit=memory_limit,
        )

    def _calculate_match_score(
        self,
        requirements: TaskRequirements,
        agent_capabilities: List[str],
        agent_cap: Optional[AgentCapability],
    ) -> Tuple[float, List[str]]:
        """Calculate how well an agent matches task requirements."""
        if not requirements.capabilities:
            # If no specific capabilities required, return base score
            base_score = 1.0
            if agent_cap:
                base_score -= agent_cap.load * 0.5  # Penalize loaded agents
                base_score += agent_cap.priority * 0.1  # Bonus for high priority agents
            return base_score, []

        # Calculate capability overlap
        required_caps = set(requirements.capabilities)
        agent_caps = set(agent_capabilities)

        matching_caps = required_caps.intersection(agent_caps)
        missing_caps = required_caps - agent_caps

        # Base score from capability match
        if not required_caps:
            score = 1.0
        else:
            score = len(matching_caps) / len(required_caps)

        # Adjust for agent load and priority
        if agent_cap:
            score -= agent_cap.load * 0.3  # Penalize loaded agents
            score += agent_cap.priority * 0.1  # Bonus for high priority agents

        # Penalize if critical capabilities are missing
        if missing_caps:
            score *= 0.5

        return score, list(missing_caps)

    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents."""
        status = {}
        for agent_id, cap in self._agent_capabilities.items():
            status[agent_id] = {
                "capabilities": cap.capabilities,
                "load": cap.load,
                "priority": cap.priority,
                "available": cap.load < 0.9,  # Consider loaded if > 90%
            }
        return status
