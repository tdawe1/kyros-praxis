#!/usr/bin/env python3
"""
Usage Examples for Criteria Framework

This script demonstrates how to use the criteria framework for making
escalation decisions in real-world scenarios.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from criteria_framework import (
    AutomatedEscalationSystem, ThresholdConfig, ServiceType,
    evaluate_escalation, validate_framework, analyze_performance
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def example_1_architect_security_critical():
    """Example 1: Security-critical architectural decision"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Security-Critical Architecture Decision")
    print("="*60)
    
    # Context: Designing authentication system across multiple services
    context = {
        "affected_services": {
            ServiceType.ORCHESTRATOR,
            ServiceType.CONSOLE,
            ServiceType.AUTH,
            ServiceType.DATABASE
        },
        "security_factors": {
            "authentication": True,
            "authorization": True,
            "data_encryption": True,
            "input_validation": True,
            "csrf_protection": True
        },
        "performance_factors": {
            "high_throughput": True,
            "low_latency_required": True,
            "scalability_constraints": True
        },
        "complexity_factors": {
            "microservices_coordination": True,
            "event_driven_design": True,
            "distributed_transactions": True,
            "service_discovery": True,
            "load_balancing": True
        }
    }
    
    # Make decision
    decision = evaluate_escalation(
        role="architect",
        task_id="AUTH-SYSTEM-DESIGN-001",
        context=context
    )
    
    # Display results
    print(f"Task: AUTH-SYSTEM-DESIGN-001")
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATION'}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Confidence: {decision.confidence.name}")
    print(f"Score: {decision.certainty_score:.3f}")
    print(f"Cost Estimate: ${decision.cost_estimate:.4f}")
    print(f"Reasoning:")
    for reason in decision.reasoning:
        print(f"  - {reason}")
    
    if decision.alternatives:
        print(f"Alternatives:")
        for alt in decision.alternatives:
            print(f"  - {alt}")


def example_2_integrator_major_merge_conflict():
    """Example 2: Major merge conflict resolution"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Major Merge Conflict Resolution")
    print("="*60)
    
    # Context: Resolving conflicts in a complex merge
    context = {
        "conflict_factors": {
            "multiple_service_conflicts": True,
            "api_contract_breaks": True,
            "data_model_conflicts": True,
            "dependency_chain_breaks": True,
            "migration_conflicts": True
        },
        "boundary_factors": {
            "authentication_boundary": True,
            "data_boundary": True,
            "service_boundary": True,
            "api_boundary": True,
            "infrastructure_boundary": True
        },
        "integration_factors": {
            "cross_service_dependencies": True,
            "version_conflicts": True,
            "schema_migrations": True,
            "configuration_drift": True,
            "test_integration": True,
            "deployment_coordination": True
        },
        "risk_factors": {
            "data_loss_risk": True,
            "service_disruption_risk": True,
            "rollback_complexity": True,
            "deployment_failure_risk": True,
            "performance_regression_risk": True
        }
    }
    
    # Make decision
    decision = evaluate_escalation(
        role="integrator",
        task_id="MERGE-CONFLICT-RESOLUTION-001",
        context=context
    )
    
    # Display results
    print(f"Task: MERGE-CONFLICT-RESOLUTION-001")
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATION'}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Risk Score: {decision.risk_score:.3f}")
    print(f"Uncertainty: {decision.uncertainty_score:.3f}")
    print(f"Reasoning:")
    for reason in decision.reasoning:
        print(f"  - {reason}")


def example_3_performance_critical_optimization():
    """Example 3: Performance-critical optimization"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Performance-Critical Optimization")
    print("="*60)
    
    # Context: Optimizing real-time data processing pipeline
    context = {
        "affected_services": {
            ServiceType.ORCHESTRATOR,
            ServiceType.DATABASE,
            ServiceType.CACHE
        },
        "security_factors": {
            "authentication": False,
            "authorization": True,
            "data_encryption": False,
            "input_validation": True,
            "csrf_protection": False
        },
        "performance_factors": {
            "high_throughput": True,
            "low_latency_required": True,
            "scalability_constraints": True,
            "resource_intensive": True,
            "real_time_requirements": True
        },
        "complexity_factors": {
            "microservices_coordination": True,
            "event_driven_design": True,
            "distributed_transactions": True,
            "circuit_breakers": False,
            "service_discovery": True
        }
    }
    
    # Make decision
    decision = evaluate_escalation(
        role="architect",
        task_id="PERFORMANCE-OPTIMIZATION-001",
        context=context
    )
    
    # Display results
    print(f"Task: PERFORMANCE-OPTIMIZATION-001")
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATION'}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Score: {decision.certainty_score:.3f}")
    print(f"Reasoning:")
    for reason in decision.reasoning:
        print(f"  - {reason}")


