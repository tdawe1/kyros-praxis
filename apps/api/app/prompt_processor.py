"""
Prompt processing and validation.

PRD Requirements:
- "validate prompt quality"
- "warn if too short or ambiguous"
- "inject system prompts to guide agents"
"""

import re
from typing import Dict, List, Optional
from pydantic import BaseModel


class ValidationResult(BaseModel):
    """Result of prompt validation."""
    valid: bool
    score: int  # 0-100
    issues: List[str]
    suggestions: List[str]
    warnings: List[str]


class PromptRequirements(BaseModel):
    """Structured requirements extracted from prompt."""
    purpose: Optional[str] = None
    features: List[str] = []
    tech_stack: List[str] = []
    constraints: List[str] = []
    scale: Optional[str] = None  # small, medium, large


class PromptProcessor:
    """
    Validates and enhances user prompts for better AI generation.
    
    PRD: "The system should analyze the prompt before execution."
    """
    
    # Configuration
    MIN_LENGTH = 50  # characters
    RECOMMENDED_LENGTH = 200  # characters
    MAX_LENGTH = 5000  # characters
    
    # Keywords for detection
    PURPOSE_KEYWORDS = [
        'build', 'create', 'develop', 'make', 'implement',
        'want', 'need', 'require', 'looking for'
    ]
    
    TECH_KEYWORDS = {
        'python': ['python', 'fastapi', 'django', 'flask', 'pydantic'],
        'javascript': ['javascript', 'node', 'react', 'vue', 'angular', 'next'],
        'typescript': ['typescript', 'ts'],
        'go': ['golang', 'go'],
        'rust': ['rust'],
        'java': ['java', 'spring'],
        'database': ['postgres', 'mysql', 'mongodb', 'redis', 'sqlite'],
        'frontend': ['html', 'css', 'tailwind', 'bootstrap'],
        'backend': ['api', 'rest', 'graphql', 'grpc'],
    }
    
    SCALE_INDICATORS = {
        'small': ['simple', 'small', 'basic', 'minimal', 'quick', 'prototype'],
        'medium': ['moderate', 'standard', 'typical', 'normal'],
        'large': ['large', 'complex', 'enterprise', 'scalable', 'production', 'advanced']
    }
    
    def __init__(self):
        """Initialize processor."""
        pass
    
    def validate(self, prompt: str) -> ValidationResult:
        """
        Check if prompt has sufficient detail.
        
        PRD: "if the prompt is too short or ambiguous, we will warn the user"
        
        Args:
            prompt: The user's prompt
            
        Returns:
            ValidationResult with validation details
        """
        issues = []
        suggestions = []
        warnings = []
        score = 100
        
        # Clean prompt
        prompt = prompt.strip()
        
        # Length validation
        length = len(prompt)
        if length < self.MIN_LENGTH:
            issues.append(f"Prompt too short ({length} chars, minimum {self.MIN_LENGTH})")
            suggestions.append("Add more details about what you want to build")
            score -= 40
        elif length < self.RECOMMENDED_LENGTH:
            warnings.append(f"Prompt is short ({length} chars, recommended {self.RECOMMENDED_LENGTH}+)")
            suggestions.append("Consider adding more details for better results")
            score -= 15
        
        if length > self.MAX_LENGTH:
            warnings.append(f"Prompt is very long ({length} chars)")
            suggestions.append("Consider breaking into multiple projects")
        
        # Purpose check
        has_purpose = self._has_purpose(prompt)
        if not has_purpose:
            issues.append("Purpose unclear")
            suggestions.append("Start with 'I want to build...' or 'I need...'")
            score -= 20
        
        # Features check
        has_features = self._has_features(prompt)
        if not has_features:
            issues.append("No features or functionality described")
            suggestions.append("List the key features you need")
            score -= 20
        
        # Tech stack mentioned (optional but recommended)
        tech_mentions = self._detect_tech_stack(prompt)
        if not tech_mentions:
            suggestions.append("Consider mentioning preferred tech stack (e.g., Python, React)")
            score -= 10
        
        # Specificity check
        is_specific = self._check_specificity(prompt)
        if not is_specific:
            warnings.append("Prompt may be too vague")
            suggestions.append("Be more specific about requirements and constraints")
            score -= 10
        
        # Check for questions (indicates uncertainty)
        if '?' in prompt:
            question_count = prompt.count('?')
            if question_count > 3:
                warnings.append(f"Contains {question_count} questions - may indicate uncertainty")
                suggestions.append("Try to state requirements rather than ask questions")
        
        # Final score adjustment
        score = max(0, min(100, score))
        
        # Determine validity
        valid = len(issues) == 0
        
        return ValidationResult(
            valid=valid,
            score=score,
            issues=issues,
            suggestions=suggestions,
            warnings=warnings
        )
    
    def enhance(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Add system instructions to guide agents.
        
        PRD: "inject certain system prompts or context to guide the agents' behavior"
        
        Args:
            prompt: The user's prompt
            context: Optional additional context
            
        Returns:
            Enhanced prompt with system instructions
        """
        # Extract requirements
        requirements = self.extract_requirements(prompt)
        
        # Build enhancement
        parts = ["SYSTEM CONTEXT:"]
        
        # Add standard instructions
        parts.append("- Generate production-ready code")
        parts.append("- Follow language best practices")
        parts.append("- Include comprehensive error handling")
        parts.append("- Add clear docstrings and comments")
        parts.append("- Make code testable and maintainable")
        parts.append("- Consider security implications")
        
        # Add tech-specific guidance
        if requirements.tech_stack:
            parts.append(f"\nDETECTED TECHNOLOGIES: {', '.join(requirements.tech_stack)}")
        
        # Add scale guidance
        if requirements.scale:
            parts.append(f"\nPROJECT SCALE: {requirements.scale.upper()}")
            if requirements.scale == 'small':
                parts.append("- Focus on simplicity and quick delivery")
            elif requirements.scale == 'large':
                parts.append("- Focus on scalability and maintainability")
                parts.append("- Consider microservices architecture")
        
        # Add user context if provided
        if context:
            parts.append(f"\nADDITIONAL CONTEXT:")
            for key, value in context.items():
                parts.append(f"- {key}: {value}")
        
        # Add user's prompt
        parts.append(f"\nUSER REQUIREMENTS:\n{prompt}")
        
        # Add closing instruction
        parts.append("\nPlease analyze these requirements and proceed with implementation.")
        
        return "\n".join(parts)
    
    def extract_requirements(self, prompt: str) -> PromptRequirements:
        """
        Parse structured information from prompt.
        
        Args:
            prompt: The user's prompt
            
        Returns:
            PromptRequirements with extracted info
        """
        prompt_lower = prompt.lower()
        
        # Extract purpose (first sentence usually)
        purpose = self._extract_purpose(prompt)
        
        # Extract features (bullet points or numbered lists)
        features = self._extract_features(prompt)
        
        # Detect tech stack
        tech_stack = self._detect_tech_stack(prompt)
        
        # Extract constraints
        constraints = self._extract_constraints(prompt)
        
        # Determine scale
        scale = self._determine_scale(prompt)
        
        return PromptRequirements(
            purpose=purpose,
            features=features,
            tech_stack=tech_stack,
            constraints=constraints,
            scale=scale
        )
    
    # Helper methods
    
    def _has_purpose(self, prompt: str) -> bool:
        """Check if prompt has a clear purpose."""
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in self.PURPOSE_KEYWORDS)
    
    def _has_features(self, prompt: str) -> bool:
        """Check if prompt describes features."""
        # Look for multiple sentences or bullet points
        sentences = len([s for s in prompt.split('.') if s.strip()])
        bullet_points = prompt.count('•') + prompt.count('-') + prompt.count('*')
        numbered = len(re.findall(r'\d+[\.\)]\s', prompt))
        
        return sentences > 2 or bullet_points > 2 or numbered > 1
    
    def _check_specificity(self, prompt: str) -> bool:
        """Check if prompt is specific enough."""
        # Look for specific details (numbers, names, examples)
        has_numbers = bool(re.search(r'\d+', prompt))
        has_examples = 'example' in prompt.lower() or 'such as' in prompt.lower()
        has_specifics = 'specifically' in prompt.lower() or 'exactly' in prompt.lower()
        
        # Check word count
        words = len(prompt.split())
        
        return words > 40 or has_numbers or has_examples or has_specifics
    
    def _extract_purpose(self, prompt: str) -> Optional[str]:
        """Extract the main purpose from prompt."""
        # Try to find first sentence with purpose keyword
        sentences = [s.strip() for s in prompt.split('.') if s.strip()]
        
        for sentence in sentences[:3]:  # Check first 3 sentences
            if any(keyword in sentence.lower() for keyword in self.PURPOSE_KEYWORDS):
                return sentence[:200]  # Limit to 200 chars
        
        # Fallback: return first sentence
        if sentences:
            return sentences[0][:200]
        
        return None
    
    def _extract_features(self, prompt: str) -> List[str]:
        """Extract features from prompt."""
        features = []
        
        # Find bullet points
        bullet_matches = re.findall(r'[•\-\*]\s*([^\n\r]+)', prompt)
        features.extend(bullet_matches)
        
        # Find numbered items
        numbered_matches = re.findall(r'\d+[\.\)]\s*([^\n\r]+)', prompt)
        features.extend(numbered_matches)
        
        # Clean and limit
        features = [f.strip() for f in features if f.strip()]
        return features[:10]  # Max 10 features
    
    def _detect_tech_stack(self, prompt: str) -> List[str]:
        """Detect mentioned technologies."""
        prompt_lower = prompt.lower()
        detected = set()
        
        for category, keywords in self.TECH_KEYWORDS.items():
            if any(keyword in prompt_lower for keyword in keywords):
                # Add the actual keyword that was found
                for keyword in keywords:
                    if keyword in prompt_lower:
                        detected.add(keyword)
        
        return sorted(list(detected))
    
    def _extract_constraints(self, prompt: str) -> List[str]:
        """Extract constraints or requirements."""
        constraints = []
        
        constraint_keywords = [
            'must', 'should', 'need to', 'required', 'constraint',
            'limitation', 'cannot', 'must not'
        ]
        
        sentences = [s.strip() for s in prompt.split('.') if s.strip()]
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in constraint_keywords):
                constraints.append(sentence[:150])
        
        return constraints[:5]  # Max 5 constraints
    
    def _determine_scale(self, prompt: str) -> str:
        """Determine project scale from prompt."""
        prompt_lower = prompt.lower()
        
        # Count indicators
        scale_counts = {
            'small': 0,
            'medium': 0,
            'large': 0
        }
        
        for scale, indicators in self.SCALE_INDICATORS.items():
            for indicator in indicators:
                if indicator in prompt_lower:
                    scale_counts[scale] += 1
        
        # Return scale with highest count
        if scale_counts['large'] > 0:
            return 'large'
        elif scale_counts['small'] > 0:
            return 'small'
        else:
            return 'medium'  # Default


# Global instance
prompt_processor = PromptProcessor()
