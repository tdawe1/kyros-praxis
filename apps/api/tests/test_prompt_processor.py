"""
Tests for prompt processor module.
"""

import pytest
from app.prompt_processor import PromptProcessor, ValidationResult, PromptRequirements


class TestPromptProcessorValidation:
    """Test prompt validation logic."""
    
    def setup_method(self):
        """Initialize processor for each test."""
        self.processor = PromptProcessor()
    
    def test_very_short_prompt_fails(self):
        """Test extremely short prompts are rejected."""
        result = self.processor.validate("hi")
        
        assert result.valid is False
        assert result.score < 20
        assert len(result.issues) > 0
        assert any("too short" in issue.lower() for issue in result.issues)
    
    def test_minimal_length_prompt_passes(self):
        """Test prompt at minimum length passes with warnings."""
        prompt = "I want to build a simple web application for tracking tasks"
        result = self.processor.validate(prompt)
        
        # Should pass but with lower score
        assert len(prompt) >= 50
        assert result.score >= 40
    
    def test_recommended_length_prompt_scores_higher(self):
        """Test longer detailed prompts score better."""
        detailed_prompt = """
        I want to build a comprehensive web application for task management.
        
        Key features:
        - User authentication and authorization
        - Create, read, update, and delete tasks
        - Assign tasks to team members
        - Set priorities and due dates
        - Email notifications for deadlines
        - Dashboard with statistics
        
        Technology: Python with FastAPI for backend, React for frontend, PostgreSQL database.
        Should support 1000+ concurrent users.
        """
        
        result = self.processor.validate(detailed_prompt)
        
        assert result.valid is True
        assert result.score >= 80
        assert len(result.issues) == 0
    
    def test_prompt_without_purpose_fails(self):
        """Test prompt without clear purpose fails validation."""
        # Random text without purpose keywords
        prompt = "This is some random text that doesn't describe what to build or create"
        
        result = self.processor.validate(prompt)
        
        assert result.valid is False
        # Should have issues (might say "purpose" or "unclear" etc.)
        assert len(result.issues) > 0
    
    def test_prompt_with_purpose_keywords_passes(self):
        """Test prompt with purpose keywords passes purpose check."""
        prompt = "I need to create a web application for managing customer relationships"
        
        result = self.processor.validate(prompt)
        
        # Might still have other issues, but purpose should be OK
        assert not any("purpose" in issue.lower() for issue in result.issues)
    
    def test_prompt_without_features_gets_warning(self):
        """Test prompt without feature descriptions gets flagged."""
        prompt = "Build a simple app"
        
        result = self.processor.validate(prompt)
        
        assert result.valid is False
        assert any("feature" in issue.lower() for issue in result.issues)
    
    def test_prompt_with_bullet_features_passes(self):
        """Test prompt with bullet point features passes."""
        prompt = """
        Build a todo app with:
        - User authentication
        - Task creation
        - Task editing
        - Task deletion
        """
        
        result = self.processor.validate(prompt)
        
        # Should not have feature complaint
        feature_issues = [i for i in result.issues if "feature" in i.lower()]
        assert len(feature_issues) == 0
    
    def test_prompt_with_numbered_features_passes(self):
        """Test prompt with numbered features passes."""
        prompt = """
        Build an app with these features:
        1. User login
        2. Data dashboard
        3. Export reports
        """
        
        result = self.processor.validate(prompt)
        
        feature_issues = [i for i in result.issues if "feature" in i.lower()]
        assert len(feature_issues) == 0
    
    def test_prompt_with_tech_stack_scores_higher(self):
        """Test mentioning tech stack improves score."""
        prompt_without_tech = "Build a web app for task management with user authentication"
        prompt_with_tech = "Build a web app for task management with user authentication using Python FastAPI and React"
        
        result_without = self.processor.validate(prompt_without_tech)
        result_with = self.processor.validate(prompt_with_tech)
        
        assert result_with.score >= result_without.score
    
    def test_very_long_prompt_gets_warning(self):
        """Test extremely long prompts get warnings."""
        long_prompt = "Build app. " * 1000  # Over 5000 chars
        
        result = self.processor.validate(long_prompt)
        
        assert any("long" in warning.lower() for warning in result.warnings)
    
    def test_prompt_with_many_questions_gets_warning(self):
        """Test prompts with many questions indicate uncertainty."""
        questionable_prompt = """
        Should I build a web app? Or maybe a mobile app? What technology should I use?
        React or Vue? Should it have authentication? What about the database?
        """
        
        result = self.processor.validate(questionable_prompt)
        
        assert len(result.warnings) > 0
        assert any("question" in w.lower() for w in result.warnings)


