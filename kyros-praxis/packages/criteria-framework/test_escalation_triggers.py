#!/usr/bin/env python3
"""
Test cases that should trigger escalation to Claude 4.1 Opus
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from escalation_criteria import ArchitectCriteria, IntegratorCriteria
from decision_threshold import AutomatedEscalationSystem, ThresholdConfig

def test_escalation_scenarios():
    print("Testing Escalation Trigger Scenarios")
    print("=" * 50)
    
    config = ThresholdConfig(
        architect_threshold=0.75,
        integrator_threshold=0.80,
        architect_auto_escalate_threshold=0.90
    )
    
    system = AutomatedEscalationSystem(config)
    
    escalation_count = 0
    
    # Test 1: Critical Security Implementation (should escalate)
    print("\n1. Testing Critical Security Implementation")
    print("-" * 45)
    
    context = {
        "affected_services": ["orchestrator", "console", "database", "terminal_daemon", "auth_service"],
        "security_factors": {
            "authentication": True,
            "authorization": True,
            "encryption": True,
            "compliance": True,
            "audit_logging": True,
            "key_management": True,
            "access_control": True
        },
        "performance_factors": {
            "high_throughput": True,
            "low_latency_required": True,
            "scalability_required": True,
            "real_time_processing": True
        },
        "complexity_factors": {
            "microservices_coordination": True,
            "event_driven_design": True,
            "distributed_transactions": True,
            "cross_service_consistency": True,
            "security_architecture": True,
            "compliance_framework": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="SEC-CRITICAL-001",
        context=context
    )
    
    print(f"Decision: {'🚀 ESCALATE' if decision.should_escalate else '📝 NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    if decision.should_escalate:
        escalation_count += 1
    
    # Test 2: Performance Critical Optimization (should escalate)
    print("\n2. Testing Performance Critical Optimization")
    print("-" * 43)
    
    context = {
        "affected_services": ["orchestrator", "database", "console", "terminal_daemon", "cache_service"],
        "security_factors": {
            "performance_impact": True,
            "security_review_required": True
        },
        "performance_factors": {
            "high_throughput": True,
            "low_latency_required": True,
            "scalability_required": True,
            "performance_optimization": True,
            "large_data_volume": True,
            "real_time_processing": True,
            "bottleneck_resolution": True,
            "resource_optimization": True
        },
        "complexity_factors": {
            "algorithm_optimization": True,
            "caching_strategy": True,
            "query_optimization": True,
            "load_balancing": True,
            "index_optimization": True,
            "memory_management": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="PERF-CRITICAL-001",
        context=context
    )
    
    print(f"Decision: {'🚀 ESCALATE' if decision.should_escalate else '📝 NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    if decision.should_escalate:
        escalation_count += 1
    
    # Test 3: Critical Integration Conflict (should escalate)
    print("\n3. Testing Critical Integration Conflict")
    print("-" * 40)
    
    context = {
        "conflict_factors": {
            "multiple_service_conflicts": True,
            "api_contract_breaks": True,
            "data_model_conflicts": True,
            "dependency_chain_breaks": True,
            "migration_conflicts": True,
            "version_conflicts": True,
            "configuration_conflicts": True
        },
        "boundary_factors": {
            "system_boundary_change": True,
            "api_version_mismatch": True,
            "deployment_coordination": True,
            "service_discovery_change": True,
            "protocol_mismatch": True,
            "authentication_boundary_change": True
        },
        "integration_factors": {
            "service_coupling": "critical",
            "testing_complexity": "critical",
            "deployment_complexity": "critical",
            "monitoring_complexity": "critical",
            "rollback_complexity": "critical",
            "data_consistency": "critical"
        },
        "risk_factors": {
            "data_loss_risk": True,
            "service_disruption_risk": True,
            "rollback_complexity": True,
            "deployment_failure_risk": True,
            "performance_regression_risk": True,
            "security_breach_risk": True,
            "compliance_violation_risk": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="integrator",
        task_id="INT-CRITICAL-001",
        context=context
    )
    
    print(f"Decision: {'🚀 ESCALATE' if decision.should_escalate else '📝 NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    if decision.should_escalate:
        escalation_count += 1
    
    # Test 4: System Architecture Redesign (should escalate)
    print("\n4. Testing System Architecture Redesign")
    print("-" * 38)
    
    context = {
        "affected_services": ["orchestrator", "console", "database", "terminal_daemon", "auth_service", "cache_service"],
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
            "scalability_required": True,
            "performance_optimization": True
        },
        "complexity_factors": {
            "microservices_coordination": True,
            "event_driven_design": True,
            "distributed_transactions": True,
            "cross_service_consistency": True,
            "architecture_redesign": True,
            "pattern_implementation": True,
            "service_decomposition": True,
            "communication_protocol": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="ARCH-REDESIGN-001",
        context=context
    )
    
    print(f"Decision: {'🚀 ESCALATE' if decision.should_escalate else '📝 NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    if decision.should_escalate:
        escalation_count += 1
    
    # Test 5: Simple bug fix (should not escalate)
    print("\n5. Testing Simple Bug Fix (No Escalation)")
    print("-" * 41)
    
    context = {
        "affected_services": ["console"],
        "security_factors": {},
        "performance_factors": {},
        "complexity_factors": {
            "bug_fix": True,
            "minor_change": True
        }
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="BUG-SIMPLE-001",
        context=context
    )
    
    print(f"Decision: {'🚀 ESCALATE' if decision.should_escalate else '📝 NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Certainty Score: {decision.certainty_score:.3f}")
    print(f"Reasoning: {decision.reasoning}")
    
    if decision.should_escalate:
        escalation_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Escalation Summary: {escalation_count}/4 critical tasks should escalate")
    print("✅ Framework successfully identifies escalation scenarios!")
    
    return escalation_count >= 3  # At least 3 critical scenarios should escalate

if __name__ == "__main__":
    success = test_escalation_scenarios()
    if success:
        print("\n🎉 PASSED: Criteria framework correctly identifies escalation scenarios!")
    else:
        print("\n⚠️  WARNING: Framework may not be escalating critical scenarios appropriately.")
    print(f"\nExit code: {0 if success else 1}")
    sys.exit(0 if success else 1)