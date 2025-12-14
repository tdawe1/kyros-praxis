"""
Coder Agent: Generates code based on approved specifications.

PRD Requirements:
- "generates actual code for each component"
- "creates file structure"
- "adds comments/documentation"
"""

import logging
from typing import Dict, Any, Optional, List

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = Task = Crew = Process = None


logger = logging.getLogger(__name__)


def create_coder_agent(llm_config: Optional[Dict] = None) -> Optional[Agent]:
    """
    Create agent that writes code from specifications.
    
    Args:
        llm_config: Optional LLM configuration override
        
    Returns:
        Agent instance or None if CrewAI not available
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, cannot create coder agent")
        return None
    
    return Agent(
        role="Senior Software Engineer",
        goal="Generate clean, well-documented, production-ready code from specifications",
        backstory="""You are a senior software engineer with expertise across multiple 
        languages and frameworks. You write code that is:
        - Clean and readable
        - Well-documented with docstrings and comments
        - Following best practices and design patterns
        - Properly error-handled
        - Testable and maintainable
        - Secure and performant
        
        You don't just write code that works - you write code that other developers 
        will enjoy reading and maintaining. You think about edge cases, validation, 
        and the developer experience.""",
        verbose=True,
        allow_delegation=False,
        tools=[],
    )


def create_coding_task(specification: Dict, agent: Agent) -> Optional[Task]:
    """
    Create task for generating code from specification.
    
    Args:
        specification: The approved specification from planner
        agent: The coder agent
        
    Returns:
        Task instance or None if CrewAI not available
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, cannot create coding task")
        return None
    
    # Format specification nicely
    import json
    spec_str = json.dumps(specification, indent=2)
    
    return Task(
        description=f"""
        Generate production-ready code based on this specification:
        
        SPECIFICATION:
        {spec_str}
        
        For each component in the specification:
        
        1. WRITE COMPLETE CODE
           - Implement all functionality
           - Include proper imports
           - Use appropriate data structures
           - Follow language conventions
        
        2. ADD DOCUMENTATION
           - File-level docstrings explaining purpose
           - Function/class docstrings with parameters and returns
           - Inline comments for complex logic
           - Usage examples where helpful
        
        3. ERROR HANDLING
           - Validate inputs
           - Handle edge cases
           - Provide meaningful error messages
           - Use try/except appropriately
        
        4. BEST PRACTICES
           - Follow DRY principle
           - Use meaningful variable names
           - Keep functions focused and small
           - Apply SOLID principles
        
        5. MAKE IT TESTABLE
           - Separate concerns
           - Use dependency injection where appropriate
           - Avoid hard-coded values
        
        Return the code as a structured JSON with this format:
        {{
            "files": [
                {{
                    "path": "relative/path/to/file.py",
                    "content": "... complete file content ...",
                    "description": "Brief description of what this file does"
                }},
                ...
            ],
            "setup_instructions": "How to install dependencies and run",
            "notes": "Any important notes for the developer"
        }}
        
        Ensure all code is complete, functional, and ready to run.
        """,
        expected_output="""Valid JSON containing all code files with their full content, 
        setup instructions, and relevant notes. Code should be production-ready.""",
        agent=agent,
    )


async def run_coder(
    specification: Dict,
    project_id: Optional[str] = None,
    llm_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Run coder agent to generate code from specification.
    
    Args:
        specification: The approved specification
        project_id: Optional project ID for tracking
        llm_config: Optional LLM configuration
        
    Returns:
        Dictionary containing:
        - files: List of generated files
        - status: "completed" or "failed"
        - error: Error message if failed
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, using simulation mode")
        return {
            "status": "completed",
            "files": [
                {
                    "path": "main.py",
                    "content": "# Simulated code\nprint('Hello from simulation')",
                    "description": "Main entry point"
                }
            ],
            "setup_instructions": "This is a simulation. Install CrewAI for real code generation.",
            "simulation": True
        }
    
    try:
        logger.info(f"Starting coder agent for project: {project_id}")
        
        # Create agent and task
        agent = create_coder_agent(llm_config)
        task = create_coding_task(specification, agent)
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute
        result = crew.kickoff()
        
        logger.info(f"Coder agent completed for project: {project_id}")
        
        # Parse result
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
            "code_output": output,
            "project_id": project_id,
        }
        
    except Exception as e:
        logger.error(f"Error in coder agent: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "project_id": project_id,
        }


# Code generation helpers

def parse_code_output(output: Any) -> Dict[str, Any]:
    """
    Parse coder agent output into structured format.
    
    Args:
        output: Raw output from coder agent
        
    Returns:
        Parsed code structure
    """
    import json
    
    # Try to parse as JSON
    if isinstance(output, str):
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            # Fallback: treat as single file
            return {
                "files": [{
                    "path": "output.txt",
                    "content": output,
                    "description": "Generated content"
                }],
                "setup_instructions": "Review the generated content",
                "notes": "Output was not in expected JSON format"
            }
    
    if isinstance(output, dict):
        return output
    
    return {
        "files": [],
        "error": "Unable to parse coder output"
    }


def validate_code_output(output: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate that code output has expected structure.
    
    Args:
        output: Parsed code output
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(output, dict):
        return False, "Output must be a dictionary"
    
    if "files" not in output:
        return False, "Output must contain 'files' key"
    
    files = output["files"]
    if not isinstance(files, list):
        return False, "'files' must be a list"
    
    for i, file_obj in enumerate(files):
        if not isinstance(file_obj, dict):
            return False, f"File {i} must be a dictionary"
        
        if "path" not in file_obj:
            return False, f"File {i} missing 'path' field"
        
        if "content" not in file_obj:
            return False, f"File {i} missing 'content' field"
    
    return True, None


def get_file_tree(files: List[Dict]) -> Dict[str, Any]:
    """
    Build a tree structure from flat file list.
    
    Args:
        files: List of file dictionaries with 'path' keys
        
    Returns:
        Nested directory tree
    """
    tree = {}
    
    for file_obj in files:
        path = file_obj["path"]
        parts = path.split("/")
        
        current = tree
        for part in parts[:-1]:  # All but last (directories)
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Last part (filename)
        current[parts[-1]] = {
            "type": "file",
            "size": len(file_obj.get("content", "")),
            "description": file_obj.get("description", "")
        }
    
    return tree


def count_code_stats(files: List[Dict]) -> Dict[str, int]:
    """
    Calculate statistics about generated code.
    
    Args:
        files: List of generated files
        
    Returns:
        Statistics dictionary
    """
    total_files = len(files)
    total_lines = 0
    total_chars = 0
    
    file_types = {}
    
    for file_obj in files:
        content = file_obj.get("content", "")
        total_chars += len(content)
        total_lines += content.count("\n")
        
        # Get file extension
        path = file_obj.get("path", "")
        ext = path.split(".")[-1] if "." in path else "unknown"
        file_types[ext] = file_types.get(ext, 0) + 1
    
    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "total_chars": total_chars,
        "file_types": file_types
    }