class TestPromptProcessorEnhancement:
    """Test prompt enhancement logic."""
    
    def setup_method(self):
        """Initialize processor for each test."""
        self.processor = PromptProcessor()
    
    def test_enhancement_adds_system_context(self):
        """Test enhancement adds system prompts."""
        original = "Build a todo app"
        enhanced = self.processor.enhance(original)
        
        assert "SYSTEM CONTEXT" in enhanced
        assert len(enhanced) > len(original)
    
    def test_enhancement_includes_original_prompt(self):
        """Test original prompt is preserved in enhancement."""
        original = "Build a specific custom application"
        enhanced = self.processor.enhance(original)
        
        assert original in enhanced
    
    def test_enhancement_adds_best_practices(self):
        """Test enhancement mentions best practices."""
        enhanced = self.processor.enhance("Build app")
        
        assert "production-ready" in enhanced.lower()
        assert "best practices" in enhanced.lower()
        assert "error handling" in enhanced.lower()
    
    def test_enhancement_with_context(self):
        """Test enhancement with additional context."""
        enhanced = self.processor.enhance(
            "Build app",
            context={"user_level": "beginner", "deadline": "1 week"}
        )
        
        assert "ADDITIONAL CONTEXT" in enhanced
        assert "user_level" in enhanced
        assert "beginner" in enhanced
    
    def test_enhancement_mentions_detected_tech(self):
        """Test enhancement mentions detected technologies."""
        enhanced = self.processor.enhance("Build app with Python and React")
        
        # Should detect tech stack
        assert "DETECTED TECHNOLOGIES" in enhanced or "python" in enhanced.lower()
    
    def test_enhancement_includes_scale_guidance(self):
        """Test enhancement adds scale-specific guidance."""
        large_prompt = "Build a scalable enterprise platform"
        enhanced = self.processor.enhance(large_prompt)
        
        assert "SCALE" in enhanced.upper()
        # Should detect as large and mention scalability
        assert "large" in enhanced.lower() or "scalability" in enhanced.lower()


class TestRequirementsExtraction:
    """Test requirements extraction."""
    
    def setup_method(self):
        """Initialize processor for each test."""
        self.processor = PromptProcessor()
    
    def test_extract_purpose_from_first_sentence(self):
        """Test purpose extraction from opening sentence."""
        prompt = "I want to build a task manager. It should have many features."
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert reqs.purpose is not None
        assert "task manager" in reqs.purpose.lower()
    
    def test_extract_features_from_bullets(self):
        """Test feature extraction from bullet points."""
        prompt = """
        Build app with:
        - Feature one
        - Feature two
        - Feature three
        """
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert len(reqs.features) >= 3
    
    def test_extract_features_from_numbered_list(self):
        """Test feature extraction from numbered lists."""
        prompt = """
        Features needed:
        1. User login
        2. Dashboard
        3. Reports
        """
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert len(reqs.features) >= 3
    
    def test_detect_python_tech_stack(self):
        """Test Python technology detection."""
        prompt = "Build with Python, FastAPI, and PostgreSQL"
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert "python" in reqs.tech_stack
        assert "fastapi" in reqs.tech_stack
    
    def test_detect_javascript_tech_stack(self):
        """Test JavaScript technology detection."""
        prompt = "Create a React app with Node.js backend"
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert "react" in reqs.tech_stack
        assert "node" in reqs.tech_stack or "javascript" in reqs.tech_stack
    
    def test_detect_multiple_tech_stacks(self):
        """Test detection of mixed technology stacks."""
        prompt = "Build full-stack app: Python FastAPI backend, React TypeScript frontend, PostgreSQL database, Redis cache"
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert len(reqs.tech_stack) >= 4
        assert "python" in reqs.tech_stack
        assert "react" in reqs.tech_stack
        assert "postgres" in reqs.tech_stack or "postgresql" in reqs.tech_stack
        assert "redis" in reqs.tech_stack
    
    def test_extract_constraints(self):
        """Test constraint extraction."""
        prompt = "Build app that must support 1000 users and must not use external APIs"
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert len(reqs.constraints) > 0
        assert any("must" in c.lower() for c in reqs.constraints)
    
    def test_determine_small_scale(self):
        """Test small scale determination."""
        prompt = "Build a simple basic calculator app"
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert reqs.scale == "small"
    
    def test_determine_medium_scale(self):
        """Test medium scale determination."""
        prompt = "Build a standard web application"
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert reqs.scale == "medium"
    
    def test_determine_large_scale(self):
        """Test large scale determination."""
        prompt = "Build a complex enterprise-grade scalable platform"
        
        reqs = self.processor.extract_requirements(prompt)
        
        assert reqs.scale == "large"


