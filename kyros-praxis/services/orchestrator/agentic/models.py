"""
Agentic Workflow Models for Sophisticated Agent Coordination

This module defines the SQLAlchemy ORM models for implementing advanced agentic workflows
including ReAct loops, self-reflection, critic-generator loops, and manager-worker hierarchies.
These models enable persistent memory, context management, and sophisticated agent coordination.

The agentic system implements:
- ReAct patterns (Reason → Act → Observe)
- Self-reflection and critique capabilities
- Manager-worker hierarchies for task delegation  
- Persistent memory and context across sessions
- Critic-generator loops for iterative improvement

ENTITY MODELS:
--------------
1. AgentDefinition: Template for agent behavior and capabilities
2. AgentInstance: Running instance of an agent with state
3. AgentRun: Execution session tracking agent workflow
4. Thought: Reasoning step in ReAct loop
5. Action: Action step in ReAct loop  
6. Observation: Observation step in ReAct loop
7. Reflection: Self-critique and improvement notes
8. AgentMemory: Persistent memory and context storage
9. TaskDelegation: Manager-worker task assignments
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, Boolean, Float, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for SQLAlchemy models with async support."""
    pass


class AgentType(str, Enum):
    """Agent type classification for role-based coordination."""
    REASONING = "reasoning"      # Pure reasoning/planning agents
    ACTION = "action"           # Action execution agents  
    OBSERVER = "observer"       # Observation and monitoring agents
    CRITIC = "critic"           # Critique and evaluation agents
    MANAGER = "manager"         # Task delegation and coordination
    WORKER = "worker"           # Task execution workers
    HYBRID = "hybrid"           # Multi-capability agents


class AgentStatus(str, Enum):
    """Agent instance lifecycle status."""
    INACTIVE = "inactive"       # Agent not running
    ACTIVE = "active"          # Agent ready and available
    BUSY = "busy"              # Agent currently executing
    ERROR = "error"            # Agent in error state
    PAUSED = "paused"          # Agent temporarily paused
    TERMINATED = "terminated"   # Agent shut down


class RunStatus(str, Enum):
    """Agent run execution status."""
    STARTING = "starting"       # Run initialization
    REASONING = "reasoning"     # In reasoning phase
    ACTING = "acting"          # In action execution phase
    OBSERVING = "observing"    # In observation phase
    REFLECTING = "reflecting"   # In self-reflection phase
    COMPLETED = "completed"     # Run finished successfully
    FAILED = "failed"          # Run failed with error
    CANCELLED = "cancelled"     # Run was cancelled


class ThoughtType(str, Enum):
    """Types of reasoning thoughts in ReAct loops."""
    GOAL_ANALYSIS = "goal_analysis"         # Initial goal breakdown
    PROBLEM_DECOMPOSITION = "problem_decomposition"  # Breaking down complex problems
    STRATEGY_PLANNING = "strategy_planning"  # High-level approach planning
    ACTION_PLANNING = "action_planning"     # Specific action planning
    HYPOTHESIS = "hypothesis"               # Forming hypotheses
    EVALUATION = "evaluation"               # Evaluating options/results
    CONSTRAINT_ANALYSIS = "constraint_analysis"  # Analyzing constraints
    NEXT_STEP = "next_step"                # Determining next action


class ActionType(str, Enum):
    """Types of actions agents can execute."""
    MCP_CALL = "mcp_call"                  # Call to MCP server
    TOOL_USE = "tool_use"                  # Use external tool
    DELEGATION = "delegation"               # Delegate to another agent
    QUERY = "query"                        # Information query
    COMPUTATION = "computation"             # Perform calculation
    COMMUNICATION = "communication"         # Communicate with external system
    FILE_OPERATION = "file_operation"       # File/data manipulation
    API_CALL = "api_call"                  # External API call


class ReflectionType(str, Enum):
    """Types of self-reflection and critique."""
    SELF_CRITIQUE = "self_critique"         # Agent critiquing own performance
    PEER_REVIEW = "peer_review"            # Review from another agent
    OUTCOME_ANALYSIS = "outcome_analysis"   # Analysis of action outcomes
    STRATEGY_REVIEW = "strategy_review"     # Review of overall strategy
    ERROR_ANALYSIS = "error_analysis"       # Analysis of failures/errors
    IMPROVEMENT_SUGGESTION = "improvement_suggestion"  # Suggestions for improvement


