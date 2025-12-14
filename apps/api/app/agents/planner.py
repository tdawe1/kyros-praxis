"""
Planner Agent: Analyzes user prompts and creates structured specifications.

PRD Requirements:
- "Planner Agent refines the user's prompt into a structured plan"
- "outlines the components needed"
- "creates a pseudo-design document"
- "user can review and approve before coding starts"
"""

import logging
from typing import Dict, Any, Optional

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Task = Crew = Process = None


logger = logging.getLogger(__name__)


def create_planner_agent(llm_config: Optional[Dict] = None) -> Optional[Agent]:
    """
    Create agent that analyzes prompts and creates specifications.
    
    Args:
        llm_config: Optional LLM configuration override
        
    Returns:
        Agent instance or None if CrewAI not available
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, cannot create planner agent")
        return None
    
    return Agent(
        role="Software Architect",
        goal="Analyze user requirements and create detailed, actionable specifications",
        backstory="""You are an experienced software architect with 15+ years of 
        experience. You excel at understanding project requirements, asking clarifying 
        questions when needed, and breaking down complex projects into structured, 
        implementable plans. You think about scalability, maintainability, and best 
        practices. You create specifications that developers can immediately use to 
        start coding.""",
        verbose=True,
        allow_delegation=False,
        # Tools can be added here (e.g., web search, documentation lookup)
        tools=[],
    )


def create_planning_task(user_prompt: str, agent: Agent) -> Optional[Task]:
    """
    Create task for analyzing prompt and generating specification.
    
    Args:
        user_prompt: The user's detailed prompt
        agent: The planner agent
        
    Returns:
        Task instance or None if CrewAI not available
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, cannot create planning task")
        return None
    
    return Task(
        description=f"""
        Analyze this user requirement and create a detailed technical specification:
        
        USER PROMPT:
        {user_prompt}
        
        Create a comprehensive specification including:
        
        1. PURPOSE & OVERVIEW
           - What is being built and why
           - Target users and use cases
           - Success criteria
        
        2. COMPONENTS & ARCHITECTURE
           - List of major components/modules
           - How they interact
           - Data flow diagram (text description)
        
        3. TECHNOLOGY STACK
           - Recommended languages and frameworks
           - Databases and storage
           - External services/APIs needed
           - Justification for each choice
        
        4. FILE STRUCTURE
           - Proposed project organization
           - Directory layout
           - Key files and their purposes
        
        5. DEPENDENCIES
           - External libraries needed
           - Version requirements
           - Installation requirements
        
        6. DATA MODELS
           - Database schemas
           - API request/response formats
           - Key data structures
        
        7. IMPLEMENTATION PLAN
           - Break down into phases
           - Suggested implementation order
           - Critical path items
        
        8. TESTING CONSIDERATIONS
           - What needs to be tested
           - Edge cases to consider
           - Integration points
        
        9. POTENTIAL CHALLENGES
           - Technical risks
           - Complexity areas
           - Suggested mitigations
        
        Format the output as valid JSON with this structure:
        {{
            "purpose": "...",
            "components": [...],
            "technology": {{...}},
            "file_structure": {{...}},
            "dependencies": [...],
            "data_models": {{...}},
            "implementation_plan": [...],
            "testing_considerations": [...],
            "challenges": [...]
        }}
        
        Be specific and actionable. The coder agent will use this to generate code.
        """,
        expected_output="""Detailed technical specification in valid JSON format with 
        all required sections filled out. The specification should be complete enough 
        that a developer can start coding immediately without additional questions.""",
        agent=agent,
    )


async def run_planner(
    user_prompt: str, 
    project_id: Optional[str] = None,
    llm_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Run planner agent to analyze prompt and create specification.
    
    PRD: "user can review and approve before coding starts"
    
    Args:
        user_prompt: The user's detailed prompt
        project_id: Optional project ID for tracking
        llm_config: Optional LLM configuration
        
    Returns:
        Dictionary containing:
        - specification: The generated spec (JSON)
        - status: "completed" or "failed"
        - error: Error message if failed
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, using simulation mode")
        return {
            "status": "completed",
            "specification": {
                "purpose": f"Simulated specification for: {user_prompt[:100]}...",
                "components": ["component1", "component2"],
                "technology": {"language": "python", "framework": "fastapi"},
                "note": "This is a simulation. Install CrewAI for real planning."
            },
            "simulation": True
        }
    
    try:
        logger.info(f"Starting planner agent for project: {project_id}")
        
        # Create agent and task
        agent = create_planner_agent(llm_config)
        task = create_planning_task(user_prompt, agent)
        
        # Create crew with single agent
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute
        result = crew.kickoff()
        
        logger.info(f"Planner agent completed for project: {project_id}")
        
        # Parse result
        # Note: CrewAI returns various formats depending on version
        # We'll try to extract the output
        if hasattr(result, 'raw'):
            output = result.raw
        elif hasattr(result, 'output'):
            output = result.output
        elif isinstance(result, dict):
            output = result.get('output', result)
        else:
            output = str(result)
        
        return {
            "status": "completed",
            "specification": output,
            "project_id": project_id,
        }
        
    except Exception as e:
        logger.error(f"Error in planner agent: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "project_id": project_id,
        }


# Validation helpers

def validate_specification(spec: Any) -> tuple[bool, Optional[str]]:
    """
    Validate that a specification has all required fields.
    
    Args:
        spec: The specification to validate (dict or JSON string)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    import json
    
    # Parse if string
    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
        except json.JSONDecodeError:
            return False, "Specification is not valid JSON"
    
    if not isinstance(spec, dict):
        return False, "Specification must be a dictionary"
    
    # Required fields
    required_fields = [
        "purpose",
        "components", 
        "technology",
        "file_structure",
        "dependencies"
    ]
    
    missing = [field for field in required_fields if field not in spec]
    
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    
    return True, None


def extract_key_info(spec: Dict) -> Dict[str, Any]:
    """
    Extract key information from specification for quick display.
    
    Args:
        spec: The full specification
        
    Returns:
        Dictionary with key info
    """
    return {
        "purpose": spec.get("purpose", "")[:200],  # First 200 chars
        "num_components": len(spec.get("components", [])),
        "technology": spec.get("technology", {}).get("language", "unknown"),
        "complexity": _estimate_complexity(spec),
    }


def _estimate_complexity(spec: Dict) -> str:
    """Estimate project complexity based on specification."""
    num_components = len(spec.get("components", []))
    num_dependencies = len(spec.get("dependencies", []))
    
    if num_components <= 3 and num_dependencies <= 5:
        return "simple"
    elif num_components <= 8 and num_dependencies <= 15:
        return "moderate"
    else:
        return "complex"
