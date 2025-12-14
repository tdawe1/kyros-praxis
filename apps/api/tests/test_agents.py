"""
Tests for multi-agent system (planner, coder, tester).
"""

import pytest
from app.agents.planner import (
    validate_specification,
    extract_key_info,
    run_planner,
)
from app.agents.coder import (
    parse_code_output,
    validate_code_output,
    count_code_stats,
    get_file_tree,
    run_coder,
)
from app.agents.tester import (
    parse_test_output,
    validate_test_output,
    count_issues_by_severity,
    has_blocking_issues,
    generate_test_summary,
    extract_critical_issues,
    run_tester,
)


# Planner Agent Tests

class TestPlannerValidation:
    """Test specification validation."""
    
    def test_validate_complete_spec(self):
        """Test validation of complete specification."""
        spec = {
            "purpose": "Test project",
            "components": ["comp1", "comp2"],
            "technology": {"language": "python"},
            "file_structure": {"src": {}},
            "dependencies": ["fastapi"]
        }
        
        is_valid, error = validate_specification(spec)
        assert is_valid is True
        assert error is None
    
    def test_validate_missing_fields(self):
        """Test validation fails with missing fields."""
        spec = {
            "purpose": "Test project",
            "components": ["comp1"]
            # Missing: technology, file_structure, dependencies
        }
        
        is_valid, error = validate_specification(spec)
        assert is_valid is False
        assert "Missing required fields" in error
    
    def test_validate_invalid_json_string(self):
        """Test validation fails with invalid JSON string."""
        spec = "not valid json {"
        
        is_valid, error = validate_specification(spec)
        assert is_valid is False
        assert "not valid JSON" in error
    
    def test_validate_non_dict(self):
        """Test validation fails with non-dictionary."""
        spec = ["list", "not", "dict"]
        
        is_valid, error = validate_specification(spec)
        assert is_valid is False
        assert "must be a dictionary" in error


class TestPlannerHelpers:
    """Test planner helper functions."""
    
    def test_extract_key_info(self):
        """Test extracting key information from spec."""
        spec = {
            "purpose": "A" * 300,  # Long purpose
            "components": ["comp1", "comp2", "comp3"],
            "technology": {"language": "python"},
            "dependencies": ["dep1", "dep2"]
        }
        
        info = extract_key_info(spec)
        
        assert len(info["purpose"]) == 200  # Truncated
        assert info["num_components"] == 3
        assert info["technology"] == "python"
        assert info["complexity"] == "simple"
    
    def test_complexity_estimation(self):
        """Test complexity estimation."""
        # Simple project
        simple_spec = {
            "components": ["comp1", "comp2"],
            "dependencies": ["dep1", "dep2"]
        }
        info = extract_key_info(simple_spec)
        assert info["complexity"] == "simple"
        
        # Moderate project
        moderate_spec = {
            "components": ["comp" + str(i) for i in range(5)],
            "dependencies": ["dep" + str(i) for i in range(10)]
        }
        info = extract_key_info(moderate_spec)
        assert info["complexity"] == "moderate"
        
        # Complex project
        complex_spec = {
            "components": ["comp" + str(i) for i in range(10)],
            "dependencies": ["dep" + str(i) for i in range(20)]
        }
        info = extract_key_info(complex_spec)
        assert info["complexity"] == "complex"


@pytest.mark.asyncio
async def test_run_planner_simulation_mode():
    """Test planner runs in simulation mode when CrewAI unavailable."""
    result = await run_planner("Test prompt", project_id="test-123")
    
    assert result["status"] == "completed"
    assert "specification" in result
    assert result.get("simulation") is True


# Coder Agent Tests

class TestCoderParsing:
    """Test code output parsing."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON output."""
        output = """
        {
            "files": [
                {"path": "main.py", "content": "print('hello')", "description": "Main file"}
            ],
            "setup_instructions": "Run with python main.py"
        }
        """
        
        parsed = parse_code_output(output)
        
        assert "files" in parsed
        assert len(parsed["files"]) == 1
        assert parsed["files"][0]["path"] == "main.py"
    
    def test_parse_invalid_json_fallback(self):
        """Test fallback for invalid JSON."""
        output = "Some non-JSON output"
        
        parsed = parse_code_output(output)
        
        assert "files" in parsed
        assert len(parsed["files"]) == 1
        assert parsed["files"][0]["content"] == output
        assert "not in expected JSON format" in parsed["notes"]
    
    def test_parse_dict_input(self):
        """Test parsing dictionary input."""
        output = {
            "files": [{"path": "test.py", "content": "test"}]
        }
        
        parsed = parse_code_output(output)
        
        assert parsed == output


class TestCoderValidation:
    """Test code output validation."""
    
    def test_validate_complete_output(self):
        """Test validation of complete code output."""
        output = {
            "files": [
                {"path": "main.py", "content": "code here"}
            ]
        }
        
        is_valid, error = validate_code_output(output)
        assert is_valid is True
        assert error is None
    
    def test_validate_missing_files_key(self):
        """Test validation fails without files key."""
        output = {"setup_instructions": "test"}
        
        is_valid, error = validate_code_output(output)
        assert is_valid is False
        assert "must contain 'files'" in error
    
    def test_validate_missing_file_fields(self):
        """Test validation fails with incomplete file objects."""
        output = {
            "files": [
                {"path": "test.py"}  # Missing content
            ]
        }
        
        is_valid, error = validate_code_output(output)
        assert is_valid is False
        assert "missing 'content'" in error