class AgentDefinition(Base):
    """
    Agent definition template defining agent behavior and capabilities.
    
    Defines the template for agent behavior including capabilities, prompts,
    configuration, and integration settings. Multiple agent instances can
    be created from a single definition.
    """
    __tablename__ = "agent_definitions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    agent_type = Column(String(50), nullable=False)  # AgentType enum
    
    # Agent capabilities and configuration
    capabilities = Column(JSON, nullable=True)  # List of capabilities
    system_prompt = Column(Text)  # Base system prompt
    reasoning_prompt = Column(Text)  # Reasoning phase prompt
    action_prompt = Column(Text)  # Action phase prompt
    observation_prompt = Column(Text)  # Observation phase prompt
    reflection_prompt = Column(Text)  # Reflection phase prompt
    
    # Integration settings
    mcp_servers = Column(JSON, nullable=True)  # List of available MCP servers
    tool_config = Column(JSON, nullable=True)  # Tool configuration
    llm_config = Column(JSON, nullable=True)  # LLM model configuration
    
    # Behavioral parameters
    max_iterations = Column(Integer, default=10)  # Max ReAct loop iterations
    reflection_frequency = Column(Integer, default=3)  # How often to reflect
    delegation_threshold = Column(Float, default=0.7)  # When to delegate
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    instances = relationship("AgentInstance", back_populates="definition")


class AgentInstance(Base):
    """
    Running instance of an agent with state and configuration.
    
    Represents a specific running instance of an agent definition with
    current state, configuration overrides, and execution context.
    """
    __tablename__ = "agent_instances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    definition_id = Column(String(36), ForeignKey("agent_definitions.id"), nullable=False)
    name = Column(String(255), nullable=False)  # Instance name
    status = Column(String(50), default=AgentStatus.INACTIVE.value)
    
    # Instance-specific configuration
    config_overrides = Column(JSON, nullable=True)  # Override definition config
    current_context = Column(JSON, nullable=True)  # Current execution context
    
    # Runtime state
    current_run_id = Column(String(36), ForeignKey("agent_runs.id", use_alter=True))
    last_activity = Column(DateTime)
    error_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    
    # Resource management
    max_concurrent_runs = Column(Integer, default=1)
    priority = Column(Integer, default=5)  # 1-10 priority scale
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), ForeignKey("users.id"))
    
    # Relationships
    definition = relationship("AgentDefinition", back_populates="instances")
    runs = relationship("AgentRun", back_populates="agent_instance", foreign_keys="AgentRun.agent_instance_id")
    memory_entries = relationship("AgentMemory", back_populates="agent_instance")
    delegated_tasks = relationship("TaskDelegation", foreign_keys="TaskDelegation.manager_agent_id", back_populates="manager_agent")
    assigned_tasks = relationship("TaskDelegation", foreign_keys="TaskDelegation.worker_agent_id", back_populates="worker_agent")


class AgentRun(Base):
    """
    Execution session tracking agent workflow through ReAct loops.
    
    Tracks a single execution session of an agent, including all reasoning,
    actions, observations, and reflections performed during the run.
    """
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_instance_id = Column(String(36), ForeignKey("agent_instances.id"), nullable=False)
    
    # Run identification
    run_name = Column(String(255))
    goal = Column(Text, nullable=False)  # Primary goal for this run
    status = Column(String(50), default=RunStatus.STARTING.value)
    
    # Execution tracking
    current_iteration = Column(Integer, default=0)
    max_iterations = Column(Integer, default=10)
    
    # Phase tracking
    current_phase = Column(String(50))  # Current ReAct phase
    last_thought_id = Column(String(36))
    last_action_id = Column(String(36))
    last_observation_id = Column(String(36))
    
    # Results and outputs
    final_result = Column(JSON, nullable=True)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Performance metrics
    total_reasoning_time = Column(Float, default=0.0)  # seconds
    total_action_time = Column(Float, default=0.0)     # seconds
    total_observation_time = Column(Float, default=0.0) # seconds
    
    # Context and metadata
    input_context = Column(JSON, nullable=True)  # Initial context
    run_metadata = Column(JSON, nullable=True)   # Additional metadata
    
    # Timestamps
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    agent_instance = relationship("AgentInstance", back_populates="runs", foreign_keys=[agent_instance_id])
    thoughts = relationship("Thought", back_populates="run")
    actions = relationship("Action", back_populates="run")
    observations = relationship("Observation", back_populates="run")
    reflections = relationship("Reflection", back_populates="run")


