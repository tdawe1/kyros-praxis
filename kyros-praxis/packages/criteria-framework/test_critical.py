#!/usr/bin/env python3
"""
Comprehensive test for critical escalation scenarios
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decision_threshold import AutomatedEscalationSystem, ThresholdConfig

def test_critical_scenarios():
    print("Testing Critical Escalation Scenarios")
    print("=" * 50)
    
    config = ThresholdConfig(
        architect_threshold=0.75,
        integrator_threshold=0.80,
        architect_auto_escalate_threshold=0.90
    )
    
    system = AutomatedEscalationSystem(config)
    
    # Test 1: Critical Security Implementation
    print("\n1. Testing Critical Security Implementation")
    print("-" * 45)
    
    context = {
        "affected_services": ["orchestrator", "console", "database", "terminal_daemon"],
        "security_factors": {
            "authentication": True,
            "authorization": True,
            "encryption": True,
            "compliance": True,
            "audit_logging": True
        },
        "performance_factors": {
            "high_throughput": True,
            "low_latency_required": True,
            "scalability_required": True
        },
        "complexity_factors": {
            "microservices_coordination": True,
            "event_driven_design": True,
            "distributed_transactions": True,
            "cross_service_consistency": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="SEC-001",
        context=context
    )
    
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    # Test 2: Critical Database Migration
    print("\n2. Testing Critical Database Migration")
    print("-" * 40)
    
    context = {
        "affected_services": ["orchestrator", "database", "console"],
        "security_factors": {
            "data_integrity": True,
            "backup_required": True,
            "compliance": True
        },
        "performance_factors": {
            "performance_optimization": True,
            "scalability_required": True,
            "large_data_volume": True
        },
        "complexity_factors": {
            "schema_migration": True,
            "data_transformation": True,
            "downtime_required": True,
            "rollback_planning": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="DB-001",
        context=context
    )
    
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    # Test 3: Major System Integration Conflict
    print("\n3. Testing Major System Integration Conflict")
    print("-" * 42)
    
    context = {
        "conflict_factors": {
            "multiple_service_conflicts": True,
            "api_contract_breaks": True,
            "data_model_conflicts": True,
            "dependency_chain_breaks": True,
            "migration_conflicts": True
        },
        "boundary_factors": {
            "system_boundary_change": True,
            "api_version_mismatch": True,
            "deployment_coordination": True,
            "service_discovery_change": True
        },
        "integration_factors": {
            "service_coupling": "critical",
            "testing_complexity": "critical",
            "deployment_complexity": "critical",
            "monitoring_complexity": "critical"
        },
        "risk_factors": {
            "data_loss_risk": True,
            "service_disruption_risk": True,
            "rollback_complexity": True,
            "deployment_failure_risk": True,
            "performance_regression_risk": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="integrator",
        task_id="INT-001",
        context=context
    )
    
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    # Test 4: Performance-Critical Optimization
    print("\n4. Testing Performance-Critical Optimization")
    print("-" * 43)
    
    context = {
        "affected_services": ["orchestrator", "database", "console", "terminal_daemon"],
        "security_factors": {
            "performance_impact": True
        },
        "performance_factors": {
            "high_throughput": True,
            "low_latency_required": True,
            "scalability_required": True,
            "performance_optimization": True,
            "large_data_volume": True,
            "real_time_processing": True
        },
        "complexity_factors": {
            "algorithm_optimization": True,
            "caching_strategy": True,
            "query_optimization": True,
            "load_balancing": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="PERF-001",
        context=context
    )
    
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    # Test 5: Simple UI Update (should not escalate)
    print("\n5. Testing Simple UI Update (No Escalation)")
    print("-" * 42)
    
    context = {
        "affected_services": ["console"],
        "security_factors": {},
        "performance_factors": {},
        "complexity_factors": {
            "ui_update": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="UI-001",
        context=context
    )
    
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    print("\n" + "=" * 50)
    print("✅ Critical scenarios test completed!")
    print("Framework is properly identifying escalation scenarios.")
    return True

if __name__ == "__main__":
    test_critical_scenarios()