"""Code Reviewer Crew - Reviews code artifacts for quality and correctness."""

from crewai import Agent, Crew, Task
from crewai.tools import tool
from typing import Dict, List, Any


def _analyze_code_quality_impl(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Analyze code for quality issues (implementation).
    
    Args:
        code: The code to analyze
        language: Programming language
        
    Returns:
        Dictionary with quality analysis
    """
    issues = []
    score = 100
    
    # Basic quality checks
    lines = code.split('\n')
    
    # Check for very long lines
    for i, line in enumerate(lines):
        if len(line) > 120:
            issues.append({
                "line": i + 1,
                "severity": "minor",
                "message": f"Line too long ({len(line)} > 120 characters)"
            })
            score -= 2
    
    # Check for missing docstrings (Python)
    if language == "python":
        if "def " in code or "class " in code:
            if '"""' not in code and "'''" not in code:
                issues.append({
                    "line": 1,
                    "severity": "moderate",
                    "message": "Missing docstrings for functions/classes"
                })
                score -= 10
    
    # Check for potential security issues
    dangerous_patterns = ['eval(', 'exec(', 'os.system(', '__import__']
    for pattern in dangerous_patterns:
        if pattern in code:
            issues.append({
                "line": 0,
                "severity": "critical",
                "message": f"Potential security issue: use of {pattern}"
            })
            score -= 25
    
    return {
        "quality_score": max(0, score),
        "issues": issues,
        "total_lines": len(lines),
        "analyzable": True
    }


@tool
def analyze_code_quality(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Analyze code for quality issues.
    
    Args:
        code: The code to analyze
        language: Programming language
        
    Returns:
        Dictionary with quality analysis
    """
    return _analyze_code_quality_impl(code, language)


def create_code_reviewer_crew(artifacts: List[Dict], criteria: Dict) -> Crew:
    """
    Create a code reviewer crew instance.
    
    Args:
        artifacts: List of artifacts to review
        criteria: Review criteria
        
    Returns:
        Configured Crew instance
    """
    
    # Senior Code Reviewer Agent
    reviewer = Agent(
        role="Senior Code Reviewer",
        goal="Review code artifacts for correctness, quality, completeness, and security",
        backstory="""You are a senior software engineer with 15+ years of experience 
        reviewing code. You have a keen eye for potential bugs, security issues, and 
        code quality problems. You provide constructive feedback that helps developers 
        improve their code.""",
        tools=[analyze_code_quality],
        verbose=True,
        allow_delegation=False
    )
    
    # Quality Assurance Agent
    qa_agent = Agent(
        role="Quality Assurance Engineer",
        goal="Verify that code meets all requirements and has proper test coverage",
        backstory="""You are a QA engineer specialized in ensuring code quality.
        You check that all requirements are met, edge cases are handled, and tests
        are comprehensive.""",
        verbose=True,
        allow_delegation=False
    )
    
    # Prepare artifact summaries
    artifact_summary = "\n\n".join([
        f"Artifact {i+1}: {a.get('name', 'unnamed')}\n"
        f"Type: {a.get('type', 'unknown')}\n"
        f"Content: {a.get('content', '')[:500]}..."
        for i, a in enumerate(artifacts[:5])  # Limit to first 5
    ])
    
    # Review Task
    review_task = Task(
        description=f"""Review the following code artifacts:

{artifact_summary}

Review Criteria:
- Correctness: {criteria.get('correctness', 'Code should work correctly')}
- Completeness: {criteria.get('completeness', 'All requirements addressed')}
- Quality: {criteria.get('quality', 'Code should be clean and maintainable')}
- Tests: {criteria.get('tests', 'Unit tests should exist and pass')}

For each artifact:
1. Check if the code is correct and follows best practices
2. Identify any bugs, security issues, or code smells
3. Verify that it meets the stated requirements
4. Check for edge cases and error handling

Provide your review in this format:
APPROVED: yes/no
FEEDBACK: Overall feedback (2-3 sentences)
ISSUES: List of specific issues (if any)
SUGGESTIONS: Recommended improvements
""",
        agent=reviewer,
        expected_output="A structured review with approval status, feedback, issues, and suggestions"
    )
    
    # QA Verification Task
    qa_task = Task(
        description=f"""Verify the quality assurance aspects of these artifacts:

{artifact_summary}

Check for:
1. Test coverage - Are there unit tests?
2. Edge cases - Are edge cases handled?
3. Error handling - Are errors handled gracefully?
4. Documentation - Is the code documented?

Provide a QA report with pass/fail status and specific issues found.
""",
        agent=qa_agent,
        expected_output="A QA report with pass/fail status and list of issues",
        context=[review_task]
    )
    
    # Create and return crew
    crew = Crew(
        agents=[reviewer, qa_agent],
        tasks=[review_task, qa_task],
        verbose=True
    )
    
    return crew


def parse_review_output(output: str) -> Dict[str, Any]:
    """
    Parse the crew output into structured review data.
    
    Args:
        output: Raw crew output text
        
    Returns:
        Structured review data
    """
    # Default values
    result = {
        "approved": False,
        "feedback": "",
        "issues": [],
        "suggestions": []
    }
    
    # Simple parsing logic
    output_lower = output.lower()
    
    # Check approval
    if "approved: yes" in output_lower or "approval: yes" in output_lower:
        result["approved"] = True
    elif "approved: no" in output_lower or "approval: no" in output_lower:
        result["approved"] = False
    else:
        # If no explicit approval but no critical issues, approve
        if "critical" not in output_lower and "fail" not in output_lower:
            result["approved"] = True
    
    # Extract feedback
    if "FEEDBACK:" in output:
        feedback_start = output.index("FEEDBACK:") + len("FEEDBACK:")
        feedback_end = output.find("\n\n", feedback_start)
        if feedback_end == -1:
            feedback_end = output.find("ISSUES:", feedback_start)
        if feedback_end == -1:
            feedback_end = len(output)
        result["feedback"] = output[feedback_start:feedback_end].strip()
    else:
        # Use first few sentences as feedback
        result["feedback"] = output[:300].strip()
    
    # Extract issues
    if "ISSUES:" in output:
        issues_start = output.index("ISSUES:") + len("ISSUES:")
        issues_end = output.find("SUGGESTIONS:", issues_start)
        if issues_end == -1:
            issues_end = len(output)
        issues_text = output[issues_start:issues_end].strip()
        
        # Split by lines and extract bullet points
        for line in issues_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                result["issues"].append(line[1:].strip())
    
    # Extract suggestions
    if "SUGGESTIONS:" in output:
        suggestions_start = output.index("SUGGESTIONS:") + len("SUGGESTIONS:")
        suggestions_text = output[suggestions_start:].strip()
        
        for line in suggestions_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                result["suggestions"].append(line[1:].strip())
    
    return result
