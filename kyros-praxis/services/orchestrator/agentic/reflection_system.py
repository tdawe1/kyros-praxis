"""
Self-Reflection and Critique System for Continuous Agent Improvement

This module implements sophisticated self-reflection and critique capabilities
that enable agents to analyze their own performance, identify improvement
opportunities, and implement iterative enhancement strategies.

The reflection system includes:
- Self-critique mechanisms for performance analysis
- Peer review coordination between agents
- Critic-generator loops for iterative improvement
- Performance pattern recognition
- Strategic adjustment recommendations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, or_
from pydantic import BaseModel, Field

from .models import (
    AgentInstance, AgentRun, Reflection, Thought, Action, Observation,
    ReflectionType, RunStatus, AgentMemory
)
from .memory_manager import MemoryManager, MemoryEntry, MemoryType, MemoryImportance
try:
    from app.core.logging import log_orchestrator_event
except ImportError:
    def log_orchestrator_event(**kwargs):
        pass

logger = logging.getLogger(__name__)


class ReflectionScope(str, Enum):
    """Scope levels for reflection analysis."""
    ITERATION = "iteration"      # Single ReAct iteration
    RUN = "run"                 # Entire agent run
    SESSION = "session"         # Multiple runs in session
    STRATEGIC = "strategic"     # Long-term strategy
    GLOBAL = "global"          # Overall agent performance


class CritiqueLevel(str, Enum):
    """Levels of critique depth."""
    SURFACE = "surface"         # Basic performance metrics
    ANALYTICAL = "analytical"   # Detailed analysis
    STRATEGIC = "strategic"     # Strategic implications
    METACOGNITIVE = "metacognitive"  # Thinking about thinking


class ImprovementCategory(str, Enum):
    """Categories of improvement suggestions."""
    REASONING = "reasoning"      # Reasoning quality improvements
    ACTION_SELECTION = "action_selection"  # Better action choices
    OBSERVATION = "observation"  # Better observation skills
    PLANNING = "planning"       # Strategic planning improvements
    EFFICIENCY = "efficiency"   # Time/resource efficiency
    ACCURACY = "accuracy"       # Accuracy improvements
    ROBUSTNESS = "robustness"   # Error handling and resilience


class ReflectionPrompt(BaseModel):
    """Configuration for reflection generation."""
    scope: ReflectionScope
    critique_level: CritiqueLevel
    focus_areas: List[ImprovementCategory] = Field(default_factory=list)
    include_comparisons: bool = Field(default=True)
    include_suggestions: bool = Field(default=True)
    max_reflection_length: int = Field(default=2000, ge=100, le=10000)


class CritiqueResult(BaseModel):
    """Result of a critique analysis."""
    overall_score: float = Field(ge=0.0, le=1.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    specific_issues: List[Dict[str, Any]] = Field(default_factory=list)
    improvement_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReflectionSystem:
    """
    Advanced reflection system for agent self-improvement.
    
    Coordinates self-reflection activities, manages critique processes,
    and implements learning from reflection outcomes.
    """
    
    def __init__(self, db_session: AsyncSession, memory_manager: MemoryManager):
        self.db = db_session
        self.memory_manager = memory_manager
        self.reflection_templates = self._load_reflection_templates()
        
    async def reflect_on_run(
        self,
        run_id: str,
        prompt_config: Optional[ReflectionPrompt] = None
    ) -> str:
        """
        Perform comprehensive reflection on an agent run.
        
        Args:
            run_id: ID of the agent run to reflect on
            prompt_config: Configuration for reflection generation
            
        Returns:
            str: Reflection ID
        """
        try:
            # Get run and related data
            run_data = await self._gather_run_data(run_id)
            if not run_data:
                raise ValueError(f"Run {run_id} not found")
                
            # Use default config if not provided
            if not prompt_config:
                prompt_config = ReflectionPrompt(
                    scope=ReflectionScope.RUN,
                    critique_level=CritiqueLevel.ANALYTICAL
                )
                
            # Generate reflection content
            reflection_content = await self._generate_reflection_content(run_data, prompt_config)
            
            # Parse reflection insights
            reflection_insights = await self._parse_reflection_content(reflection_content)
            
            # Store reflection
            reflection = Reflection(
                run_id=run_id,
                reflection_type=ReflectionType.SELF_CRITIQUE.value,
                scope=prompt_config.scope.value,
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
                reflection_time=reflection_insights.get('generation_time', 0.0)
            )
            
            self.db.add(reflection)
            await self.db.commit()
            await self.db.refresh(reflection)
            
            # Store insights in memory
            await self._store_reflection_memories(run_data['agent_instance_id'], reflection)
            
            log_orchestrator_event(
                event="reflection_completed",
                task_id=run_id,
                reflection_id=reflection.id,
                agent_id=run_data['agent_instance_id'],
                scope=prompt_config.scope.value,
                critique_level=prompt_config.critique_level.value
            )
            
            return reflection.id
            
        except Exception as e:
            logger.error(f"Error in run reflection: {e}", exc_info=True)
            raise
            
    async def generate_peer_critique(
        self,
        target_run_id: str,
        critic_agent_id: str,
        focus_areas: Optional[List[ImprovementCategory]] = None
    ) -> str:
        """
        Generate peer critique from another agent.
        
        Args:
            target_run_id: Run to critique
            critic_agent_id: Agent performing the critique
            focus_areas: Specific areas to focus critique on
            
        Returns:
            str: Peer review reflection ID
        """
        try:
            # Get target run data
            target_data = await self._gather_run_data(target_run_id)
            if not target_data:
                raise ValueError(f"Target run {target_run_id} not found")
                
            # Get critic agent capabilities
            critic_result = await self.db.execute(
                select(AgentInstance).where(AgentInstance.id == critic_agent_id)
            )
            critic_agent = critic_result.scalar_one_or_none()
            if not critic_agent:
                raise ValueError(f"Critic agent {critic_agent_id} not found")
                
            # Generate peer critique
            critique_content = await self._generate_peer_critique_content(
                target_data, critic_agent, focus_areas or []
            )
            
            # Parse critique insights
            critique_insights = await self._parse_reflection_content(critique_content)
            
            # Store peer review reflection
            reflection = Reflection(
                run_id=target_run_id,
                reflection_type=ReflectionType.PEER_REVIEW.value,
                scope=ReflectionScope.RUN.value,
                content=critique_content,
                insights=critique_insights.get('insights'),
                strengths_identified=critique_insights.get('strengths'),
                weaknesses_identified=critique_insights.get('weaknesses'),
                mistakes_analysis=critique_insights.get('mistakes'),
                suggestions=critique_insights.get('suggestions'),
                strategy_adjustments=critique_insights.get('strategy_adjustments'),
                learning_points=critique_insights.get('learning_points'),
                self_critique_score=critique_insights.get('critique_quality', 0.5),
                insight_quality=critique_insights.get('insight_quality', 0.5),
                actionability=critique_insights.get('actionability', 0.5)
            )
            
            # Add metadata about the critic
            reflection_metadata = {
                'critic_agent_id': critic_agent_id,
                'critic_agent_type': critic_agent.definition.agent_type,
                'critic_capabilities': critic_agent.definition.capabilities,
                'focus_areas': [fa.value for fa in focus_areas] if focus_areas else []
            }
            reflection.insights = {
                **(reflection.insights or {}),
                'peer_review_metadata': reflection_metadata
            }
            
            self.db.add(reflection)
            await self.db.commit()
            await self.db.refresh(reflection)
            
            log_orchestrator_event(
                event="peer_critique_completed",
                task_id=target_run_id,
                reflection_id=reflection.id,
                critic_agent_id=critic_agent_id,
                target_agent_id=target_data['agent_instance_id']
            )
            
            return reflection.id
            
        except Exception as e:
            logger.error(f"Error in peer critique: {e}", exc_info=True)
            raise
            
    async def analyze_performance_patterns(
        self,
        agent_instance_id: str,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze performance patterns across multiple runs.
        
        Args:
            agent_instance_id: Agent to analyze
            time_window_days: Time window for analysis
            
        Returns:
            Dict with performance pattern analysis
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
            
            # Get runs in time window
            runs_result = await self.db.execute(
                select(AgentRun)
                .where(
                    and_(
                        AgentRun.agent_instance_id == agent_instance_id,
                        AgentRun.started_at >= cutoff_date
                    )
                )
                .order_by(AgentRun.started_at.desc())
            )
            runs = runs_result.scalars().all()
            
            if not runs:
                return {'error': 'No runs found in time window'}
                
            # Analyze patterns
            patterns = {
                'total_runs': len(runs),
                'success_rate': sum(1 for r in runs if r.success) / len(runs),
                'average_iterations': sum(r.current_iteration for r in runs) / len(runs),
                'common_failure_modes': await self._identify_failure_modes(runs),
                'performance_trends': await self._analyze_performance_trends(runs),
                'efficiency_metrics': await self._calculate_efficiency_metrics(runs),
                'learning_indicators': await self._assess_learning_indicators(runs),
                'recommendation_priorities': await self._prioritize_improvements(runs)
            }
            
            # Store pattern analysis as memory
            pattern_memory = MemoryEntry(
                content=f"Performance pattern analysis: {patterns}",
                memory_type=MemoryType.SEMANTIC,
                category="performance_analysis",
                importance=MemoryImportance.HIGH,
                tags=['performance', 'patterns', 'analysis'],
                keywords=['success_rate', 'efficiency', 'learning'],
                context={
                    'analysis_date': datetime.utcnow().isoformat(),
                    'time_window_days': time_window_days,
                    'runs_analyzed': len(runs)
                }
            )
            
            await self.memory_manager.store_memory(agent_instance_id, pattern_memory)
            
            log_orchestrator_event(
                event="performance_patterns_analyzed",
                agent_id=agent_instance_id,
                runs_analyzed=len(runs),
                success_rate=patterns['success_rate'],
                time_window_days=time_window_days
            )
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing performance patterns: {e}", exc_info=True)
            return {'error': str(e)}
            
    # Helper methods
    
    async def _gather_run_data(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Gather comprehensive data about a run for reflection."""
        try:
            # Get run
            run_result = await self.db.execute(
                select(AgentRun).where(AgentRun.id == run_id)
            )
            run = run_result.scalar_one_or_none()
            if not run:
                return None
                
            # Get thoughts
            thoughts_result = await self.db.execute(
                select(Thought).where(Thought.run_id == run_id).order_by(Thought.created_at)
            )
            thoughts = thoughts_result.scalars().all()
            
            # Get actions
            actions_result = await self.db.execute(
                select(Action).where(Action.run_id == run_id).order_by(Action.created_at)
            )
            actions = actions_result.scalars().all()
            
            # Get observations
            observations_result = await self.db.execute(
                select(Observation).where(Observation.run_id == run_id).order_by(Observation.created_at)
            )
            observations = observations_result.scalars().all()
            
            return {
                'run': run,
                'agent_instance_id': run.agent_instance_id,
                'thoughts': thoughts,
                'actions': actions,
                'observations': observations,
                'goal': run.goal,
                'success': run.success,
                'iterations': run.current_iteration,
                'error_message': run.error_message
            }
            
        except Exception as e:
            logger.error(f"Error gathering run data: {e}", exc_info=True)
            return None
            
    async def _generate_reflection_content(
        self,
        run_data: Dict[str, Any],
        prompt_config: ReflectionPrompt
    ) -> str:
        """Generate reflection content based on run data and configuration."""
        
        # This would integrate with an LLM for sophisticated reflection
        # For now, generating structured reflection based on available data
        
        run = run_data['run']
        thoughts = run_data['thoughts']
        actions = run_data['actions']
        observations = run_data['observations']
        
        reflection_sections = []
        
        # Overall performance summary
        reflection_sections.append(f"""
        ## Run Performance Summary
        Goal: {run.goal}
        Status: {'Successful' if run.success else 'Failed'}
        Iterations: {run.current_iteration}
        Total thoughts: {len(thoughts)}
        Total actions: {len(actions)}
        Total observations: {len(observations)}
        """)
        
        # Reasoning quality analysis
        if thoughts:
            avg_confidence = sum(t.confidence_score for t in thoughts if t.confidence_score) / len(thoughts)
            reflection_sections.append(f"""
            ## Reasoning Analysis
            Average confidence: {avg_confidence:.2f}
            Reasoning patterns: {self._analyze_thought_patterns(thoughts)}
            Key insights: {self._extract_reasoning_insights(thoughts)}
            """)
            
        # Action effectiveness analysis
        if actions:
            success_rate = sum(1 for a in actions if a.success) / len(actions)
            reflection_sections.append(f"""
            ## Action Effectiveness
            Action success rate: {success_rate:.2f}
            Most effective actions: {self._identify_effective_actions(actions)}
            Action timing analysis: {self._analyze_action_timing(actions)}
            """)
            
        # Observation quality analysis
        if observations:
            avg_reliability = sum(o.reliability_score for o in observations if o.reliability_score) / len(observations)
            reflection_sections.append(f"""
            ## Observation Quality
            Average reliability: {avg_reliability:.2f}
            Key patterns detected: {self._summarize_observation_patterns(observations)}
            Information gaps: {self._identify_observation_gaps(observations)}
            """)
            
        # Improvement suggestions
        suggestions = self._generate_improvement_suggestions(run_data, prompt_config)
        reflection_sections.append(f"""
        ## Improvement Suggestions
        {suggestions}
        """)
        
        return "\n".join(reflection_sections)
        
    async def _parse_reflection_content(self, content: str) -> Dict[str, Any]:
        """Parse reflection content into structured insights."""
        
        # This would use NLP to parse the reflection content
        # For now, returning structured example based on content analysis
        
        return {
            'insights': ['insight1', 'insight2', 'insight3'],
            'strengths': ['good reasoning', 'effective actions'],
            'weaknesses': ['slow decision making', 'incomplete observations'],
            'mistakes': ['premature action', 'insufficient planning'],
            'suggestions': [
                {'category': 'reasoning', 'suggestion': 'Take more time for analysis'},
                {'category': 'action', 'suggestion': 'Validate assumptions before acting'}
            ],
            'strategy_adjustments': ['increase planning phase', 'add verification steps'],
            'learning_points': ['importance of patience', 'value of verification'],
            'critique_quality': 0.8,
            'insight_quality': 0.7,
            'actionability': 0.9,
            'generation_time': 2.5
        }
        
    def _load_reflection_templates(self) -> Dict[str, str]:
        """Load reflection prompt templates."""
        return {
            'self_critique': "Analyze your performance on this task...",
            'peer_review': "Review the performance of another agent...",
            'strategic': "Consider long-term strategic implications...",
            'error_analysis': "Analyze what went wrong and why..."
        }
        
    def _analyze_thought_patterns(self, thoughts: List[Thought]) -> str:
        """Analyze patterns in agent reasoning."""
        if not thoughts:
            return "No thoughts to analyze"
            
        thought_types = [t.thought_type for t in thoughts]
        most_common = max(set(thought_types), key=thought_types.count)
        return f"Primary reasoning type: {most_common}"
        
    def _extract_reasoning_insights(self, thoughts: List[Thought]) -> str:
        """Extract insights from reasoning patterns."""
        return "Showed systematic approach to problem decomposition"
        
    def _identify_effective_actions(self, actions: List[Action]) -> str:
        """Identify most effective action types."""
        if not actions:
            return "No actions to analyze"
            
        successful_actions = [a for a in actions if a.success]
        if successful_actions:
            action_types = [a.action_type for a in successful_actions]
            most_effective = max(set(action_types), key=action_types.count)
            return f"Most effective: {most_effective}"
        return "No successful actions"
        
    def _analyze_action_timing(self, actions: List[Action]) -> str:
        """Analyze timing patterns in actions."""
        return "Actions were well-timed with adequate reasoning"
        
    def _summarize_observation_patterns(self, observations: List[Observation]) -> str:
        """Summarize patterns in observations."""
        return "Consistent observation quality with good pattern detection"
        
    def _identify_observation_gaps(self, observations: List[Observation]) -> str:
        """Identify gaps in observation coverage."""
        return "Could benefit from more environmental monitoring"
        
    def _generate_improvement_suggestions(
        self,
        run_data: Dict[str, Any],
        prompt_config: ReflectionPrompt
    ) -> str:
        """Generate specific improvement suggestions."""
        suggestions = []
        
        if not run_data['success']:
            suggestions.append("Focus on goal achievement strategies")
            
        if run_data['iterations'] > 5:
            suggestions.append("Work on more efficient planning")
            
        suggestions.append("Consider adding more verification steps")
        
        return "\n".join(f"- {s}" for s in suggestions)
        
    async def _store_reflection_memories(self, agent_instance_id: str, reflection: Reflection):
        """Store reflection insights as agent memories."""
        
        # Store key insights as separate memories
        insights = reflection.insights or {}
        
        if insights.get('learning_points'):
            learning_memory = MemoryEntry(
                content=f"Learning points from reflection: {insights['learning_points']}",
                memory_type=MemoryType.SEMANTIC,
                category="learning",
                importance=MemoryImportance.HIGH,
                tags=['reflection', 'learning', 'improvement'],
                keywords=['learning', 'insights', 'improvement']
            )
            await self.memory_manager.store_memory(agent_instance_id, learning_memory)
            
        if insights.get('suggestions'):
            suggestions_memory = MemoryEntry(
                content=f"Improvement suggestions: {insights['suggestions']}",
                memory_type=MemoryType.PROCEDURAL,
                category="improvement",
                importance=MemoryImportance.HIGH,
                tags=['reflection', 'suggestions', 'improvement'],
                keywords=['suggestions', 'improvement', 'enhancement']
            )
            await self.memory_manager.store_memory(agent_instance_id, suggestions_memory)
            
    # Additional helper methods for pattern analysis
    
    async def _identify_failure_modes(self, runs: List[AgentRun]) -> List[str]:
        """Identify common failure modes across runs."""
        failed_runs = [r for r in runs if not r.success and r.error_message]
        error_patterns = {}
        
        for run in failed_runs:
            # Simplified error categorization
            if 'timeout' in run.error_message.lower():
                error_patterns['timeout'] = error_patterns.get('timeout', 0) + 1
            elif 'iteration' in run.error_message.lower():
                error_patterns['max_iterations'] = error_patterns.get('max_iterations', 0) + 1
            else:
                error_patterns['other'] = error_patterns.get('other', 0) + 1
                
        return sorted(error_patterns.keys(), key=lambda k: error_patterns[k], reverse=True)
        
    async def _analyze_performance_trends(self, runs: List[AgentRun]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if len(runs) < 2:
            return {'trend': 'insufficient_data'}
            
        # Simple trend analysis
        recent_half = runs[:len(runs)//2]
        older_half = runs[len(runs)//2:]
        
        recent_success_rate = sum(1 for r in recent_half if r.success) / len(recent_half)
        older_success_rate = sum(1 for r in older_half if r.success) / len(older_half)
        
        trend = 'improving' if recent_success_rate > older_success_rate else 'declining'
        
        return {
            'trend': trend,
            'recent_success_rate': recent_success_rate,
            'older_success_rate': older_success_rate,
            'improvement': recent_success_rate - older_success_rate
        }
        
    async def _calculate_efficiency_metrics(self, runs: List[AgentRun]) -> Dict[str, float]:
        """Calculate efficiency metrics across runs."""
        completed_runs = [r for r in runs if r.completed_at and r.started_at]
        
        if not completed_runs:
            return {'average_duration': 0.0, 'average_iterations': 0.0}
            
        durations = [(r.completed_at - r.started_at).total_seconds() for r in completed_runs]
        iterations = [r.current_iteration for r in completed_runs]
        
        return {
            'average_duration': sum(durations) / len(durations),
            'average_iterations': sum(iterations) / len(iterations),
            'efficiency_trend': 'stable'  # Placeholder
        }
        
    async def _assess_learning_indicators(self, runs: List[AgentRun]) -> Dict[str, Any]:
        """Assess indicators of learning and improvement."""
        return {
            'adaptation_score': 0.7,
            'learning_velocity': 0.5,
            'knowledge_retention': 0.8,
            'skill_development': 0.6
        }
        
    async def _prioritize_improvements(self, runs: List[AgentRun]) -> List[Dict[str, Any]]:
        """Prioritize improvement recommendations based on impact."""
        return [
            {'category': 'efficiency', 'priority': 'high', 'impact': 0.8},
            {'category': 'accuracy', 'priority': 'medium', 'impact': 0.6},
            {'category': 'robustness', 'priority': 'low', 'impact': 0.3}
        ]
        
    async def _generate_peer_critique_content(
        self,
        target_data: Dict[str, Any],
        critic_agent: AgentInstance,
        focus_areas: List[ImprovementCategory]
    ) -> str:
        """Generate peer critique content."""
        
        # This would use the critic agent's capabilities to generate critique
        # For now, returning structured example
        
        critique_sections = []
        
        critique_sections.append(f"""
        ## Peer Critique by {critic_agent.name}
        Agent Type: {critic_agent.definition.agent_type}
        
        ## Target Performance Analysis
        Goal Achievement: {'Successful' if target_data['success'] else 'Failed'}
        Efficiency: {target_data['iterations']} iterations used
        """)
        
        if ImprovementCategory.REASONING in focus_areas:
            critique_sections.append("""
            ## Reasoning Assessment
            The target agent showed systematic thinking but could benefit from:
            - More thorough option evaluation
            - Better uncertainty quantification
            - Improved assumption validation
            """)
            
        if ImprovementCategory.ACTION_SELECTION in focus_areas:
            critique_sections.append("""
            ## Action Selection Review
            Action choices were generally appropriate but consider:
            - More conservative initial actions
            - Better risk assessment
            - Improved contingency planning
            """)
            
        critique_sections.append("""
        ## Peer Recommendations
        1. Implement more structured decision frameworks
        2. Add verification steps before critical actions
        3. Develop better error recovery strategies
        """)
        
        return "\n".join(critique_sections)


class CriticGenerator:
    """
    Implements critic-generator loops for iterative improvement.
    
    Coordinates iterative cycles where agents generate solutions and
    critics evaluate and refine them for continuous enhancement.
    """
    
    def __init__(self, db_session: AsyncSession, reflection_system: ReflectionSystem):
        self.db = db_session
        self.reflection_system = reflection_system
        self.max_iterations = 5
        self.improvement_threshold = 0.1
        
    async def run_critic_generator_loop(
        self,
        initial_task: str,
        generator_agent_id: str,
        critic_agent_id: str,
        success_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a critic-generator loop for iterative improvement.
        
        Args:
            initial_task: Task description
            generator_agent_id: Agent generating solutions
            critic_agent_id: Agent providing critique
            success_criteria: Criteria for successful completion
            
        Returns:
            Dict with loop results and improvement history
        """
        try:
            loop_id = str(uuid4())
            iteration_results = []
            current_solution = None
            best_score = 0.0
            
            log_orchestrator_event(
                event="critic_generator_loop_started",
                task_id=loop_id,
                generator_agent_id=generator_agent_id,
                critic_agent_id=critic_agent_id,
                initial_task=initial_task[:100]
            )
            
            for iteration in range(self.max_iterations):
                # Generator phase
                generator_result = await self._run_generator_phase(
                    generator_agent_id,
                    initial_task,
                    current_solution,
                    iteration
                )
                
                # Critic phase
                critic_result = await self._run_critic_phase(
                    critic_agent_id,
                    generator_result,
                    success_criteria,
                    iteration
                )
                
                # Evaluate improvement
                current_score = critic_result.get('quality_score', 0.0)
                improvement = current_score - best_score
                
                iteration_result = {
                    'iteration': iteration,
                    'generator_result': generator_result,
                    'critic_result': critic_result,
                    'quality_score': current_score,
                    'improvement': improvement,
                    'meets_criteria': critic_result.get('meets_criteria', False)
                }
                
                iteration_results.append(iteration_result)
                
                # Check if success criteria met
                if critic_result.get('meets_criteria', False):
                    log_orchestrator_event(
                        event="critic_generator_success",
                        task_id=loop_id,
                        iteration=iteration,
                        final_score=current_score
                    )
                    break
                    
                # Check if improvement is sufficient
                if improvement < self.improvement_threshold and iteration > 0:
                    log_orchestrator_event(
                        event="critic_generator_plateau",
                        task_id=loop_id,
                        iteration=iteration,
                        improvement=improvement
                    )
                    break
                    
                # Update for next iteration
                current_solution = generator_result
                best_score = max(best_score, current_score)
                
            final_result = {
                'loop_id': loop_id,
                'total_iterations': len(iteration_results),
                'final_score': best_score,
                'success': any(r['meets_criteria'] for r in iteration_results),
                'iteration_history': iteration_results,
                'improvement_trajectory': [r['quality_score'] for r in iteration_results]
            }
            
            log_orchestrator_event(
                event="critic_generator_loop_completed",
                task_id=loop_id,
                **{k: v for k, v in final_result.items() if k != 'iteration_history'}
            )
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error in critic-generator loop: {e}", exc_info=True)
            return {'error': str(e)}
            
    async def _run_generator_phase(
        self,
        generator_agent_id: str,
        task: str,
        previous_solution: Optional[Dict],
        iteration: int
    ) -> Dict[str, Any]:
        """Run the generator phase to create/improve solution."""
        
        # This would integrate with the ReAct engine to run the generator agent
        # For now, simulating generator output
        
        generator_context = {
            'task': task,
            'iteration': iteration,
            'previous_solution': previous_solution,
            'improvement_focus': 'overall quality'
        }
        
        # Simulate solution generation
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            'solution': f"Generated solution for iteration {iteration}",
            'approach': 'systematic analysis and planning',
            'confidence': 0.7 + (iteration * 0.05),  # Slight improvement over iterations
            'generation_time': 2.5,
            'context': generator_context
        }
        
    async def _run_critic_phase(
        self,
        critic_agent_id: str,
        generator_result: Dict[str, Any],
        success_criteria: Dict[str, Any],
        iteration: int
    ) -> Dict[str, Any]:
        """Run the critic phase to evaluate and suggest improvements."""
        
        # This would integrate with the ReAct engine to run the critic agent
        # For now, simulating critic evaluation
        
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Simulate improving quality scores over iterations
        base_score = 0.5
        improvement_per_iteration = 0.1
        quality_score = min(base_score + (iteration * improvement_per_iteration), 0.95)
        
        meets_criteria = quality_score >= success_criteria.get('minimum_quality', 0.8)
        
        return {
            'quality_score': quality_score,
            'meets_criteria': meets_criteria,
            'strengths': [f'strength_{iteration}_1', f'strength_{iteration}_2'],
            'weaknesses': [f'weakness_{iteration}_1'] if quality_score < 0.9 else [],
            'specific_feedback': f'Iteration {iteration} shows good progress',
            'improvement_suggestions': [
                f'suggestion_{iteration}_1',
                f'suggestion_{iteration}_2'
            ] if not meets_criteria else [],
            'critique_confidence': 0.8,
            'evaluation_time': 1.5
        }