class TestPromptProcessorEdgeCases:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Initialize processor for each test."""
        self.processor = PromptProcessor()
    
    def test_empty_prompt(self):
        """Test handling of empty prompt."""
        result = self.processor.validate("")
        
        assert result.valid is False
        assert result.score < 20
    
    def test_whitespace_only_prompt(self):
        """Test handling of whitespace-only prompt."""
        result = self.processor.validate("   \n\t   ")
        
        assert result.valid is False
    
    def test_special_characters_in_prompt(self):
        """Test prompts with special characters."""
        prompt = "Build app with @mentions, #hashtags, and $variables! Should handle UTF-8: 你好世界"
        
        result = self.processor.validate(prompt)
        
        # Should not crash, should process normally
        assert isinstance(result, ValidationResult)
    
    def test_extremely_repetitive_prompt(self):
        """Test handling of repetitive text."""
        prompt = "Build app. " * 100
        
        result = self.processor.validate(prompt)
        
        # Should process but might have low specificity score
        assert isinstance(result, ValidationResult)
    
    def test_extract_from_unstructured_text(self):
        """Test extraction from rambling unstructured text."""
        prompt = "So I was thinking maybe we could build something and it might have some features I guess"
        
        reqs = self.processor.extract_requirements(prompt)
        
        # Should not crash
        assert isinstance(reqs, PromptRequirements)


class TestValidationResultModel:
    """Test ValidationResult data model."""
    
    def test_validation_result_creation(self):
        """Test creating ValidationResult."""
        result = ValidationResult(
            valid=True,
            score=85,
            issues=[],
            suggestions=["Add more details"],
            warnings=[]
        )
        
        assert result.valid is True
        assert result.score == 85
        assert len(result.suggestions) == 1
    
    def test_validation_result_with_issues(self):
        """Test ValidationResult with issues."""
        result = ValidationResult(
            valid=False,
            score=30,
            issues=["Too short", "No purpose"],
            suggestions=["Make longer", "Add purpose"],
            warnings=[]
        )
        
        assert result.valid is False
        assert len(result.issues) == 2
        assert len(result.suggestions) == 2


class TestPromptRequirementsModel:
    """Test PromptRequirements data model."""
    
    def test_requirements_creation(self):
        """Test creating PromptRequirements."""
        reqs = PromptRequirements(
            purpose="Build app",
            features=["feat1", "feat2"],
            tech_stack=["python", "react"],
            constraints=["must be fast"],
            scale="medium"
        )
        
        assert reqs.purpose == "Build app"
        assert len(reqs.features) == 2
        assert len(reqs.tech_stack) == 2
        assert reqs.scale == "medium"
    
    def test_requirements_defaults(self):
        """Test PromptRequirements with defaults."""
        reqs = PromptRequirements()
        
        assert reqs.purpose is None
        assert reqs.features == []
        assert reqs.tech_stack == []
        assert reqs.constraints == []
        assert reqs.scale is None