def example_4_simple_feature_implementation():
    """Example 4: Simple feature implementation (no escalation)"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Simple Feature Implementation")
    print("="*60)
    
    # Context: Adding a simple feature to a single service
    context = {
        "affected_services": {
            ServiceType.CONSOLE
        },
        "security_factors": {
            "authentication": False,
            "authorization": False,
            "data_encryption": False,
            "input_validation": True,
            "csrf_protection": False
        },
        "performance_factors": {
            "high_throughput": False,
            "low_latency_required": False,
            "scalability_constraints": False,
            "resource_intensive": False,
            "real_time_requirements": False
        },
        "complexity_factors": {
            "microservices_coordination": False,
            "event_driven_design": False,
            "distributed_transactions": False,
            "circuit_breakers": False,
            "service_discovery": False
        }
    }
    
    # Make decision
    decision = evaluate_escalation(
        role="architect",
        task_id="SIMPLE-FEATURE-001",
        context=context
    )
    
    # Display results
    print(f"Task: SIMPLE-FEATURE-001")
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATION'}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Score: {decision.certainty_score:.3f}")
    print(f"Reasoning:")
    for reason in decision.reasoning:
        print(f"  - {reason}")


def example_5_custom_threshold_configuration():
    """Example 5: Using custom threshold configuration"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Custom Threshold Configuration")
    print("="*60)
    
    # Create custom configuration
    config = ThresholdConfig(
        architect_threshold=0.80,  # Higher threshold
        integrator_threshold=0.85,  # Higher threshold
        architect_auto_escalate_threshold=0.95,  # Higher auto-escalate
        enable_dynamic_thresholds=True,
        adjustment_rate=0.03,  # More conservative adjustments
        max_escalations_per_hour=5,  # Stricter rate limiting
        cost_threshold_per_escalation=0.30  # Lower cost threshold
    )
    
    # Create system with custom config
    system = AutomatedEscalationSystem(config)
    
    # Test with borderline case
    context = {
        "affected_services": {
            ServiceType.ORCHESTRATOR,
            ServiceType.CONSOLE,
            ServiceType.DATABASE
        },
        "security_factors": {
            "authentication": True,
            "authorization": False,
            "data_encryption": True,
            "input_validation": False,
            "csrf_protection": False
        },
        "performance_factors": {
            "high_throughput": True,
            "low_latency_required": False,
            "scalability_constraints": True,
            "resource_intensive": False,
            "real_time_requirements": False
        },
        "complexity_factors": {
            "microservices_coordination": True,
            "event_driven_design": False,
            "distributed_transactions": False,
            "circuit_breakers": False,
            "service_discovery": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="BORDERLINE-CASE-001",
        context=context
    )
    
    print(f"Custom Configuration Results:")
    print(f"Architect Threshold: {config.architect_threshold}")
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATION'}")
    print(f"Score: {decision.certainty_score:.3f} vs Threshold: {config.architect_threshold}")
    print(f"Type: {decision.escalation_type.value}")


def example_6_batch_processing():
    """Example 6: Batch processing of multiple tasks"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Batch Processing Multiple Tasks")
    print("="*60)
    
    # Define multiple tasks for batch processing
    tasks = [
        {
            "role": "architect",
            "task_id": "BATCH-ARCH-001",
            "context": {
                "affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE},
                "security_factors": {"authentication": True},
                "performance_factors": {"high_throughput": True},
                "complexity_factors": {"microservices_coordination": True}
            }
        },
        {
            "role": "integrator",
            "task_id": "BATCH-INT-001",
            "context": {
                "conflict_factors": {"multiple_service_conflicts": True},
                "boundary_factors": {"service_boundary": True},
                "integration_factors": {"cross_service_dependencies": True},
                "risk_factors": {"data_loss_risk": True}
            }
        },
        {
            "role": "architect",
            "task_id": "BATCH-ARCH-002",
            "context": {
                "affected_services": {ServiceType.ORCHESTRATOR},
                "security_factors": {"authentication": False},
                "performance_factors": {"high_throughput": False},
                "complexity_factors": {"microservices_coordination": False}
            }
        }
    ]
    
    # Process all tasks
    system = AutomatedEscalationSystem()
    results = []
    
    for task in tasks:
        decision = system.make_escalation_decision(
            role=task["role"],
            task_id=task["task_id"],
            context=task["context"]
        )
        results.append((task["task_id"], decision))
    
    # Display batch results
    print("Batch Processing Results:")
    print("-" * 40)
    
    escalations = 0
    for task_id, decision in results:
        status = "ESCALATE" if decision.should_escalate else "NO ESCALATE"
        cost = f"${decision.cost_estimate:.4f}"
        print(f"{task_id}: {status} (Cost: {cost})")
        
        if decision.should_escalate:
            escalations += 1
    
    print(f"\nSummary:")
    print(f"Total Tasks: {len(tasks)}")
    print(f"Escalations: {escalations}")
    print(f"Escalation Rate: {escalations/len(tasks)*100:.1f}%")
    
    # Show analytics
    analytics = system.get_decision_analytics()
    print(f"\nAnalytics:")
    print(f"Total Estimated Cost: ${analytics['costs']['total_estimated_cost']:.4f}")


def example_7_validation_and_calibration():
    """Example 7: Framework validation and calibration"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Framework Validation and Calibration")
    print("="*60)
    
    # Run validation
    print("Running framework validation...")
    validation_results = validate_framework()
    
    # Display validation results
    print("\nValidation Results:")
    print("-" * 30)
    
    for role, results in validation_results.items():
        if isinstance(results, dict):
            if role == "weight_consistency":
                print(f"{role}: {'PASS' if all(results.values()) else 'FAIL'}")
            else:
                continue
        else:
            print(f"{role}: {results.passed}/{results.total_tests} passed ({results.pass_rate*100:.1f}%)")
    
    # Analyze performance
    print("\nPerformance Analysis:")
    print("-" * 30)
    performance = analyze_performance()
    
    if isinstance(performance, dict) and "summary" in performance:
        summary = performance["summary"]
        print(f"Total Decisions: {summary['total_decisions']}")
        print(f"Escalation Rate: {summary['escalation_rate']*100:.1f}%")
        print(f"Auto-Escalation Rate: {summary['automatic_escalation_rate']*100:.1f}%")
    else:
        print("No decision data available")


