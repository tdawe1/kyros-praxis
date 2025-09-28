"""
ReAct Loop Engine for Adaptive Agent Behavior

This module implements the core ReAct (Reason → Act → Observe) loop engine that enables
sophisticated agent coordination with adaptive decision-making, iterative problem-solving,
and continuous learning capabilities.

The ReAct engine coordinates:
- Reasoning: Deep analysis and planning phases
- Action: Execution of planned actions with validation
- Observation: Environment monitoring and feedback analysis
- Reflection: Self-critique and continuous improvement

Key Components:
1. ReActLoop: Core loop implementation for individual runs
2. ReActEngine: High-level engine managing multiple agents and runs
3. AgentCoordinator: Coordination layer for multi-agent workflows
4. PhaseManager: Manages transitions between ReAct phases
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, Field

from .models import (
    AgentInstance, AgentRun, Thought, Action, Observation, Reflection,
    AgentStatus, RunStatus, ThoughtType, ActionType, ReflectionType,
    AgentDefinition, AgentMemory, TaskDelegation
)
# Fixed imports for orchestrator service
try:
    from ..database import get_db_session
except ImportError:
    try:
        from database import get_db_session
    except ImportError:
        def get_db_session():
            pass

try:
    from ..app.core.logging import log_orchestrator_event
except ImportError:
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.core.logging import log_orchestrator_event
    except ImportError:
        def log_orchestrator_event(**kwargs):
            pass

logger = logging.getLogger(__name__)


class ReActConfig(BaseModel):
    """Configuration for ReAct loop execution."""
    max_iterations: int = Field(default=10, ge=1, le=100)
    reflection_frequency: int = Field(default=3, ge=1)
    timeout_seconds: int = Field(default=300, ge=30)
    enable_parallel_actions: bool = Field(default=False)
    enable_self_reflection: bool = Field(default=True)
    enable_memory_persistence: bool = Field(default=True)
    reasoning_timeout: int = Field(default=60, ge=10)
    action_timeout: int = Field(default=120, ge=10)  
    observation_timeout: int = Field(default=30, ge=5)


class PhaseResult(BaseModel):
    """Result of a ReAct phase execution."""
    success: bool
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    execution_time: float
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ReActLoop:
    """
    Core ReAct loop implementation for individual agent runs.
    
    Manages the execution of a single ReAct loop for an agent, coordinating
    the reasoning, action, and observation phases with proper error handling,
    timeout management, and progress tracking.
    """
    
    def __init__(
        self,
        agent_instance: AgentInstance,
        run: AgentRun,
        db_session: AsyncSession,
        config: ReActConfig,
        mcp_client: Optional[Any] = None
    ):
        self.agent_instance = agent_instance
        self.run = run
        self.db = db_session
        self.config = config
        self.mcp_client = mcp_client
        self.current_iteration = 0
        self.loop_active = False
        
        # Phase handlers
        self.phase_handlers = {
            'reasoning': self._execute_reasoning_phase,
            'acting': self._execute_action_phase,
            'observing': self._execute_observation_phase,
            'reflecting': self._execute_reflection_phase
        }
        
    async def start_loop(self, goal: str, initial_context: Optional[Dict] = None) -> bool:
        """
        Start the ReAct loop execution.
        
        Args:
            goal: Primary goal for the agent run
            initial_context: Initial context and parameters
            
        Returns:
            bool: True if loop completed successfully, False otherwise
        """
        try:
            self.loop_active = True
            self.run.goal = goal
            self.run.status = RunStatus.REASONING.value
            self.run.input_context = initial_context or {}
            
            await self._update_run_status(RunStatus.REASONING)
            
            log_orchestrator_event(
                event="react_loop_started",
                task_id=self.run.id,
                agent_id=self.agent_instance.id,
                goal=goal,
                max_iterations=self.config.max_iterations
            )
            
            # Main ReAct loop
            while (self.current_iteration < self.config.max_iterations and 
                   self.loop_active and 
                   self.run.status not in [RunStatus.COMPLETED.value, RunStatus.FAILED.value]):
                
                iteration_success = await self._execute_iteration()
                
                if not iteration_success:
                    logger.warning(f"Iteration {self.current_iteration} failed for run {self.run.id}")
                    
                # Check if goal is achieved
                if await self._is_goal_achieved():
                    await self._complete_run(success=True)
                    break
                    
                self.current_iteration += 1
                
            # Final reflection if loop ended without completion
            if self.run.status not in [RunStatus.COMPLETED.value, RunStatus.FAILED.value]:
                if self.current_iteration >= self.config.max_iterations:
                    await self._complete_run(success=False, error="Maximum iterations reached")
                else:
                    await self._complete_run(success=False, error="Loop terminated unexpectedly")
                    
            return self.run.success
            
        except Exception as e:
            logger.error(f"ReAct loop error for run {self.run.id}: {e}", exc_info=True)
            await self._complete_run(success=False, error=str(e))
            return False
            
    async def _execute_iteration(self) -> bool:
        """Execute a single ReAct iteration."""
        try:
            iteration_start = time.time()
            
            log_orchestrator_event(
                event="react_iteration_started",
                task_id=self.run.id,
                iteration=self.current_iteration
            )
            
            # Reasoning Phase
            reasoning_result = await self._execute_reasoning_phase()
            if not reasoning_result.success:
                return False
                
            # Action Phase  
            action_result = await self._execute_action_phase()
            if not action_result.success:
                return False
                
            # Observation Phase
            observation_result = await self._execute_observation_phase()
            if not observation_result.success:
                return False
                
            # Reflection Phase (if due)
            if (self.config.enable_self_reflection and 
                self.current_iteration % self.config.reflection_frequency == 0):
                await self._execute_reflection_phase()
                
            iteration_time = time.time() - iteration_start
            
            log_orchestrator_event(
                event="react_iteration_completed",
                task_id=self.run.id,
                iteration=self.current_iteration,
                duration=iteration_time
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Iteration {self.current_iteration} error: {e}", exc_info=True)
            return False
            
    async def _execute_reasoning_phase(self) -> PhaseResult:
        """Execute the reasoning phase of the ReAct loop."""
        start_time = time.time()
        
        try:
            await self._update_run_status(RunStatus.REASONING)
            
            # Get current context
            context = await self._build_reasoning_context()
            
            # Generate reasoning prompt
            reasoning_prompt = await self._build_reasoning_prompt(context)
            
            # Execute reasoning (this would call the LLM)
            reasoning_content = await self._execute_llm_reasoning(reasoning_prompt, context)
            
            # Parse and structure reasoning
            structured_reasoning = await self._parse_reasoning_output(reasoning_content)
            
            # Store thought in database
            thought = Thought(
                run_id=self.run.id,
                thought_type=structured_reasoning.get('type', ThoughtType.NEXT_STEP.value),
                iteration=self.current_iteration,
                sequence=0,  # First thought in iteration
                content=reasoning_content,
                reasoning_chain=structured_reasoning.get('chain'),
                current_state=context.get('current_state'),
                goal_progress=structured_reasoning.get('goal_progress'),
                constraints=structured_reasoning.get('constraints'),
                options_considered=structured_reasoning.get('options'),
                confidence_score=structured_reasoning.get('confidence', 0.5),
                uncertainty_factors=structured_reasoning.get('uncertainties'),
                assumptions=structured_reasoning.get('assumptions'),
                reasoning_time=time.time() - start_time,
                complexity_score=structured_reasoning.get('complexity', 0.5)
            )
            
            self.db.add(thought)
            await self.db.commit()
            
            self.run.last_thought_id = thought.id
            await self.db.commit()
            
            log_orchestrator_event(
                event="reasoning_completed",
                task_id=self.run.id,
                thought_id=thought.id,
                confidence=thought.confidence_score,
                complexity=thought.complexity_score
            )
            
            return PhaseResult(
                success=True,
                content=reasoning_content,
                structured_data=structured_reasoning,
                confidence=thought.confidence_score,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Reasoning phase error: {e}", exc_info=True)
            return PhaseResult(
                success=False,
                content="",
                execution_time=time.time() - start_time,
                error=str(e)
            )
            
    async def _execute_action_phase(self) -> PhaseResult:
        """Execute the action phase of the ReAct loop."""
        start_time = time.time()
        
        try:
            await self._update_run_status(RunStatus.ACTING)
            
            # Get action plan from last reasoning
            last_thought = await self._get_last_thought()
            if not last_thought:
                raise ValueError("No reasoning output found for action planning")
                
            # Parse action from reasoning
            action_plan = await self._extract_action_plan(last_thought)
            
            # Execute the planned action
            action_result = await self._execute_planned_action(action_plan)
            
            # Store action in database
            action = Action(
                run_id=self.run.id,
                action_type=action_plan.get('type', ActionType.TOOL_USE.value),
                iteration=self.current_iteration,
                sequence=0,  # First action in iteration
                name=action_plan.get('name', 'unknown_action'),
                description=action_plan.get('description'),
                parameters=action_plan.get('parameters'),
                target_system=action_plan.get('target_system'),
                method=action_plan.get('method'),
                execution_plan=action_plan.get('execution_plan'),
                status="completed" if action_result['success'] else "failed",
                result=action_result.get('result'),
                error_details=action_result.get('error'),
                side_effects=action_result.get('side_effects'),
                execution_time=time.time() - start_time,
                success=action_result['success'],
                expected_outcome=action_plan.get('expected_outcome'),
                actual_outcome=action_result.get('result'),
                validation_score=action_result.get('validation_score', 0.5),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            self.db.add(action)
            await self.db.commit()
            
            self.run.last_action_id = action.id
            await self.db.commit()
            
            log_orchestrator_event(
                event="action_completed",
                task_id=self.run.id,
                action_id=action.id,
                action_type=action.action_type,
                success=action.success,
                execution_time=action.execution_time
            )
            
            return PhaseResult(
                success=action_result['success'],
                content=json.dumps(action_result.get('result', {})),
                structured_data=action_result,
                execution_time=time.time() - start_time,
                error=action_result.get('error')
            )
            
        except Exception as e:
            logger.error(f"Action phase error: {e}", exc_info=True)
            return PhaseResult(
                success=False,
                content="",
                execution_time=time.time() - start_time,
                error=str(e)
            )
            
    async def _execute_observation_phase(self) -> PhaseResult:
        """Execute the observation phase of the ReAct loop."""
        start_time = time.time()
        
        try:
            await self._update_run_status(RunStatus.OBSERVING)
            
            # Gather observations from multiple sources
            observations = await self._gather_observations()
            
            # Analyze and structure observations
            structured_obs = await self._analyze_observations(observations)
            
            # Store observation in database
            observation = Observation(
                run_id=self.run.id,
                iteration=self.current_iteration,
                sequence=0,  # First observation in iteration
                observation_source="environment",
                content=structured_obs.get('summary', ''),
                structured_data=structured_obs,
                environment_state=structured_obs.get('environment_state'),
                state_changes=structured_obs.get('state_changes'),
                action_feedback=structured_obs.get('action_feedback'),
                patterns_detected=structured_obs.get('patterns'),
                anomalies=structured_obs.get('anomalies'),
                trends=structured_obs.get('trends'),
                reliability_score=structured_obs.get('reliability', 0.8),
                completeness_score=structured_obs.get('completeness', 0.8),
                noise_level=structured_obs.get('noise_level', 0.2),
                processing_time=time.time() - start_time,
                complexity_score=structured_obs.get('complexity', 0.5),
                observed_at=datetime.utcnow()
            )
            
            self.db.add(observation)
            await self.db.commit()
            
            self.run.last_observation_id = observation.id
            await self.db.commit()
            
            log_orchestrator_event(
                event="observation_completed", 
                task_id=self.run.id,
                observation_id=observation.id,
                reliability=observation.reliability_score,
                completeness=observation.completeness_score
            )
            
            return PhaseResult(
                success=True,
                content=structured_obs.get('summary', ''),
                structured_data=structured_obs,
                confidence=observation.reliability_score,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Observation phase error: {e}", exc_info=True)
            return PhaseResult(
                success=False,
                content="",
                execution_time=time.time() - start_time,
                error=str(e)
            )
            
    async def _execute_reflection_phase(self) -> PhaseResult:
        """Execute the reflection phase for self-improvement."""
        start_time = time.time()
        
        try:
            await self._update_run_status(RunStatus.REFLECTING)
            
            # Gather reflection context
            reflection_context = await self._build_reflection_context()
            
            # Execute self-reflection
            reflection_content = await self._execute_self_reflection(reflection_context)
            
            # Parse reflection insights
            reflection_insights = await self._parse_reflection_output(reflection_content)
            
            # Store reflection in database
            reflection = Reflection(
                run_id=self.run.id,
                reflection_type=ReflectionType.SELF_CRITIQUE.value,
                scope="iteration",
                target_iteration=self.current_iteration,
                content=reflection_content,
                insights=reflection_insights.get('insights'),
                strengths_identified=reflection_insights.get('strengths'),
                weaknesses_identified=reflection_insights.get('weaknesses'),
                mistakes_analysis=reflection_insights.get('mistakes'),
                suggestions=reflection_insights.get('suggestions'),
                strategy_adjustments=reflection_insights.get('strategy_adjustments'),
                learning_points=reflection_insights.get('learning_points'),
                self_critique_score=reflection_insights.get('critique_quality', 0.5),
                insight_quality=reflection_insights.get('insight_quality', 0.5),
                actionability=reflection_insights.get('actionability', 0.5),
                reflection_time=time.time() - start_time
            )
            
            self.db.add(reflection)
            await self.db.commit()
            
            log_orchestrator_event(
                event="reflection_completed",
                task_id=self.run.id,
                reflection_id=reflection.id,
                critique_quality=reflection.self_critique_score,
                insight_quality=reflection.insight_quality
            )
            
            return PhaseResult(
                success=True,
                content=reflection_content,
                structured_data=reflection_insights,
                confidence=reflection.insight_quality,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Reflection phase error: {e}", exc_info=True)
            return PhaseResult(
                success=False,
                content="",
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    # Helper methods for phase execution
    
    async def _build_reasoning_context(self) -> Dict[str, Any]:
        """Build context for the reasoning phase."""
        context = {
            'goal': self.run.goal,
            'current_iteration': self.current_iteration,
            'max_iterations': self.config.max_iterations,
            'agent_capabilities': self.agent_instance.definition.capabilities,
            'previous_thoughts': [],
            'previous_actions': [],
            'previous_observations': [],
            'memory_context': await self._get_relevant_memories(),
            'current_state': await self._assess_current_state()
        }
        
        # Get recent history
        if self.current_iteration > 0:
            context['previous_thoughts'] = await self._get_recent_thoughts(limit=3)
            context['previous_actions'] = await self._get_recent_actions(limit=3)
            context['previous_observations'] = await self._get_recent_observations(limit=3)
            
        return context
        
    async def _execute_llm_reasoning(self, prompt: str, context: Dict) -> str:
        """Execute LLM-based reasoning (placeholder for actual LLM integration)."""
        # This would integrate with the actual LLM service
        # For now, return a structured reasoning example
        reasoning = f"""
        Given the goal: {context['goal']}
        Current iteration: {context['current_iteration']}
        
        Analysis:
        1. Current situation assessment
        2. Available options evaluation  
        3. Constraint identification
        4. Next action planning
        
        Decision: [Planned next action]
        Confidence: 0.8
        """
        
        await asyncio.sleep(0.1)  # Simulate LLM processing time
        return reasoning
        
    async def _parse_reasoning_output(self, content: str) -> Dict[str, Any]:
        """Parse and structure LLM reasoning output."""
        # This would parse the actual LLM output
        # For now, return structured example
        return {
            'type': ThoughtType.ACTION_PLANNING.value,
            'chain': [
                {'step': 1, 'description': 'Situation assessment'},
                {'step': 2, 'description': 'Option evaluation'},
                {'step': 3, 'description': 'Action planning'}
            ],
            'goal_progress': {'completion': 0.3, 'milestones_reached': 1},
            'constraints': ['time_limit', 'resource_availability'],
            'options': [
                {'option': 'option_a', 'pros': ['fast'], 'cons': ['risky']},
                {'option': 'option_b', 'pros': ['safe'], 'cons': ['slow']}
            ],
            'confidence': 0.8,
            'uncertainties': ['market_conditions', 'external_dependencies'],
            'assumptions': ['stable_environment', 'resource_availability'],
            'complexity': 0.6
        }
        
    async def _update_run_status(self, status: RunStatus):
        """Update the run status in the database."""
        self.run.status = status.value
        self.run.current_phase = status.value
        await self.db.commit()
        
    async def _is_goal_achieved(self) -> bool:
        """Check if the run goal has been achieved."""
        # This would implement goal achievement detection
        # For now, simple heuristic
        return self.current_iteration >= 3  # Placeholder logic
        
    async def _complete_run(self, success: bool, error: Optional[str] = None):
        """Complete the run with final status."""
        self.loop_active = False
        self.run.success = success
        self.run.status = RunStatus.COMPLETED.value if success else RunStatus.FAILED.value
        self.run.completed_at = datetime.utcnow()
        
        if error:
            self.run.error_message = error
            
        await self.db.commit()
        
        log_orchestrator_event(
            event="react_loop_completed",
            task_id=self.run.id,
            success=success,
            iterations=self.current_iteration,
            error=error
        )

    # Additional helper methods would be implemented here...
    async def _get_last_thought(self) -> Optional[Thought]:
        """Get the most recent thought for this run."""
        result = await self.db.execute(
            select(Thought)
            .where(Thought.run_id == self.run.id)
            .order_by(Thought.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
        
    async def _extract_action_plan(self, thought: Thought) -> Dict[str, Any]:
        """Extract action plan from reasoning output."""
        # Parse the thought content to extract action plan
        return {
            'type': ActionType.TOOL_USE.value,
            'name': 'example_action',
            'description': 'Example action based on reasoning',
            'parameters': {'param1': 'value1'},
            'target_system': 'mcp_server',
            'method': 'execute_tool',
            'expected_outcome': {'expected': 'result'}
        }
        
    async def _execute_planned_action(self, action_plan: Dict) -> Dict[str, Any]:
        """Execute the planned action."""
        # This would execute the actual action
        await asyncio.sleep(0.1)  # Simulate action execution
        return {
            'success': True,
            'result': {'status': 'completed', 'output': 'action_result'},
            'validation_score': 0.9
        }
        
    async def _gather_observations(self) -> Dict[str, Any]:
        """Gather observations from the environment."""
        # Collect observations from various sources
        return {
            'environment_status': 'stable',
            'action_results': 'positive',
            'state_changes': ['change1', 'change2']
        }
        
    async def _analyze_observations(self, observations: Dict) -> Dict[str, Any]:
        """Analyze and structure observations."""
        return {
            'summary': 'Observations analyzed successfully',
            'environment_state': observations.get('environment_status'),
            'state_changes': observations.get('state_changes'),
            'action_feedback': 'positive',
            'reliability': 0.9,
            'completeness': 0.8,
            'noise_level': 0.1,
            'complexity': 0.5
        }
        
    async def _get_relevant_memories(self) -> List[Dict]:
        """Get relevant memories for current context."""
        # Query agent memory for relevant context
        return []
        
    async def _assess_current_state(self) -> Dict[str, Any]:
        """Assess the current state of the environment."""
        return {'state': 'active', 'resources': 'available'}
        
    async def _build_reasoning_prompt(self, context: Dict) -> str:
        """Build the reasoning prompt for the LLM."""
        return f"Reasoning prompt for goal: {context['goal']}"
        
    async def _get_recent_thoughts(self, limit: int) -> List[Dict]:
        """Get recent thoughts from this run."""
        return []
        
    async def _get_recent_actions(self, limit: int) -> List[Dict]:
        """Get recent actions from this run."""
        return []
        
    async def _get_recent_observations(self, limit: int) -> List[Dict]:
        """Get recent observations from this run."""
        return []
        
    async def _build_reflection_context(self) -> Dict[str, Any]:
        """Build context for reflection phase."""
        return {
            'recent_performance': 'good',
            'goal_progress': 0.5,
            'iteration_summary': f'Completed {self.current_iteration} iterations'
        }
        
    async def _execute_self_reflection(self, context: Dict) -> str:
        """Execute self-reflection analysis."""
        return f"Reflection on performance: {context['recent_performance']}"
        
    async def _parse_reflection_output(self, content: str) -> Dict[str, Any]:
        """Parse reflection output into structured insights."""
        return {
            'insights': ['insight1', 'insight2'],
            'strengths': ['strength1'],
            'weaknesses': ['weakness1'],
            'suggestions': ['suggestion1'],
            'critique_quality': 0.7,
            'insight_quality': 0.8,
            'actionability': 0.6
        }


class ReActEngine:
    """
    High-level ReAct engine managing multiple agents and runs.
    
    Coordinates multiple ReAct loops, manages agent lifecycle, handles
    resource allocation, and provides oversight for complex multi-agent workflows.
    """
    
    def __init__(self, db_session: AsyncSession, mcp_client: Optional[Any] = None):
        self.db = db_session
        self.mcp_client = mcp_client
        self.active_runs: Dict[str, ReActLoop] = {}
        self.config = ReActConfig()
        
    async def start_agent_run(
        self,
        agent_instance_id: str,
        goal: str,
        context: Optional[Dict] = None,
        config_overrides: Optional[Dict] = None
    ) -> str:
        """Start a new ReAct run for an agent."""
        
        # Get agent instance
        result = await self.db.execute(
            select(AgentInstance).where(AgentInstance.id == agent_instance_id)
        )
        agent_instance = result.scalar_one_or_none()
        
        if not agent_instance:
            raise ValueError(f"Agent instance {agent_instance_id} not found")
            
        # Create agent run
        run = AgentRun(
            agent_instance_id=agent_instance_id,
            goal=goal,
            input_context=context,
            max_iterations=self.config.max_iterations
        )
        
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        
        # Apply config overrides
        config = ReActConfig(**self.config.model_dump())
        if config_overrides:
            for key, value in config_overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # Create and start ReAct loop
        react_loop = ReActLoop(agent_instance, run, self.db, config, self.mcp_client)
        self.active_runs[run.id] = react_loop
        
        # Start loop in background
        asyncio.create_task(self._run_loop_with_cleanup(react_loop, goal, context))
        
        return run.id
        
    async def _run_loop_with_cleanup(self, react_loop: ReActLoop, goal: str, context: Optional[Dict]):
        """Run loop with proper cleanup."""
        try:
            await react_loop.start_loop(goal, context)
        finally:
            # Cleanup
            if react_loop.run.id in self.active_runs:
                del self.active_runs[react_loop.run.id]
                
    async def get_run_status(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a running ReAct loop."""
        result = await self.db.execute(
            select(AgentRun).where(AgentRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            return None
            
        return {
            'id': run.id,
            'status': run.status,
            'current_iteration': run.current_iteration,
            'goal': run.goal,
            'started_at': run.started_at.isoformat() if run.started_at else None,
            'completed_at': run.completed_at.isoformat() if run.completed_at else None,
            'success': run.success,
            'error_message': run.error_message
        }
        
    async def stop_run(self, run_id: str) -> bool:
        """Stop a running ReAct loop."""
        if run_id in self.active_runs:
            react_loop = self.active_runs[run_id]
            react_loop.loop_active = False
            await react_loop._update_run_status(RunStatus.CANCELLED)
            del self.active_runs[run_id]
            return True
        return False


class AgentCoordinator:
    """
    Coordination layer for multi-agent workflows.
    
    Manages coordination between multiple agents, handles task delegation,
    monitors agent interactions, and ensures efficient resource utilization.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.react_engine = ReActEngine(db_session)
        self.delegation_handlers: Dict[str, Callable] = {}
        
    async def coordinate_multi_agent_task(
        self,
        task_description: str,
        required_capabilities: List[str],
        context: Optional[Dict] = None
    ) -> str:
        """Coordinate a task across multiple agents."""
        
        # Find suitable agents
        suitable_agents = await self._find_suitable_agents(required_capabilities)
        
        if not suitable_agents:
            raise ValueError("No suitable agents found for required capabilities")
            
        # Create coordination plan
        coordination_plan = await self._create_coordination_plan(
            task_description, suitable_agents, context
        )
        
        # Execute coordination plan
        coordination_run_id = str(uuid4())
        
        log_orchestrator_event(
            event="multi_agent_coordination_started",
            task_id=coordination_run_id,
            task_description=task_description,
            agent_count=len(suitable_agents)
        )
        
        # Start agent runs according to plan
        agent_runs = []
        for agent_plan in coordination_plan['agent_plans']:
            run_id = await self.react_engine.start_agent_run(
                agent_instance_id=agent_plan['agent_id'],
                goal=agent_plan['goal'],
                context=agent_plan['context']
            )
            agent_runs.append(run_id)
            
        return coordination_run_id
        
    async def _find_suitable_agents(self, capabilities: List[str]) -> List[AgentInstance]:
        """Find agents with required capabilities."""
        # Query for active agents with matching capabilities
        result = await self.db.execute(
            select(AgentInstance)
            .join(AgentDefinition)
            .where(AgentInstance.status == AgentStatus.ACTIVE.value)
        )
        
        agents = result.scalars().all()
        suitable_agents = []
        
        for agent in agents:
            agent_capabilities = agent.definition.capabilities or []
            if all(cap in agent_capabilities for cap in capabilities):
                suitable_agents.append(agent)
                
        return suitable_agents
        
    async def _create_coordination_plan(
        self,
        task_description: str,
        agents: List[AgentInstance],
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Create a coordination plan for multi-agent execution."""
        
        # Simple coordination plan (could be enhanced with AI planning)
        agent_plans = []
        
        for i, agent in enumerate(agents):
            agent_plans.append({
                'agent_id': agent.id,
                'goal': f"Sub-task {i+1} of: {task_description}",
                'context': {
                    'main_task': task_description,
                    'sub_task_index': i,
                    'total_agents': len(agents),
                    **(context or {})
                }
            })
            
        return {
            'task_description': task_description,
            'agent_plans': agent_plans,
            'coordination_strategy': 'parallel_execution'
        }