class Thought(Base):
    """
    Reasoning step in ReAct loop with detailed thought process.
    
    Captures the reasoning phase of a ReAct loop, including the agent's
    thought process, analysis, planning, and decision making.
    """
    __tablename__ = "thoughts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.id"), nullable=False)
    
    # Thought classification
    thought_type = Column(String(50), nullable=False)  # ThoughtType enum
    iteration = Column(Integer, nullable=False)
    sequence = Column(Integer, nullable=False)  # Order within iteration
    
    # Thought content
    content = Column(Text, nullable=False)  # The actual thought/reasoning
    reasoning_chain = Column(JSON, nullable=True)  # Structured reasoning steps
    
    # Context and analysis
    current_state = Column(JSON, nullable=True)  # Agent's view of current state
    goal_progress = Column(JSON, nullable=True)  # Progress toward goal
    constraints = Column(JSON, nullable=True)    # Identified constraints
    options_considered = Column(JSON, nullable=True)  # Options analyzed
    
    # Decision making
    confidence_score = Column(Float)  # Confidence in reasoning (0-1)
    uncertainty_factors = Column(JSON, nullable=True)  # Sources of uncertainty
    assumptions = Column(JSON, nullable=True)  # Assumptions made
    
    # Performance metrics
    reasoning_time = Column(Float)  # Time spent reasoning (seconds)
    complexity_score = Column(Float)  # Complexity of reasoning (0-1)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    run = relationship("AgentRun", back_populates="thoughts")


class Action(Base):
    """
    Action step in ReAct loop with execution details and results.
    
    Captures the action phase of a ReAct loop, including the planned action,
    execution details, parameters, and immediate results.
    """
    __tablename__ = "actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.id"), nullable=False)
    
    # Action classification
    action_type = Column(String(50), nullable=False)  # ActionType enum
    iteration = Column(Integer, nullable=False)
    sequence = Column(Integer, nullable=False)  # Order within iteration
    
    # Action details
    name = Column(String(255), nullable=False)  # Action name/identifier
    description = Column(Text)  # Human-readable description
    
    # Execution parameters
    parameters = Column(JSON, nullable=True)  # Action parameters
    target_system = Column(String(255))  # Target system/service
    method = Column(String(255))  # Method/function called
    
    # Execution tracking
    execution_plan = Column(JSON, nullable=True)  # Planned execution steps
    status = Column(String(50), default="planned")  # planned, executing, completed, failed
    
    # Results
    result = Column(JSON, nullable=True)  # Action result/output
    error_details = Column(JSON, nullable=True)  # Error information if failed
    side_effects = Column(JSON, nullable=True)  # Observed side effects
    
    # Performance metrics
    execution_time = Column(Float)  # Time to execute (seconds)
    success = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    
    # Validation and verification
    expected_outcome = Column(JSON, nullable=True)  # Expected results
    actual_outcome = Column(JSON, nullable=True)    # Actual results
    validation_score = Column(Float)  # How well outcome matched expectation
    
    # Metadata
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    run = relationship("AgentRun", back_populates="actions")


class Observation(Base):
    """
    Observation step in ReAct loop capturing environment state and feedback.
    
    Captures the observation phase of a ReAct loop, including environmental
    feedback, state changes, and analysis of action outcomes.
    """
    __tablename__ = "observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.id"), nullable=False)
    
    # Observation classification
    iteration = Column(Integer, nullable=False)
    sequence = Column(Integer, nullable=False)  # Order within iteration
    observation_source = Column(String(255))  # Source of observation
    
    # Observation content
    content = Column(Text, nullable=False)  # Raw observation data
    structured_data = Column(JSON, nullable=True)  # Structured observation
    
    # State analysis
    environment_state = Column(JSON, nullable=True)  # Current environment state
    state_changes = Column(JSON, nullable=True)      # Detected state changes
    action_feedback = Column(JSON, nullable=True)    # Feedback on last action
    
    # Pattern recognition
    patterns_detected = Column(JSON, nullable=True)  # Identified patterns
    anomalies = Column(JSON, nullable=True)          # Detected anomalies
    trends = Column(JSON, nullable=True)             # Observed trends
    
    # Quality assessment
    reliability_score = Column(Float)  # Reliability of observation (0-1)
    completeness_score = Column(Float) # Completeness of observation (0-1)
    noise_level = Column(Float)        # Amount of noise in data (0-1)
    
    # Analysis metrics
    processing_time = Column(Float)    # Time to process observation
    complexity_score = Column(Float)   # Complexity of observation
    
    # Metadata
    observed_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    run = relationship("AgentRun", back_populates="observations")


