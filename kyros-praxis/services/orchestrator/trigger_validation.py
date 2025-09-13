"""
Trigger Validation Mechanisms

This module provides comprehensive validation for escalation triggers to ensure
accurate and reliable escalation decisions. It includes rule-based validation,
historical validation, cost-benefit analysis, and performance monitoring.

VALIDATION COMPONENTS:
1. Rule Validator - Validates triggers against business rules
2. Historical Validator - Uses historical data for validation
3. Cost-Benefit Analyzer - Analyzes cost vs benefit of escalation
4. Performance Monitor - Tracks validation performance
5. Confidence Calculator - Calculates overall confidence scores
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from collections import defaultdict, Counter

from .escalation_triggers import (
    EscalationDetector,
    EscalationAssessment,
    EscalationTrigger,
    EscalationReason,
    EscalationPriority
)
from .context_analysis import (
    ContextAnalyzer,
    ContextAnalysisResult,
    ComplexityLevel,
    BusinessImpact,
    RiskLevel
)

logger = logging.getLogger(__name__)


class ValidationRule(Enum):
    """Types of validation rules"""
    
    BUSINESS_RULE = "business_rule"          # Business-specific rules
    TECHNICAL_RULE = "technical_rule"        # Technical validation rules
    COST_RULE = "cost_rule"                  # Cost-related rules
    QUALITY_RULE = "quality_rule"            # Quality assurance rules
    SECURITY_RULE = "security_rule"          # Security validation rules


class ValidationResult(Enum):
    """Validation result types"""
    
    VALID = "valid"                          # Trigger is valid
    INVALID = "invalid"                      # Trigger is invalid
    PARTIALLY_VALID = "partially_valid"      # Trigger is partially valid
    REQUIRES_REVIEW = "requires_review"      # Requires manual review
    INSUFFICIENT_DATA = "insufficient_data"  # Not enough data to validate


@dataclass
class ValidationCheck:
    """Individual validation check result"""
    
    rule_type: ValidationRule
    rule_name: str
    result: ValidationResult
    confidence: float
    message: str
    evidence: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report for an escalation trigger"""
    
    trigger_id: str
    trigger_type: EscalationReason
    overall_result: ValidationResult
    overall_confidence: float
    checks: List[ValidationCheck]
    validation_timestamp: datetime
    validator_version: str
    metadata: Dict[str, Any]


@dataclass
class CostBenefitAnalysis:
    """Cost-benefit analysis for escalation"""
    
    estimated_cost: float
    estimated_benefit: float
    roi_score: float
    risk_mitigation_value: float
    quality_improvement_value: float
    time_savings_value: float
    recommendation: str


@dataclass
class HistoricalValidation:
    """Historical validation data"""
    
    total_validations: int
    successful_validations: int
    false_positives: int
    false_negatives: int
    average_confidence: float
    recent_performance: List[Dict[str, Any]]
    improvement_suggestions: List[str]


