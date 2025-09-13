#!/usr/bin/env python3
"""
Criteria Framework Package

Comprehensive decision criteria framework for determining when GLM-4.5 should escalate 
to Claude 4.1 Opus based on task complexity, security implications, and system impact.

This package provides:
- Automated escalation decision making
- Dynamic threshold adjustment
- Cost analysis and optimization
- Confidence scoring and uncertainty management
- Validation and calibration tools
- Comprehensive test coverage

Usage:
    from criteria_framework import AutomatedEscalationSystem, ThresholdConfig
    
    # Create escalation system with custom configuration
    config = ThresholdConfig(
        architect_threshold=0.75,
        integrator_threshold=0.80,
        architect_auto_escalate_threshold=0.90
    )
    
    system = AutomatedEscalationSystem(config)
    
    # Make escalation decision
    context = {
        "affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE, ServiceType.DATABASE},
        "security_factors": {"authentication": True, "authorization": True},
        "performance_factors": {"high_throughput": True, "low_latency_required": True},
        "complexity_factors": {"microservices_coordination": True, "event_driven_design": True}
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="ARCH-001",
        context=context
    )
    
    if decision.should_escalate:
        print(f"Escalate to Claude 4.1 Opus: {decision.escalation_type}")
        print(f"Reasoning: {decision.reasoning}")
        print(f"Estimated cost: ${decision.cost_estimate:.4f}")
    else:
        print("Proceed with GLM-4.5")
"""

__version__ = "1.0.0"
__author__ = "Kyros Praxis Team"

# Core imports
from .escalation_criteria import (
    EscalationFramework,
    DecisionResult,
    CriteriaScore,
    ArchitectCriteria,
    IntegratorCriteria,
    ServiceType,
    RiskLevel,
    extract_service_context,
    extract_security_factors,
    extract_performance_factors,
    framework
)

from .decision_threshold import (
    AutomatedEscalationSystem,
    ThresholdConfig,
    EscalationDecision,
    ConfidenceLevel,
    EscalationType,
    DynamicThresholdManager,
    ConfidenceCalculator,
    CostEstimator,
    create_escalation_system
)

from .validation_system import (
    CriteriaValidator,
    ValidationTestCase,
    ValidationResults,
    ScoringCalibrator,
    create_validator,
    create_calibrator
)

# Package-level convenience functions
def evaluate_escalation(
    role: str,
    task_id: str,
    context: dict,
    force_escalation: bool = False,
    prevent_escalation: bool = False
) -> EscalationDecision:
    """
    Convenience function for quick escalation evaluation.
    
    Args:
        role: Either "architect" or "integrator"
        task_id: Unique identifier for the task
        context: Dictionary containing task context
        force_escalation: Override to force escalation
        prevent_escalation: Override to prevent escalation
    
    Returns:
        EscalationDecision object with recommendation
    """
    system = create_escalation_system()
    return system.make_escalation_decision(
        role=role,
        task_id=task_id,
        context=context,
        force_escalation=force_escalation,
        prevent_escalation=prevent_escalation
)


def validate_framework() -> dict:
    """
    Run comprehensive validation of the criteria framework.
    
    Returns:
        Dictionary with validation results
    """
    validator = create_validator()
    
    results = {}
    results["architect"] = validator.validate_architect_criteria()
    results["integrator"] = validator.validate_integrator_criteria()
    results["edge_cases"] = validator.run_edge_case_tests()
    results["weight_consistency"] = validator.validate_weight_consistency()
    
    return results


def analyze_performance() -> dict:
    """
    Analyze framework performance metrics.
    
    Returns:
        Dictionary with performance analytics
    """
    system = create_escalation_system()
    return system.get_decision_analytics()


__all__ = [
    # Core classes
    "EscalationFramework",
    "DecisionResult", 
    "CriteriaScore",
    "ArchitectCriteria",
    "IntegratorCriteria",
    "ServiceType",
    "RiskLevel",
    "AutomatedEscalationSystem",
    "ThresholdConfig",
    "EscalationDecision",
    "ConfidenceLevel",
    "EscalationType",
    "DynamicThresholdManager",
    "ConfidenceCalculator",
    "CostEstimator",
    "CriteriaValidator",
    "ValidationTestCase",
    "ValidationResults",
    "ScoringCalibrator",
    
    # Utility functions
    "extract_service_context",
    "extract_security_factors", 
    "extract_performance_factors",
    "evaluate_escalation",
    "validate_framework",
    "analyze_performance",
    "create_escalation_system",
    "create_validator",
    "create_calibrator",
    
    # Framework instance
    "framework"
]