def example_8_context_extraction_utilities():
    """Example 8: Using context extraction utilities"""
    print("\n" + "="*60)
    print("EXAMPLE 8: Context Extraction Utilities")
    print("="*60)
    
    # Example files and messages
    files_changed = [
        "services/orchestrator/main.py",
        "services/console/src/components/AuthForm.tsx",
        "services/orchestrator/models.py",
        "services/orchestrator/auth.py",
        "services/console/src/api/client.ts"
    ]
    
    commit_messages = [
        "Add JWT authentication middleware",
        "Implement user login form with validation",
        "Update user model with encrypted password field",
        "Add OAuth2 integration for third-party authentication"
    ]
    
    # Extract contexts
    from criteria_framework import extract_service_context, extract_security_factors, extract_performance_factors
    
    print("File Analysis:")
    print("-" * 20)
    services = extract_service_context(files_changed)
    print(f"Services affected: {[s.value for s in services]}")
    
    print("\nSecurity Analysis:")
    print("-" * 20)
    security_factors = extract_security_factors(files_changed, commit_messages)
    for factor, present in security_factors.items():
        print(f"{factor}: {'YES' if present else 'NO'}")
    
    print("\nPerformance Analysis:")
    print("-" * 20)
    perf_factors = extract_performance_factors(files_changed, commit_messages)
    for factor, present in perf_factors.items():
        print(f"{factor}: {'YES' if present else 'NO'}")
    
    # Make decision based on extracted context
    context = {
        "affected_services": services,
        "security_factors": security_factors,
        "performance_factors": perf_factors,
        "complexity_factors": {"microservices_coordination": True}
    }
    
    decision = evaluate_escalation(
        role="architect",
        task_id="CONTEXT-EXTRACTION-001",
        context=context
    )
    
    print(f"\nDecision based on extracted context: {'ESCALATE' if decision.should_escalate else 'NO ESCALATE'}")


def main():
    """Run all examples"""
    print("CRITERIA FRAMEWORK USAGE EXAMPLES")
    print("=" * 60)
    
    try:
        # Run all examples
        example_1_architect_security_critical()
        example_2_integrator_major_merge_conflict()
        example_3_performance_critical_optimization()
        example_4_simple_feature_implementation()
        example_5_custom_threshold_configuration()
        example_6_batch_processing()
        example_7_validation_and_calibration()
        example_8_context_extraction_utilities()
        
        print("\n" + "="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()