class TriggerValidator:
    """
    Comprehensive trigger validation system
    
    This class validates escalation triggers using multiple validation
    strategies to ensure accurate and reliable escalation decisions.
    """
    
    def __init__(self):
        # Validation rules
        self.business_rules = self._initialize_business_rules()
        self.technical_rules = self._initialize_technical_rules()
        self.cost_rules = self._initialize_cost_rules()
        self.quality_rules = self._initialize_quality_rules()
        self.security_rules = self._initialize_security_rules()
        
        # Historical data (in-memory, could be database-backed)
        self.validation_history: List[ValidationReport] = []
        self.performance_metrics = {
            "total_validations": 0,
            "valid_triggers": 0,
            "invalid_triggers": 0,
            "average_confidence": 0.0,
            "validation_time_avg": 0.0
        }
        
        # Configuration
        self.min_confidence_threshold = 0.7
        self.cost_threshold = 10.0  # Maximum cost before requiring review
        self.risk_threshold = 0.8  # Risk threshold for automatic escalation
    
    def _initialize_business_rules(self) -> List[Dict[str, Any]]:
        """Initialize business validation rules"""
        return [
            {
                "name": "business_impact_threshold",
                "description": "Validate business impact is sufficient for escalation",
                "condition": lambda context: context.get("business_impact") in [BusinessImpact.HIGH, BusinessImpact.CRITICAL],
                "weight": 0.3
            },
            {
                "name": "revenue_critical_path",
                "description": "Check if task affects revenue-critical paths",
                "condition": lambda context: any(keyword in context.get("task_description", "").lower() 
                                               for keyword in ["revenue", "billing", "payment", "checkout"]),
                "weight": 0.4
            },
            {
                "name": "compliance_requirement",
                "description": "Validate compliance-related tasks",
                "condition": lambda context: any(keyword in context.get("task_description", "").lower() 
                                               for keyword in ["compliance", "audit", "gdpr", "hipaa"]),
                "weight": 0.5
            }
        ]
    
    def _initialize_technical_rules(self) -> List[Dict[str, Any]]:
        """Initialize technical validation rules"""
        return [
            {
                "name": "complexity_threshold",
                "description": "Validate technical complexity meets threshold",
                "condition": lambda context: context.get("complexity_level") in [ComplexityLevel.COMPLEX, ComplexityLevel.CRITICAL],
                "weight": 0.3
            },
            {
                "name": "multi_service_dependency",
                "description": "Check for cross-service dependencies",
                "condition": lambda context: len(context.get("cross_service_dependencies", [])) > 0,
                "weight": 0.4
            },
            {
                "name": "database_schema_change",
                "description": "Validate database schema changes",
                "condition": lambda context: any("schema" in f.lower() or "migration" in f.lower() 
                                               for f in context.get("files_to_modify", [])),
                "weight": 0.35
            }
        ]
    
    def _initialize_cost_rules(self) -> List[Dict[str, Any]]:
        """Initialize cost validation rules"""
        return [
            {
                "name": "cost_benefit_ratio",
                "description": "Validate cost-benefit ratio is acceptable",
                "condition": lambda context: self._calculate_cost_benefit_ratio(context) > 1.0,
                "weight": 0.4
            },
            {
                "name": "budget_threshold",
                "description": "Check if escalation exceeds budget threshold",
                "condition": lambda context: self._estimate_escalation_cost(context) <= self.cost_threshold,
                "weight": 0.3
            },
            {
                "name": "roi_positive",
                "description": "Ensure positive ROI for escalation",
                "condition": lambda context: self._calculate_roi(context) > 0,
                "weight": 0.3
            }
        ]
    
    def _initialize_quality_rules(self) -> List[Dict[str, Any]]:
        """Initialize quality validation rules"""
        return [
            {
                "name": "testing_complexity",
                "description": "Validate testing complexity requires escalation",
                "condition": lambda context: context.get("testing_complexity") in [ComplexityLevel.COMPLEX, ComplexityLevel.CRITICAL],
                "weight": 0.3
            },
            {
                "name": "code_review_requirement",
                "description": "Check if comprehensive code review is needed",
                "condition": lambda context: context.get("review_complexity") in [ComplexityLevel.COMPLEX, ComplexityLevel.CRITICAL],
                "weight": 0.35
            },
            {
                "name": "documentation_needs",
                "description": "Validate documentation requirements",
                "condition": lambda context: context.get("documentation_needs") in [BusinessImpact.HIGH, BusinessImpact.CRITICAL],
                "weight": 0.25
            }
        ]
    
    def _initialize_security_rules(self) -> List[Dict[str, Any]]:
        """Initialize security validation rules"""
        return [
            {
                "name": "security_critical_path",
                "description": "Validate security-critical file modifications",
                "condition": lambda context: any("auth" in f.lower() or "security" in f.lower() or "crypt" in f.lower() 
                                               for f in context.get("files_to_modify", [])),
                "weight": 0.5
            },
            {
                "name": "vulnerability_fix",
                "description": "Check if task involves vulnerability fixes",
                "condition": lambda context: any(keyword in context.get("task_description", "").lower() 
                                               for keyword in ["vulnerability", "exploit", "security", "patch"]),
                "weight": 0.4
            },
            {
                "name": "compliance_security",
                "description": "Validate compliance-related security requirements",
                "condition": lambda context: any(keyword in context.get("task_description", "").lower() 
                                               for keyword in ["compliance", "audit", "certification"]),
                "weight": 0.35
            }
        ]
    
    def validate_escalation_trigger(
        self,
        trigger: EscalationTrigger,
        context: Dict[str, Any],
        assessment: Optional[EscalationAssessment] = None,
        context_analysis: Optional[ContextAnalysisResult] = None
    ) -> ValidationReport:
        """
        Validate an escalation trigger against all rules
        
        Args:
            trigger: The escalation trigger to validate
            context: Context information for validation
            assessment: Optional escalation assessment
            context_analysis: Optional context analysis result
            
        Returns:
            ValidationReport with validation results
        """
        
        validation_id = f"val_{int(time.time())}_{hash(trigger.description) % 10000:04d}"
        
        # Prepare context for validation
        validation_context = {
            "trigger": trigger,
            "task_description": context.get("task_description", ""),
            "files_to_modify": context.get("files_to_modify", []),
            "current_files": context.get("current_files", []),
            "task_type": context.get("task_type", "implementation")
        }
        
        # Add assessment and context analysis data if available
        if assessment:
            validation_context.update({
                "should_escalate": assessment.should_escalate,
                "confidence": assessment.confidence,
                "triggers": assessment.triggers
            })
        
        if context_analysis:
            validation_context.update({
                "complexity_level": context_analysis.overall_complexity,
                "business_impact": context_analysis.business_impact.overall_impact,
                "risk_level": context_analysis.risk_assessment.overall_risk,
                "cross_service_dependencies": context_analysis.dependencies.cross_service_dependencies,
                "testing_complexity": context_analysis.quality_requirements.testing_complexity,
                "review_complexity": context_analysis.quality_requirements.review_complexity,
                "documentation_needs": context_analysis.quality_requirements.documentation_needs
            })
        
        # Perform validation checks
        validation_checks = []
        
        # Business rule validation
        validation_checks.extend(self._validate_business_rules(validation_context))
        
        # Technical rule validation
        validation_checks.extend(self._validate_technical_rules(validation_context))
        
        # Cost rule validation
        validation_checks.extend(self._validate_cost_rules(validation_context))
        
        # Quality rule validation
        validation_checks.extend(self._validate_quality_rules(validation_context))
        
        # Security rule validation
        validation_checks.extend(self._validate_security_rules(validation_context))
        
        # Calculate overall result
        overall_result, overall_confidence = self._calculate_overall_result(validation_checks)
        
        # Create validation report
        report = ValidationReport(
            trigger_id=validation_id,
            trigger_type=trigger.reason,
            overall_result=overall_result,
            overall_confidence=overall_confidence,
            checks=validation_checks,
            validation_timestamp=datetime.utcnow(),
            validator_version="1.0.0",
            metadata={
                "context": validation_context,
                "validation_duration": 0.0,  # Would track actual duration
                "rules_applied": len(validation_checks)
            }
        )
        
        # Store validation history
        self.validation_history.append(report)
        
        # Update performance metrics
        self._update_performance_metrics(report)
        
        logger.info(f"Validation complete for trigger {trigger.reason.value}: {overall_result.value} ({overall_confidence:.2f})")
        
        return report
    
    def _validate_business_rules(self, context: Dict[str, Any]) -> List[ValidationCheck]:
        """Validate against business rules"""
        checks = []
        
        for rule in self.business_rules:
            try:
                result = rule["condition"](context)
                
                validation_result = ValidationResult.VALID if result else ValidationResult.INVALID
                confidence = rule["weight"]
                
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.BUSINESS_RULE,
                    rule_name=rule["name"],
                    result=validation_result,
                    confidence=confidence,
                    message=rule["description"],
                    evidence={"context": context, "result": result},
                    recommendation="Validated" if result else "Review required"
                ))
                
            except Exception as e:
                logger.error(f"Error in business rule {rule['name']}: {str(e)}")
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.BUSINESS_RULE,
                    rule_name=rule["name"],
                    result=ValidationResult.INSUFFICIENT_DATA,
                    confidence=0.0,
                    message=f"Rule execution error: {str(e)}",
                    evidence={"error": str(e)},
                    recommendation="Manual review required"
                ))
        
        return checks
    
    def _validate_technical_rules(self, context: Dict[str, Any]) -> List[ValidationCheck]:
        """Validate against technical rules"""
        checks = []
        
        for rule in self.technical_rules:
            try:
                result = rule["condition"](context)
                
                validation_result = ValidationResult.VALID if result else ValidationResult.INVALID
                confidence = rule["weight"]
                
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.TECHNICAL_RULE,
                    rule_name=rule["name"],
                    result=validation_result,
                    confidence=confidence,
                    message=rule["description"],
                    evidence={"context": context, "result": result},
                    recommendation="Validated" if result else "Consider alternatives"
                ))
                
            except Exception as e:
                logger.error(f"Error in technical rule {rule['name']}: {str(e)}")
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.TECHNICAL_RULE,
                    rule_name=rule["name"],
                    result=ValidationResult.INSUFFICIENT_DATA,
                    confidence=0.0,
                    message=f"Rule execution error: {str(e)}",
                    evidence={"error": str(e)},
                    recommendation="Technical review required"
                ))
        
        return checks
    
    def _validate_cost_rules(self, context: Dict[str, Any]) -> List[ValidationCheck]:
        """Validate against cost rules"""
        checks = []
        
        for rule in self.cost_rules:
            try:
                result = rule["condition"](context)
                
                validation_result = ValidationResult.VALID if result else ValidationResult.INVALID
                confidence = rule["weight"]
                
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.COST_RULE,
                    rule_name=rule["name"],
                    result=validation_result,
                    confidence=confidence,
                    message=rule["description"],
                    evidence={"context": context, "result": result},
                    recommendation="Cost-effective" if result else "Cost review needed"
                ))
                
            except Exception as e:
                logger.error(f"Error in cost rule {rule['name']}: {str(e)}")
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.COST_RULE,
                    rule_name=rule["name"],
                    result=ValidationResult.INSUFFICIENT_DATA,
                    confidence=0.0,
                    message=f"Rule execution error: {str(e)}",
                    evidence={"error": str(e)},
                    recommendation="Cost analysis required"
                ))
        
        return checks
    
    def _validate_quality_rules(self, context: Dict[str, Any]) -> List[ValidationCheck]:
        """Validate against quality rules"""
        checks = []
        
        for rule in self.quality_rules:
            try:
                result = rule["condition"](context)
                
                validation_result = ValidationResult.VALID if result else ValidationResult.INVALID
                confidence = rule["weight"]
                
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.QUALITY_RULE,
                    rule_name=rule["name"],
                    result=validation_result,
                    confidence=confidence,
                    message=rule["description"],
                    evidence={"context": context, "result": result},
                    recommendation="Quality assured" if result else "Quality improvements needed"
                ))
                
            except Exception as e:
                logger.error(f"Error in quality rule {rule['name']}: {str(e)}")
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.QUALITY_RULE,
                    rule_name=rule["name"],
                    result=ValidationResult.INSUFFICIENT_DATA,
                    confidence=0.0,
                    message=f"Rule execution error: {str(e)}",
                    evidence={"error": str(e)},
                    recommendation="Quality review required"
                ))
        
        return checks
    
    def _validate_security_rules(self, context: Dict[str, Any]) -> List[ValidationCheck]:
        """Validate against security rules"""
        checks = []
        
        for rule in self.security_rules:
            try:
                result = rule["condition"](context)
                
                validation_result = ValidationResult.VALID if result else ValidationResult.INVALID
                confidence = rule["weight"]
                
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.SECURITY_RULE,
                    rule_name=rule["name"],
                    result=validation_result,
                    confidence=confidence,
                    message=rule["description"],
                    evidence={"context": context, "result": result},
                    recommendation="Security validated" if result else "Security review required"
                ))
                
            except Exception as e:
                logger.error(f"Error in security rule {rule['name']}: {str(e)}")
                checks.append(ValidationCheck(
                    rule_type=ValidationRule.SECURITY_RULE,
                    rule_name=rule["name"],
                    result=ValidationResult.INSUFFICIENT_DATA,
                    confidence=0.0,
                    message=f"Rule execution error: {str(e)}",
                    evidence={"error": str(e)},
                    recommendation="Security assessment required"
                ))
        
        return checks
    
    def _calculate_overall_result(self, checks: List[ValidationCheck]) -> Tuple[ValidationResult, float]:
        """Calculate overall validation result and confidence"""
        if not checks:
            return ValidationResult.INSUFFICIENT_DATA, 0.0
        
        # Calculate weighted confidence
        total_weight = sum(check.confidence for check in checks)
        valid_weight = sum(check.confidence for check in checks if check.result == ValidationResult.VALID)
        
        overall_confidence = valid_weight / total_weight if total_weight > 0 else 0.0
        
        # Determine overall result
        valid_count = sum(1 for check in checks if check.result == ValidationResult.VALID)
        invalid_count = sum(1 for check in checks if check.result == ValidationResult.INVALID)
        requires_review_count = sum(1 for check in checks if check.result == ValidationResult.REQUIRES_REVIEW)
        
        if valid_count == len(checks):
            overall_result = ValidationResult.VALID
        elif invalid_count > len(checks) * 0.5:
            overall_result = ValidationResult.INVALID
        elif requires_review_count > 0:
            overall_result = ValidationResult.REQUIRES_REVIEW
        else:
            overall_result = ValidationResult.PARTIALLY_VALID
        
        return overall_result, overall_confidence
    
    def _calculate_cost_benefit_ratio(self, context: Dict[str, Any]) -> float:
        """Calculate cost-benefit ratio for escalation"""
        # Simplified cost-benefit calculation
        estimated_cost = self._estimate_escalation_cost(context)
        estimated_benefit = self._estimate_escalation_benefit(context)
        
        return estimated_benefit / estimated_cost if estimated_cost > 0 else 0.0
    
    def _estimate_escalation_cost(self, context: Dict[str, Any]) -> float:
        """Estimate cost of escalation"""
        # Simplified cost estimation
        base_cost = 5.0  # Base cost for Claude 4.1 Opus
        
        # Add complexity factor
        complexity_level = context.get("complexity_level", ComplexityLevel.SIMPLE)
        complexity_multiplier = {
            ComplexityLevel.SIMPLE: 1.0,
            ComplexityLevel.MODERATE: 1.5,
            ComplexityLevel.COMPLEX: 2.0,
            ComplexityLevel.CRITICAL: 3.0
        }
        
        # Add file count factor
        file_count = len(context.get("files_to_modify", []))
        file_multiplier = 1.0 + (file_count * 0.1)
        
        total_cost = base_cost * complexity_multiplier.get(complexity_level, 1.0) * file_multiplier
        
        return total_cost
    
    def _estimate_escalation_benefit(self, context: Dict[str, Any]) -> float:
        """Estimate benefit of escalation"""
        # Simplified benefit estimation
        base_benefit = 10.0  # Base benefit value
        
        # Add risk mitigation value
        risk_level = context.get("risk_level", RiskLevel.LOW)
        risk_multiplier = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 1.5,
            RiskLevel.HIGH: 2.0,
            RiskLevel.CRITICAL: 3.0
        }
        
        # Add business impact value
        business_impact = context.get("business_impact", BusinessImpact.LOW)
        business_multiplier = {
            BusinessImpact.LOW: 1.0,
            BusinessImpact.MEDIUM: 1.5,
            BusinessImpact.HIGH: 2.0,
            BusinessImpact.CRITICAL: 3.0
        }
        
        total_benefit = base_benefit * risk_multiplier.get(risk_level, 1.0) * business_multiplier.get(business_impact, 1.0)
        
        return total_benefit
    
    def _calculate_roi(self, context: Dict[str, Any]) -> float:
        """Calculate return on investment for escalation"""
        cost = self._estimate_escalation_cost(context)
        benefit = self._estimate_escalation_benefit(context)
        
        return (benefit - cost) / cost if cost > 0 else 0.0
    
    def _update_performance_metrics(self, report: ValidationReport) -> None:
        """Update performance metrics"""
        self.performance_metrics["total_validations"] += 1
        
        if report.overall_result == ValidationResult.VALID:
            self.performance_metrics["valid_triggers"] += 1
        else:
            self.performance_metrics["invalid_triggers"] += 1
        
        # Update average confidence
        total = self.performance_metrics["total_validations"]
        current_avg = self.performance_metrics["average_confidence"]
        new_confidence = report.overall_confidence
        
        self.performance_metrics["average_confidence"] = (current_avg * (total - 1) + new_confidence) / total
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            **self.performance_metrics,
            "validation_history_size": len(self.validation_history),
            "rules_count": {
                "business": len(self.business_rules),
                "technical": len(self.technical_rules),
                "cost": len(self.cost_rules),
                "quality": len(self.quality_rules),
                "security": len(self.security_rules)
            },
            "recent_validations": [
                {
                    "trigger_type": report.trigger_type.value,
                    "result": report.overall_result.value,
                    "confidence": report.overall_confidence,
                    "timestamp": report.validation_timestamp.isoformat()
                }
                for report in self.validation_history[-10:]  # Last 10 validations
            ]
        }
    
    def analyze_historical_performance(self, days: int = 30) -> HistoricalValidation:
        """Analyze historical validation performance"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_validations = [
            report for report in self.validation_history
            if report.validation_timestamp >= cutoff_date
        ]
        
        if not recent_validations:
            return HistoricalValidation(
                total_validations=0,
                successful_validations=0,
                false_positives=0,
                false_negatives=0,
                average_confidence=0.0,
                recent_performance=[],
                improvement_suggestions=["Need more validation data for analysis"]
            )
        
        successful_validations = sum(1 for report in recent_validations 
                                    if report.overall_result == ValidationResult.VALID)
        
        # These would be tracked based on actual outcomes
        false_positives = 0  # Valid triggers that shouldn't have escalated
        false_negatives = 0  # Invalid triggers that should have escalated
        
        average_confidence = sum(report.overall_confidence for report in recent_validations) / len(recent_validations)
        
        recent_performance = [
            {
                "date": report.validation_timestamp.date().isoformat(),
                "total_validations": len([r for r in recent_validations if r.validation_timestamp.date() == report.validation_timestamp.date()]),
                "success_rate": len([r for r in recent_validations if r.validation_timestamp.date() == report.validation_timestamp.date() and r.overall_result == ValidationResult.VALID]) / max(1, len([r for r in recent_validations if r.validation_timestamp.date() == report.validation_timestamp.date()]))
            }
            for report in recent_validations[-7:]  # Last 7 days
        ]
        
        improvement_suggestions = self._generate_improvement_suggestions(recent_validations)
        
        return HistoricalValidation(
            total_validations=len(recent_validations),
            successful_validations=successful_validations,
            false_positives=false_positives,
            false_negatives=false_negatives,
            average_confidence=average_confidence,
            recent_performance=recent_performance,
            improvement_suggestions=improvement_suggestions
        )
    
    def _generate_improvement_suggestions(self, validations: List[ValidationReport]) -> List[str]:
        """Generate improvement suggestions based on validation history"""
        suggestions = []
        
        # Analyze common failure patterns
        failed_validations = [v for v in validations if v.overall_result != ValidationResult.VALID]
        
        if failed_validations:
            # Find common failed rules
            failed_rules = Counter()
            for validation in failed_validations:
                for check in validation.checks:
                    if check.result != ValidationResult.VALID:
                        failed_rules[check.rule_name] += 1
            
            common_failures = failed_rules.most_common(3)
            
            for rule_name, count in common_failures:
                if count > len(failed_validations) * 0.3:  # Fails in >30% of cases
                    suggestions.append(f"Review and adjust rule '{rule_name}' - fails frequently")
        
        # Check confidence levels
        avg_confidence = sum(v.overall_confidence for v in validations) / len(validations)
        if avg_confidence < 0.7:
            suggestions.append("Consider adjusting validation rules to improve confidence scores")
        
        # Check for validation patterns
        recent_performance = validations[-10:]  # Last 10 validations
        if len(recent_performance) >= 5:
            recent_success_rate = sum(1 for v in recent_performance if v.overall_result == ValidationResult.VALID) / len(recent_performance)
            if recent_success_rate < 0.8:
                suggestions.append("Recent validation success rate is low - consider rule adjustments")
        
        return suggestions


# Global validator instance
_validator: Optional[TriggerValidator] = None


def get_trigger_validator() -> TriggerValidator:
    """Get the global trigger validator instance"""
    global _validator
    if _validator is None:
        _validator = TriggerValidator()
    return _validator


# Convenience functions
def validate_escalation_trigger(
    trigger: EscalationTrigger,
    context: Dict[str, Any],
    assessment: Optional[EscalationAssessment] = None,
    context_analysis: Optional[ContextAnalysisResult] = None
) -> ValidationReport:
    """
    Validate an escalation trigger
    
    Args:
        trigger: The escalation trigger to validate
        context: Context information
        assessment: Optional escalation assessment
        context_analysis: Optional context analysis
        
    Returns:
        ValidationReport with validation results
    """
    validator = get_trigger_validator()
    return validator.validate_escalation_trigger(trigger, context, assessment, context_analysis)


def get_validation_statistics() -> Dict[str, Any]:
    """Get validation statistics"""
    validator = get_trigger_validator()
    return validator.get_validation_statistics()


def analyze_validation_performance(days: int = 30) -> HistoricalValidation:
    """Analyze historical validation performance"""
    validator = get_trigger_validator()
    return validator.analyze_historical_performance(days)