class Reflection(Base):
    """
    Self-reflection and critique for continuous improvement.
    
    Captures self-reflection, peer review, and critique activities that
    help agents improve their performance and decision-making over time.
    """
    __tablename__ = "reflections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.id"), nullable=False)
    
    # Reflection classification
    reflection_type = Column(String(50), nullable=False)  # ReflectionType enum
    scope = Column(String(50))  # iteration, run, strategy, global
    target_iteration = Column(Integer)  # Which iteration is being reflected on
    
    # Reflection content
    content = Column(Text, nullable=False)  # Main reflection text
    insights = Column(JSON, nullable=True)  # Key insights discovered
    
    # Performance analysis
    strengths_identified = Column(JSON, nullable=True)    # What worked well
    weaknesses_identified = Column(JSON, nullable=True)   # What needs improvement
    mistakes_analysis = Column(JSON, nullable=True)       # Analysis of mistakes
    
    # Improvement suggestions
    suggestions = Column(JSON, nullable=True)             # Improvement suggestions
    strategy_adjustments = Column(JSON, nullable=True)    # Strategy changes
    learning_points = Column(JSON, nullable=True)         # Key learning points
    
    # Quality metrics
    self_critique_score = Column(Float)   # Quality of self-critique (0-1)
    insight_quality = Column(Float)       # Quality of insights (0-1)
    actionability = Column(Float)         # How actionable suggestions are (0-1)
    
    # Impact tracking
    implemented_suggestions = Column(JSON, nullable=True)  # Which suggestions were used
    improvement_impact = Column(Float)    # Measured improvement impact
    
    # Metadata
    reflection_time = Column(Float)       # Time spent reflecting
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    run = relationship("AgentRun", back_populates="reflections")


class AgentMemory(Base):
    """
    Persistent memory and context storage for agents across sessions.
    
    Provides long-term memory capabilities for agents, storing important
    context, learned patterns, and accumulated knowledge across runs.
    """
    __tablename__ = "agent_memory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_instance_id = Column(String(36), ForeignKey("agent_instances.id"), nullable=False)
    
    # Memory classification
    memory_type = Column(String(50), nullable=False)  # episodic, semantic, procedural
    category = Column(String(100))  # Category for organization
    importance = Column(Float, default=0.5)  # Importance score (0-1)
    
    # Memory content
    content = Column(Text, nullable=False)  # Memory content
    structured_data = Column(JSON, nullable=True)  # Structured memory data
    context = Column(JSON, nullable=True)  # Context when memory was formed
    
    # Associations and relationships
    related_memories = Column(JSON, nullable=True)  # IDs of related memories
    tags = Column(JSON, nullable=True)  # Tags for categorization
    keywords = Column(JSON, nullable=True)  # Keywords for search
    
    # Quality and reliability
    confidence_score = Column(Float, default=1.0)  # Confidence in memory
    verification_count = Column(Integer, default=0)  # Times verified
    accuracy_score = Column(Float, default=1.0)  # Measured accuracy
    
    # Usage tracking
    access_count = Column(Integer, default=0)  # Times accessed
    last_accessed = Column(DateTime)
    last_updated = Column(DateTime)
    
    # Lifecycle management
    expiry_date = Column(DateTime)  # When memory expires (if applicable)
    archived = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    source_run_id = Column(String(36), ForeignKey("agent_runs.id"))  # Run that created memory
    
    # Relationships
    agent_instance = relationship("AgentInstance", back_populates="memory_entries")


class TaskDelegation(Base):
    """
    Manager-worker task delegation and coordination tracking.
    
    Tracks task delegation from manager agents to worker agents,
    including delegation criteria, progress monitoring, and results.
    """
    __tablename__ = "task_delegations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Agent roles
    manager_agent_id = Column(String(36), ForeignKey("agent_instances.id"), nullable=False)
    worker_agent_id = Column(String(36), ForeignKey("agent_instances.id"), nullable=False)
    
    # Task details
    task_description = Column(Text, nullable=False)
    task_requirements = Column(JSON, nullable=True)  # Requirements and constraints
    delegation_criteria = Column(JSON, nullable=True)  # Why this agent was chosen
    
    # Execution tracking
    status = Column(String(50), default="assigned")  # assigned, accepted, in_progress, completed, failed
    priority = Column(Integer, default=5)  # Task priority
    deadline = Column(DateTime)
    
    # Progress monitoring
    progress_updates = Column(JSON, nullable=True)  # Progress reports
    checkpoints = Column(JSON, nullable=True)  # Defined checkpoints
    current_checkpoint = Column(String(255))
    
    # Results and feedback
    result = Column(JSON, nullable=True)  # Task result
    worker_feedback = Column(Text)  # Worker's feedback
    manager_evaluation = Column(JSON, nullable=True)  # Manager's evaluation
    
    # Performance metrics
    estimated_duration = Column(Float)  # Estimated time (hours)
    actual_duration = Column(Float)     # Actual time taken
    quality_score = Column(Float)       # Quality assessment (0-1)
    efficiency_score = Column(Float)    # Efficiency assessment (0-1)
    
    # Metadata
    delegated_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    manager_agent = relationship("AgentInstance", foreign_keys=[manager_agent_id], back_populates="delegated_tasks")
    worker_agent = relationship("AgentInstance", foreign_keys=[worker_agent_id], back_populates="assigned_tasks")