"""
Tester Agent: Reviews code and creates tests.

PRD Requirements:
- "reviews generated code"
- "creates unit tests"
- "validates functionality"
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


def create_tester_agent(llm_config: Optional[Dict] = None) -> Optional[Agent]:
    """
    Create agent that reviews code and writes tests.
    
    Args:
        llm_config: Optional LLM configuration override
        
    Returns:
        Agent instance or None if CrewAI not available
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, cannot create tester agent")
        return None
    
    return Agent(
        role="QA Engineer & Test Specialist",
        goal="Review code for issues and create comprehensive test coverage",
        backstory="""You are a meticulous QA engineer with a knack for finding edge 
        cases and potential bugs. You have expertise in:
        - Code review best practices
        - Unit testing patterns
        - Integration testing
        - Test-driven development
        - Security vulnerabilities
        - Performance considerations
        
        You don't just check if code works - you ensure it works correctly in all 
        scenarios, handles errors gracefully, and will continue working as the codebase 
        evolves. You write tests that are clear, maintainable, and provide good coverage.""",
        verbose=True,
        allow_delegation=False,
        tools=[],
    )


def create_testing_task(
    code_files: Dict,
    specification: Dict,
    agent: Agent
) -> Optional[Task]:
    """
    Create task for reviewing code and generating tests.
    
    Args:
        code_files: Generated code from coder agent
        specification: Original specification
        agent: The tester agent
        
    Returns:
        Task instance or None if CrewAI not available
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, cannot create testing task")
        return None
    
    import json
    code_str = json.dumps(code_files, indent=2)
    spec_str = json.dumps(specification, indent=2)
    
    return Task(
        description=f"""
        Review this generated code and create comprehensive tests:
        
        ORIGINAL SPECIFICATION:
        {spec_str}
        
        GENERATED CODE:
        {code_str}
        
        Your tasks:
        
        1. CODE REVIEW
           - Check if code matches specification
           - Look for bugs and logic errors
           - Identify security vulnerabilities
           - Check error handling
           - Verify input validation
           - Review code quality and style
        
        2. IDENTIFY ISSUES
           - Critical: Bugs that will cause failures
           - High: Security vulnerabilities, missing error handling
           - Medium: Code quality issues, missing validation
           - Low: Style issues, minor improvements
        
        3. CREATE UNIT TESTS
           - Test happy path (normal operation)
           - Test edge cases
           - Test error conditions
           - Test input validation
           - Test boundary conditions
        
        4. CREATE INTEGRATION TESTS (if applicable)
           - Test component interactions
           - Test data flow
           - Test API endpoints
        
        5. SUGGEST IMPROVEMENTS
           - Performance optimizations
           - Code refactoring opportunities
           - Better error messages
           - Additional validation
        
        Return results as JSON:
        {{
            "review": {{
                "matches_spec": true/false,
                "overall_quality": "excellent/good/fair/poor",
                "issues": [
                    {{
                        "severity": "critical/high/medium/low",
                        "file": "path/to/file.py",
                        "line": 42,
                        "description": "Description of issue",
                        "suggestion": "How to fix"
                    }},
                    ...
                ]
            }},
            "tests": [
                {{
                    "file": "tests/test_something.py",
                    "content": "... complete test file content ...",
                    "description": "What this test file covers"
                }},
                ...
            ],
            "test_coverage": {{
                "estimated_coverage": "85%",
                "untested_areas": ["area1", "area2"]
            }},
            "recommendations": [
                "Recommendation 1",
                "Recommendation 2"
            ]
        }}
        
        Be thorough but constructive. Focus on helping improve the code.
        """,
        expected_output="""Valid JSON containing code review with issues, complete test 
        files, coverage estimation, and recommendations. Tests should be runnable and 
        comprehensive.""",
        agent=agent,
    )


async def run_tester(
    code_files: Dict,
    specification: Dict,
    project_id: Optional[str] = None,
    llm_config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Run tester agent to review code and create tests.
    
    Args:
        code_files: Generated code from coder
        specification: Original specification
        project_id: Optional project ID for tracking
        llm_config: Optional LLM configuration
        
    Returns:
        Dictionary containing:
        - review: Code review results
        - tests: Generated test files
        - status: "completed" or "failed"
        - error: Error message if failed
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, using simulation mode")
        return {
            "status": "completed",
            "review": {
                "matches_spec": True,
                "overall_quality": "good",
                "issues": []
            },
            "tests": [
                {
                    "file": "tests/test_main.py",
                    "content": "# Simulated test\ndef test_example():\n    assert True",
                    "description": "Example test"
                }
            ],
            "test_coverage": {
                "estimated_coverage": "0%",
                "untested_areas": ["everything"]
            },
            "recommendations": ["Install CrewAI for real code review"],
            "simulation": True
        }
    
    try:
        logger.info(f"Starting tester agent for project: {project_id}")
        
        # Create agent and task
        agent = create_tester_agent(llm_config)
        task = create_testing_task(code_files, specification, agent)
        
        # Create crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute
        result = crew.kickoff()
        
        logger.info(f"Tester agent completed for project: {project_id}")
        
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
            "test_output": output,
            "project_id": project_id,
        }
        
    except Exception as e:
        logger.error(f"Error in tester agent: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "project_id": project_id,
        }


# Testing helpers

def parse_test_output(output: Any) -> Dict[str, Any]:
    """
    Parse tester agent output into structured format.
    
    Args:
        output: Raw output from tester agent
        
    Returns:
        Parsed test results
    """
    import json
    
    # Try to parse as JSON
    if isinstance(output, str):
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {
                "review": {
                    "matches_spec": False,
                    "overall_quality": "unknown",
                    "issues": []
                },
                "tests": [],
                "error": "Unable to parse tester output",
                "raw_output": output
            }
    
    if isinstance(output, dict):
        return output
    
    return {
        "review": {"issues": []},
        "tests": [],
        "error": "Invalid output format"
    }


def validate_test_output(output: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate that test output has expected structure.
    
    Args:
        output: Parsed test output
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(output, dict):
        return False, "Output must be a dictionary"
    
    if "review" not in output:
        return False, "Output must contain 'review' key"
    
    if "tests" not in output:
        return False, "Output must contain 'tests' key"
    
    review = output["review"]
    if not isinstance(review, dict):
        return False, "'review' must be a dictionary"
    
    tests = output["tests"]
    if not isinstance(tests, list):
        return False, "'tests' must be a list"
    
    return True, None


def count_issues_by_severity(review: Dict) -> Dict[str, int]:
    """
    Count code issues by severity level.
    
    Args:
        review: Code review results
        
    Returns:
        Counts by severity
    """
    issues = review.get("issues", [])
    
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    for issue in issues:
        severity = issue.get("severity", "low")
        if severity in counts:
            counts[severity] += 1
    
    return counts


def has_blocking_issues(review: Dict) -> bool:
    """
    Check if review has critical or high severity issues.
    
    Args:
        review: Code review results
        
    Returns:
        True if blocking issues exist
    """
    counts = count_issues_by_severity(review)
    return counts["critical"] > 0 or counts["high"] > 0


def generate_test_summary(output: Dict) -> str:
    """
    Generate human-readable summary of test results.
    
    Args:
        output: Parsed test output
        
    Returns:
        Summary string
    """
    review = output.get("review", {})
    tests = output.get("tests", [])
    coverage = output.get("test_coverage", {})
    
    matches_spec = review.get("matches_spec", False)
    quality = review.get("overall_quality", "unknown")
    issue_counts = count_issues_by_severity(review)
    
    summary_parts = [
        f"Code Quality: {quality.upper()}",
        f"Matches Specification: {'YES' if matches_spec else 'NO'}",
        f"Issues Found: {sum(issue_counts.values())} total",
        f"  - Critical: {issue_counts['critical']}",
        f"  - High: {issue_counts['high']}",
        f"  - Medium: {issue_counts['medium']}",
        f"  - Low: {issue_counts['low']}",
        f"Test Files Generated: {len(tests)}",
        f"Estimated Coverage: {coverage.get('estimated_coverage', 'unknown')}"
    ]
    
    return "\n".join(summary_parts)


def extract_critical_issues(review: Dict) -> List[Dict]:
    """
    Extract only critical and high severity issues.
    
    Args:
        review: Code review results
        
    Returns:
        List of critical/high issues
    """
    issues = review.get("issues", [])
    return [
        issue for issue in issues
        if issue.get("severity") in ["critical", "high"]
    ]