class TestCoderHelpers:
    """Test coder helper functions."""
    
    def test_get_file_tree(self):
        """Test building file tree from flat list."""
        files = [
            {"path": "src/main.py", "content": ""},
            {"path": "src/utils/helper.py", "content": ""},
            {"path": "tests/test_main.py", "content": ""}
        ]
        
        tree = get_file_tree(files)
        
        assert "src" in tree
        assert "tests" in tree
        assert "main.py" in tree["src"]
        assert "utils" in tree["src"]
        assert "helper.py" in tree["src"]["utils"]
    
    def test_count_code_stats(self):
        """Test counting code statistics."""
        files = [
            {"path": "file1.py", "content": "line1\nline2\nline3"},
            {"path": "file2.js", "content": "const x = 1;"},
            {"path": "file3.py", "content": "print('hello')"}
        ]
        
        stats = count_code_stats(files)
        
        assert stats["total_files"] == 3
        assert stats["total_lines"] == 2  # file1 has 2 newlines, others have 0
        assert stats["file_types"]["py"] == 2
        assert stats["file_types"]["js"] == 1


@pytest.mark.asyncio
async def test_run_coder_simulation_mode():
    """Test coder runs in simulation mode when CrewAI unavailable."""
    spec = {"purpose": "test", "components": []}
    result = await run_coder(spec, project_id="test-123")
    
    assert result["status"] == "completed"
    assert "files" in result
    assert result.get("simulation") is True


# Tester Agent Tests

class TestTesterParsing:
    """Test test output parsing."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON test output."""
        output = """
        {
            "review": {
                "matches_spec": true,
                "overall_quality": "good",
                "issues": []
            },
            "tests": [
                {"file": "test_main.py", "content": "def test_x(): pass"}
            ]
        }
        """
        
        parsed = parse_test_output(output)
        
        assert "review" in parsed
        assert "tests" in parsed
        assert parsed["review"]["matches_spec"] is True
    
    def test_parse_invalid_json_fallback(self):
        """Test fallback for invalid JSON."""
        output = "Non-JSON test output"
        
        parsed = parse_test_output(output)
        
        assert "error" in parsed
        assert "raw_output" in parsed


class TestTesterValidation:
    """Test test output validation."""
    
    def test_validate_complete_output(self):
        """Test validation of complete test output."""
        output = {
            "review": {"matches_spec": True, "issues": []},
            "tests": []
        }
        
        is_valid, error = validate_test_output(output)
        assert is_valid is True
        assert error is None
    
    def test_validate_missing_review(self):
        """Test validation fails without review."""
        output = {"tests": []}
        
        is_valid, error = validate_test_output(output)
        assert is_valid is False
        assert "must contain 'review'" in error


class TestTesterHelpers:
    """Test tester helper functions."""
    
    def test_count_issues_by_severity(self):
        """Test counting issues by severity."""
        review = {
            "issues": [
                {"severity": "critical", "description": "Bug 1"},
                {"severity": "critical", "description": "Bug 2"},
                {"severity": "high", "description": "Issue 1"},
                {"severity": "medium", "description": "Issue 2"},
                {"severity": "low", "description": "Style issue"}
            ]
        }
        
        counts = count_issues_by_severity(review)
        
        assert counts["critical"] == 2
        assert counts["high"] == 1
        assert counts["medium"] == 1
        assert counts["low"] == 1
    
    def test_has_blocking_issues(self):
        """Test detecting blocking issues."""
        # No blocking issues
        review = {
            "issues": [
                {"severity": "medium"},
                {"severity": "low"}
            ]
        }
        assert has_blocking_issues(review) is False
        
        # Has critical issue
        review = {
            "issues": [
                {"severity": "critical", "description": "Bug"}
            ]
        }
        assert has_blocking_issues(review) is True
        
        # Has high issue
        review = {
            "issues": [
                {"severity": "high", "description": "Security"}
            ]
        }
        assert has_blocking_issues(review) is True
    
    def test_extract_critical_issues(self):
        """Test extracting only critical/high issues."""
        review = {
            "issues": [
                {"severity": "critical", "description": "Bug"},
                {"severity": "high", "description": "Security"},
                {"severity": "medium", "description": "Code quality"},
                {"severity": "low", "description": "Style"}
            ]
        }
        
        critical = extract_critical_issues(review)
        
        assert len(critical) == 2
        assert critical[0]["severity"] == "critical"
        assert critical[1]["severity"] == "high"
    
    def test_generate_test_summary(self):
        """Test generating human-readable summary."""
        output = {
            "review": {
                "matches_spec": True,
                "overall_quality": "excellent",
                "issues": [
                    {"severity": "low", "description": "Minor style issue"}
                ]
            },
            "tests": [
                {"file": "test1.py"},
                {"file": "test2.py"}
            ],
            "test_coverage": {
                "estimated_coverage": "85%"
            }
        }
        
        summary = generate_test_summary(output)
        
        assert "Code Quality: EXCELLENT" in summary
        assert "Matches Specification: YES" in summary
        assert "Issues Found: 1 total" in summary
        assert "Test Files Generated: 2" in summary
        assert "Estimated Coverage: 85%" in summary


@pytest.mark.asyncio
async def test_run_tester_simulation_mode():
    """Test tester runs in simulation mode when CrewAI unavailable."""
    code_files = {"files": []}
    spec = {"purpose": "test"}
    
    result = await run_tester(code_files, spec, project_id="test-123")
    
    assert result["status"] == "completed"
    assert "review" in result
    assert "tests" in result
    assert result.get("simulation") is True
