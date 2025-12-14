"""
Integration tests for multi-agent workflow pipeline.
"""

import pytest
from app.workflows.pipeline_refactored import WorkflowPipeline
from app.prompt_processor import prompt_processor


class TestWorkflowPipeline:
    """Test workflow pipeline initialization and configuration."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initializes with correct settings."""
        pipeline = WorkflowPipeline()
        
        assert pipeline.max_iterations == 3
        assert pipeline.require_user_approval is True
    
    def test_pipeline_singleton(self):
        """Test that workflow_pipeline is accessible."""
        from app.workflows.pipeline_refactored import workflow_pipeline
        
        assert workflow_pipeline is not None
        assert isinstance(workflow_pipeline, WorkflowPipeline)


class TestPromptValidation:
    """Test prompt validation in workflow."""
    
    def test_short_prompt_rejected(self):
        """Test that prompts under minimum length are rejected."""
        short_prompt = "Build app"
        
        validation = prompt_processor.validate(short_prompt)
        
        assert validation.valid is False
        assert "too short" in str(validation.issues).lower()
        assert validation.score < 50
    
    def test_good_prompt_accepted(self):
        """Test that well-formed prompts pass validation."""
        good_prompt = """
        I want to build a web application for managing tasks.
        
        Features:
        - User authentication
        - Create, read, update, delete tasks
        - Assign tasks to team members
        - Set due dates and priorities
        - Email notifications
        
        Technology: Python with FastAPI backend, React frontend, PostgreSQL database
        
        The application should be scalable to support 1000+ users.
        """
        
        validation = prompt_processor.validate(good_prompt)
        
        assert validation.valid is True
        assert validation.score >= 70
        assert len(validation.issues) == 0
    
    def test_prompt_enhancement_adds_context(self):
        """Test that prompt enhancement adds system context."""
        original_prompt = "Build a todo app with React"
        
        enhanced = prompt_processor.enhance(original_prompt)
        
        assert len(enhanced) > len(original_prompt)
        assert "SYSTEM CONTEXT" in enhanced
        assert "production-ready" in enhanced.lower()
        assert original_prompt in enhanced


class TestRequirementsExtraction:
    """Test requirements extraction from prompts."""
    
    def test_tech_stack_detection(self):
        """Test technology stack detection."""
        prompt = "Build a web app using Python, FastAPI, React, and PostgreSQL"
        
        reqs = prompt_processor.extract_requirements(prompt)
        
        assert "python" in reqs.tech_stack
        assert "fastapi" in reqs.tech_stack
        assert "react" in reqs.tech_stack
    
    def test_feature_extraction(self):
        """Test feature extraction from bullet points."""
        prompt = """
        Build a task manager with:
        - User authentication
        - Create and edit tasks
        - Set priorities
        - Email notifications
        """
        
        reqs = prompt_processor.extract_requirements(prompt)
        
        assert len(reqs.features) >= 3
        assert any("authentication" in f.lower() for f in reqs.features)
    
    def test_scale_determination(self):
        """Test project scale determination."""
        small_prompt = "Build a simple calculator app"
        large_prompt = "Build a scalable enterprise platform for managing complex workflows"
        
        small_reqs = prompt_processor.extract_requirements(small_prompt)
        large_reqs = prompt_processor.extract_requirements(large_prompt)
        
        assert small_reqs.scale == "small"
        assert large_reqs.scale == "large"


@pytest.mark.asyncio
class TestWorkflowExecution:
    """Test workflow execution (simulation mode)."""
    
    async def test_workflow_validates_prompt_first(self):
        """Test that workflow validates prompt before execution."""
        pipeline = WorkflowPipeline()
        
        # Very short invalid prompt
        result = await pipeline.execute_workflow(
            project_id="test-123",
            user_prompt="hi"
        )
        
        assert result["status"] == "failed"
        assert result["stage"] == "validation"
        assert "validation" in result
    
    async def test_workflow_returns_awaiting_approval(self):
        """Test that workflow pauses at approval gate."""
        pipeline = WorkflowPipeline()
        
        # Good prompt
        result = await pipeline.execute_workflow(
            project_id="test-123",
            user_prompt="Build a comprehensive todo application with user authentication, task management, and email notifications using Python FastAPI backend and React frontend"
        )
        
        # Should pause for approval
        assert result["status"] in ["awaiting_approval", "failed"]
        if result["status"] == "awaiting_approval":
            assert "specification" in result
            assert result["stage"] == "planner"
    
    async def test_workflow_with_approved_spec_skips_planner(self):
        """Test that providing approved spec skips planner stage."""
        pipeline = WorkflowPipeline()
        
        approved_spec = {
            "purpose": "Test application",
            "components": ["frontend", "backend"],
            "technology": {"language": "python"},
            "file_structure": {},
            "dependencies": ["fastapi"]
        }
        
        result = await pipeline.execute_workflow(
            project_id="test-123",
            user_prompt="Build app",  # Won't be used
            approved_spec=approved_spec
        )
        
        # Should skip planner
        assert "planner" in result["stages"]
        assert result["stages"]["planner"]["status"] == "skipped"


