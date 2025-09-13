"""
Claude 4.1 Opus Escalation Triggers for Hybrid Model System

This module implements intelligent escalation detection that determines when
tasks require Claude 4.1 Opus instead of GLM-4.5, providing cost-effective
model selection while ensuring quality for critical decisions.

ESCALATION CRITERIA:
1. Critical Decision Threshold: Tasks with high business impact or risk
2. Complexity Analysis: Multi-file refactors, architectural changes
3. Security Sensitivity: Auth, encryption, compliance, security reviews
4. Performance Critical: Database, caching, algorithmic optimization
5. Integration Complexity: Multi-service, cross-platform, API design
6. Quality Requirements: Code review, testing, validation
7. Error Handling: Complex error scenarios, debugging, troubleshooting
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class EscalationReason(Enum):
    """Reasons for escalating to Claude 4.1 Opus"""
    
    # Critical Decision Categories
    CRITICAL_SECURITY = "critical_security"  # Security-critical changes
    ARCHITECTURAL_DECISION = "architectural_decision"  # Major architecture decisions
    COMPLIANCE_RELATED = "compliance_related"  # Regulatory/compliance requirements
    
    # Complexity Categories
    MULTI_FILE_REFACTOR = "multi_file_refactor"  # Changes spanning multiple files
    CROSS_SERVICE_CHANGES = "cross_service_changes"  # Affects multiple services
    LEGACY_SYSTEM_INTEGRATION = "legacy_system_integration"  # Working with legacy code
    
    # Performance Categories
    PERFORMANCE_CRITICAL = "performance_critical"  # Performance-optimizing changes
    DATABASE_SCHEMA_CHANGES = "database_schema_changes"  # Database modifications
    ALGORITHM_COMPLEXITY = "algorithm_complexity"  # Complex algorithmic problems
    
    # Quality Categories
    COMPREHENSIVE_CODE_REVIEW = "comprehensive_code_review"  # Thorough code reviews
    TESTING_STRATEGY = "testing_strategy"  # Complex testing scenarios
    DEBUG_COMPLEX_ISSUES = "debug_complex_issues"  # Complex debugging scenarios
    
    # Integration Categories
    API_DESIGN = "api_design"  # API contract design
    PROTOCOL_IMPLEMENTATION = "protocol_implementation"  # Protocol implementations
    MIGRATION_STRATEGY = "migration_strategy"  # Migration planning and execution


class EscalationPriority(Enum):
    """Priority levels for escalation triggers"""
    
    LOW = "low"          # Consider escalation, but GLM-4.5 likely sufficient
    MEDIUM = "medium"    # Recommend escalation for better quality
    HIGH = "high"        # Strongly recommend escalation
    CRITICAL = "critical"  # Must escalate - risk of failure with GLM-4.5


@dataclass
class EscalationTrigger:
    """A specific trigger that may require escalation to Claude 4.1 Opus"""
    
    reason: EscalationReason
    priority: EscalationPriority
    description: str
    evidence: List[str]
    confidence: float  # 0.0 to 1.0 confidence in this trigger
    file_patterns: Optional[List[str]] = None
    code_indicators: Optional[List[str]] = None


@dataclass
class EscalationAssessment:
    """Complete assessment of whether escalation is needed"""
    
    should_escalate: bool
    confidence: float  # Overall confidence in escalation decision
    triggers: List[EscalationTrigger]
    primary_reason: str
    recommended_model: str
    fallback_model: str
    cost_impact_estimate: Optional[str] = None
    risk_assessment: Optional[str] = None


class EscalationDetector:
    """
    Detects when tasks should be escalated to Claude 4.1 Opus
    
    This class analyzes task context, files, and requirements to determine
    if escalation to a higher-capability model is warranted.
    """
    
    def __init__(self):
        # Security-sensitive patterns
        self.security_patterns = {
            "auth": ["auth", "login", "password", "token", "jwt", "oauth", "session"],
            "encryption": ["encrypt", "decrypt", "cipher", "aes", "rsa", "key", "crypto"],
            "security": ["security", "vulnerability", "exploit", "xss", "csrf", "injection"],
            "compliance": ["gdpr", "hipaa", "soc2", "pci", "compliance", "audit"]
        }
        
        # Architecture patterns
        self.architecture_patterns = {
            "design": ["architecture", "design", "pattern", "microservice", "monolith"],
            "structure": ["structure", "organization", "layout", "framework"],
            "interface": ["interface", "api", "contract", "protocol", "schema"]
        }
        
        # Performance patterns
        self.performance_patterns = {
            "optimization": ["optimize", "performance", "speed", "latency", "throughput"],
            "database": ["database", "query", "index", "migration", "schema"],
            "algorithm": ["algorithm", "complexity", "big_o", "efficient", "scale"]
        }
        
        # Quality patterns
        self.quality_patterns = {
            "review": ["review", "refactor", "clean", "quality", "best_practice"],
            "testing": ["test", "spec", "mock", "stub", "coverage", "integration"],
            "debug": ["debug", "error", "exception", "bug", "issue", "troubleshoot"]
        }
        
        # High-risk file patterns
        self.high_risk_files = [
            "**/auth*.py",
            "**/security*.py",
            "**/encryption*.py",
            "**/database*.py",
            "**/schema*.py",
            "**/migration*.py",
            "**/config*.py",
            "**/settings*.py"
        ]
        
        # Critical file extensions
        self.critical_extensions = {".py", ".js", ".ts", ".go", ".java", ".rs", ".cpp", ".h"}
    
    def analyze_task_context(
        self,
        task_description: str,
        files_to_modify: List[str],
        current_files: List[str],
        task_type: str = "implementation"
    ) -> EscalationAssessment:
        """
        Analyze task context to determine if escalation is needed
        
        Args:
            task_description: Description of the task to perform
            files_to_modify: List of files that will be modified
            current_files: List of files in the current workspace
            task_type: Type of task (implementation, review, debug, etc.)
            
        Returns:
            EscalationAssessment with recommendation
        """
        triggers = []
        
        # 1. Analyze task description for escalation keywords
        triggers.extend(self._analyze_task_keywords(task_description))
        
        # 2. Analyze files for escalation patterns
        triggers.extend(self._analyze_file_patterns(files_to_modify, current_files))
        
        # 3. Analyze task complexity
        triggers.extend(self._analyze_complexity(task_description, files_to_modify))
        
        # 4. Analyze security and compliance aspects
        triggers.extend(self._analyze_security_aspects(task_description, files_to_modify))
        
        # Calculate overall escalation decision
        return self._make_escalation_decision(triggers, task_type)
    
    def _analyze_task_keywords(self, task_description: str) -> List[EscalationTrigger]:
        """Analyze task description for escalation-triggering keywords"""
        triggers = []
        desc_lower = task_description.lower()
        
        # Security escalation triggers
        for category, keywords in self.security_patterns.items():
            matches = [kw for kw in keywords if kw in desc_lower]
            if matches:
                if category in ["auth", "encryption"]:
                    triggers.append(EscalationTrigger(
                        reason=EscalationReason.CRITICAL_SECURITY,
                        priority=EscalationPriority.CRITICAL,
                        description=f"Security-critical task involving {category}",
                        evidence=[f"Keywords found: {', '.join(matches)}"],
                        confidence=0.9,
                        code_indicators=keywords
                    ))
                elif category == "compliance":
                    triggers.append(EscalationTrigger(
                        reason=EscalationReason.COMPLIANCE_RELATED,
                        priority=EscalationPriority.HIGH,
                        description=f"Compliance-related task involving {category}",
                        evidence=[f"Keywords found: {', '.join(matches)}"],
                        confidence=0.8,
                        code_indicators=keywords
                    ))
        
        # Architecture escalation triggers
        for category, keywords in self.architecture_patterns.items():
            matches = [kw for kw in keywords if kw in desc_lower]
            if len(matches) >= 2:  # Multiple architecture keywords
                triggers.append(EscalationTrigger(
                    reason=EscalationReason.ARCHITECTURAL_DECISION,
                    priority=EscalationPriority.HIGH,
                    description=f"Architectural decision involving {category}",
                    evidence=[f"Multiple architecture keywords: {', '.join(matches)}"],
                    confidence=0.7,
                    code_indicators=keywords
                ))
        
        # Performance escalation triggers
        for category, keywords in self.performance_patterns.items():
            matches = [kw for kw in keywords if kw in desc_lower]
            if matches:
                if "optimization" in matches or "performance" in matches:
                    triggers.append(EscalationTrigger(
                        reason=EscalationReason.PERFORMANCE_CRITICAL,
                        priority=EscalationPriority.MEDIUM,
                        description=f"Performance optimization task",
                        evidence=[f"Performance keywords: {', '.join(matches)}"],
                        confidence=0.6,
                        code_indicators=keywords
                    ))
                elif category == "database" and len(matches) >= 2:
                    triggers.append(EscalationTrigger(
                        reason=EscalationReason.DATABASE_SCHEMA_CHANGES,
                        priority=EscalationPriority.HIGH,
                        description=f"Database-related changes",
                        evidence=[f"Database keywords: {', '.join(matches)}"],
                        confidence=0.7,
                        code_indicators=keywords
                    ))
        
        return triggers
    
    def _analyze_file_patterns(self, files_to_modify: List[str], current_files: List[str]) -> List[EscalationTrigger]:
        """Analyze file patterns for escalation triggers"""
        triggers = []
        
        # Check for high-risk files
        high_risk_matches = []
        for file_path in files_to_modify:
            for pattern in self.high_risk_files:
                if Path(file_path).match(pattern):
                    high_risk_matches.append(file_path)
        
        if high_risk_matches:
            triggers.append(EscalationTrigger(
                reason=EscalationReason.CRITICAL_SECURITY,
                priority=EscalationPriority.HIGH,
                description=f"Modifying high-risk files: {', '.join(high_risk_matches)}",
                evidence=[f"High-risk files: {', '.join(high_risk_matches)}"],
                confidence=0.8,
                file_patterns=self.high_risk_files
            ))
        
        # Check for multi-file changes
        if len(files_to_modify) > 3:
            triggers.append(EscalationTrigger(
                reason=EscalationReason.MULTI_FILE_REFACTOR,
                priority=EscalationPriority.MEDIUM,
                description=f"Multi-file modification ({len(files_to_modify)} files)",
                evidence=[f"File count: {len(files_to_modify)}"],
                confidence=min(0.5 + (len(files_to_modify) * 0.1), 0.9)
            ))
        
        # Check for cross-service changes
        services_affected = set()
        for file_path in files_to_modify:
            if "services/" in file_path:
                service_parts = file_path.split("services/")[1].split("/")
                if len(service_parts) > 1:
                    services_affected.add(service_parts[0])
        
        if len(services_affected) > 1:
            triggers.append(EscalationTrigger(
                reason=EscalationReason.CROSS_SERVICE_CHANGES,
                priority=EscalationPriority.HIGH,
                description=f"Cross-service changes affecting: {', '.join(services_affected)}",
                evidence=[f"Services affected: {', '.join(services_affected)}"],
                confidence=0.8
            ))
        
        return triggers
    
    def _analyze_complexity(self, task_description: str, files_to_modify: List[str]) -> List[EscalationTrigger]:
        """Analyze task complexity for escalation triggers"""
        triggers = []
        
        # Complex task indicators
        complexity_indicators = [
            "complex", "difficult", "challenging", "intricate", "sophisticated",
            "restructure", "redesign", "rewrite", "rearchitecture", "reimplement"
        ]
        
        desc_lower = task_description.lower()
        complexity_matches = [ind for ind in complexity_indicators if ind in desc_lower]
        
        if complexity_matches:
            triggers.append(EscalationTrigger(
                reason=EscalationReason.MULTI_FILE_REFACTOR,
                priority=EscalationPriority.MEDIUM,
                description=f"Complex task indicated by keywords: {', '.join(complexity_matches)}",
                evidence=[f"Complexity indicators: {', '.join(complexity_matches)}"],
                confidence=0.6
            ))
        
        # Algorithmic complexity
        algorithm_keywords = ["algorithm", "optimization", "efficiency", "complexity", "big_o"]
        algo_matches = [kw for kw in algorithm_keywords if kw in desc_lower]
        
        if algo_matches:
            triggers.append(EscalationTrigger(
                reason=EscalationReason.ALGORITHM_COMPLEXITY,
                priority=EscalationPriority.HIGH,
                description=f"Algorithmic complexity indicated: {', '.join(algo_matches)}",
                evidence=[f"Algorithm keywords: {', '.join(algo_matches)}"],
                confidence=0.7
            ))
        
        return triggers
    
    def _analyze_security_aspects(self, task_description: str, files_to_modify: List[str]) -> List[EscalationTrigger]:
        """Analyze security aspects for escalation triggers"""
        triggers = []
        
        # Direct security mentions
        security_direct_keywords = [
            "security", "vulnerability", "exploit", "breach", "attack", "threat",
            "secure", "unsafe", "risk", "protect", "defend"
        ]
        
        desc_lower = task_description.lower()
        security_matches = [kw for kw in security_direct_keywords if kw in desc_lower]
        
        if security_matches:
            triggers.append(EscalationTrigger(
                reason=EscalationReason.CRITICAL_SECURITY,
                priority=EscalationPriority.CRITICAL,
                description=f"Direct security concerns: {', '.join(security_matches)}",
                evidence=[f"Security keywords: {', '.join(security_matches)}"],
                confidence=0.95
            ))
        
        # Check for file content analysis (would need actual file content in real implementation)
        for file_path in files_to_modify:
            if any(sec_keyword in file_path.lower() for sec_keyword in ["auth", "security", "crypt", "encrypt"]):
                triggers.append(EscalationTrigger(
                    reason=EscalationReason.CRITICAL_SECURITY,
                    priority=EscalationPriority.HIGH,
                    description=f"Security-sensitive file: {file_path}",
                    evidence=[f"Security file pattern: {file_path}"],
                    confidence=0.85
                ))
        
        return triggers
    
    def _make_escalation_decision(self, triggers: List[EscalationTrigger], task_type: str) -> EscalationAssessment:
        """Make final escalation decision based on all triggers"""
        if not triggers:
            return EscalationAssessment(
                should_escalate=False,
                confidence=0.9,
                triggers=[],
                primary_reason="No escalation triggers detected",
                recommended_model="glm-4.5",
                fallback_model="glm-4.5"
            )
        
        # Calculate overall confidence and priority
        total_confidence = sum(trigger.confidence for trigger in triggers) / len(triggers)
        max_priority = max(trigger.priority.value for trigger in triggers)
        
        # Decision logic
        should_escalate = False
        recommended_model = "glm-4.5"
        fallback_model = "glm-4.5"
        
        # Critical triggers always escalate
        critical_triggers = [t for t in triggers if t.priority == EscalationPriority.CRITICAL]
        if critical_triggers:
            should_escalate = True
            recommended_model = "claude-4.1-opus"
            fallback_model = "glm-4.5"
        
        # High priority triggers with good confidence
        high_triggers = [t for t in triggers if t.priority == EscalationPriority.HIGH]
        if high_triggers and total_confidence >= 0.7:
            should_escalate = True
            recommended_model = "claude-4.1-opus"
            fallback_model = "glm-4.5"
        
        # Medium priority with multiple triggers
        medium_triggers = [t for t in triggers if t.priority == EscalationPriority.MEDIUM]
        if len(medium_triggers) >= 2 and total_confidence > 0.6:
            should_escalate = True
            recommended_model = "claude-4.1-opus"
            fallback_model = "glm-4.5"
        
        # Determine primary reason
        primary_reason = triggers[0].description if triggers else "No specific reason"
        if critical_triggers:
            primary_reason = f"Critical security/architectural concerns: {critical_triggers[0].description}"
        elif high_triggers:
            primary_reason = f"High complexity/risk: {high_triggers[0].description}"
        
        # Cost and risk assessment
        cost_impact = None
        risk_assessment = None
        
        if should_escalate:
            cost_impact = "Higher cost due to Claude 4.1 Opus usage, but justified by risk mitigation"
            risk_assessment = f"Risk of failure with GLM-4.5: {total_confidence:.0%}"
        
        return EscalationAssessment(
            should_escalate=should_escalate,
            confidence=total_confidence,
            triggers=triggers,
            primary_reason=primary_reason,
            recommended_model=recommended_model,
            fallback_model=fallback_model,
            cost_impact_estimate=cost_impact,
            risk_assessment=risk_assessment
        )
    
    def validate_escalation_decision(self, assessment: EscalationAssessment) -> bool:
        """Validate escalation decision with additional checks"""
        # Additional validation could include:
        # - Historical performance data
        # - User preferences
        # - Budget constraints
        # - Time constraints
        
        # For now, basic validation
        if assessment.should_escalate and assessment.confidence < 0.5:
            logger.warning(f"Low confidence escalation decision: {assessment.confidence}")
            return False
        
        return True


# Convenience function for quick escalation checks
def should_escalate_task(
    task_description: str,
    files_to_modify: List[str],
    current_files: Optional[List[str]] = None,
    task_type: str = "implementation"
) -> EscalationAssessment:
    """
    Quick check if a task should be escalated to Claude 4.1 Opus
    
    Args:
        task_description: Description of the task
        files_to_modify: Files that will be modified
        current_files: Current workspace files (optional)
        task_type: Type of task
        
    Returns:
        EscalationAssessment with recommendation
    """
    detector = EscalationDetector()
    return detector.analyze_task_context(
        task_description=task_description,
        files_to_modify=files_to_modify,
        current_files=current_files or [],
        task_type=task_type
    )