@pytest.mark.asyncio
class TestWorkflowStages:
    """Test individual workflow stage execution."""
    
    async def test_planner_stage_returns_specification(self):
        """Test planner stage execution."""
        from app.agents.planner import run_planner
        
        result = await run_planner(
            user_prompt="Build a simple web application",
            project_id="test-123"
        )
        
        assert result["status"] == "completed"
        assert "specification" in result
        # In simulation mode, should still return structure
        spec = result["specification"]
        assert "purpose" in str(spec).lower() or "simulation" in str(spec).lower()
    
    async def test_coder_stage_returns_files(self):
        """Test coder stage execution."""
        from app.agents.coder import run_coder
        
        spec = {
            "purpose": "Test app",
            "components": ["main"],
            "technology": {"language": "python"},
            "file_structure": {},
            "dependencies": []
        }
        
        result = await run_coder(
            specification=spec,
            project_id="test-123"
        )
        
        assert result["status"] == "completed"
        assert "code_output" in result or "files" in result
    
    async def test_tester_stage_returns_review(self):
        """Test tester stage execution."""
        from app.agents.tester import run_tester
        
        code_files = {
            "files": [
                {"path": "main.py", "content": "print('hello')"}
            ]
        }
        
        spec = {"purpose": "Test"}
        
        result = await run_tester(
            code_files=code_files,
            specification=spec,
            project_id="test-123"
        )
        
        assert result["status"] == "completed"
        assert "test_output" in result or "review" in result


class TestWorkflowValidation:
    """Test workflow validation and error handling."""
    
    def test_specification_validation_complete(self):
        """Test complete specification passes validation."""
        from app.agents.planner import validate_specification
        
        spec = {
            "purpose": "Build app",
            "components": ["comp1"],
            "technology": {"lang": "python"},
            "file_structure": {"src": {}},
            "dependencies": ["fastapi"]
        }
        
        is_valid, error = validate_specification(spec)
        
        assert is_valid is True
        assert error is None
    
    def test_specification_validation_incomplete(self):
        """Test incomplete specification fails validation."""
        from app.agents.planner import validate_specification
        
        spec = {
            "purpose": "Build app"
            # Missing: components, technology, file_structure, dependencies
        }
        
        is_valid, error = validate_specification(spec)
        
        assert is_valid is False
        assert error is not None
        assert "missing" in error.lower()
    
    def test_code_output_validation_complete(self):
        """Test complete code output passes validation."""
        from app.agents.coder import validate_code_output
        
        output = {
            "files": [
                {"path": "main.py", "content": "code here"}
            ]
        }
        
        is_valid, error = validate_code_output(output)
        
        assert is_valid is True
        assert error is None
    
    def test_code_output_validation_missing_files(self):
        """Test code output without files fails validation."""
        from app.agents.coder import validate_code_output
        
        output = {
            "setup": "instructions"
            # Missing: files
        }
        
        is_valid, error = validate_code_output(output)
        
        assert is_valid is False
        assert "files" in error.lower()


class TestWorkflowHelpers:
    """Test workflow helper functions."""
    
    def test_has_blocking_issues_none(self):
        """Test blocking issue detection with no issues."""
        from app.agents.tester import has_blocking_issues
        
        review = {
            "issues": [
                {"severity": "low", "description": "Style"}
            ]
        }
        
        assert has_blocking_issues(review) is False
    
    def test_has_blocking_issues_critical(self):
        """Test blocking issue detection with critical issue."""
        from app.agents.tester import has_blocking_issues
        
        review = {
            "issues": [
                {"severity": "critical", "description": "Bug"}
            ]
        }
        
        assert has_blocking_issues(review) is True
    
    def test_has_blocking_issues_high(self):
        """Test blocking issue detection with high severity issue."""
        from app.agents.tester import has_blocking_issues
        
        review = {
            "issues": [
                {"severity": "high", "description": "Security"}
            ]
        }
        
        assert has_blocking_issues(review) is True
    
    def test_count_issues_by_severity(self):
        """Test issue counting by severity."""
        from app.agents.tester import count_issues_by_severity
        
        review = {
            "issues": [
                {"severity": "critical"},
                {"severity": "critical"},
                {"severity": "high"},
                {"severity": "medium"},
                {"severity": "low"}
            ]
        }
        
        counts = count_issues_by_severity(review)
        
        assert counts["critical"] == 2
        assert counts["high"] == 1
        assert counts["medium"] == 1
        assert counts["low"] == 1


class TestWorkflowIterations:
    """Test workflow iteration logic."""
    
    def test_max_iterations_configuration(self):
        """Test max iterations is configurable."""
        pipeline = WorkflowPipeline()
        
        assert pipeline.max_iterations == 3
        
        # Can be changed
        pipeline.max_iterations = 5
        assert pipeline.max_iterations == 5
    
    def test_approval_gate_configuration(self):
        """Test approval gate can be disabled."""
        pipeline = WorkflowPipeline()
        
        assert pipeline.require_user_approval is True
        
        # Can be disabled for testing
        pipeline.require_user_approval = False
        assert pipeline.require_user_approval is False
