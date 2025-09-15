#!/usr/bin/env python3
"""
Simple test script for criteria framework
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from escalation_criteria import ArchitectCriteria, IntegratorCriteria, ServiceType, RiskLevel
from decision_threshold import AutomatedEscalationSystem, ThresholdConfig

def test_basic_functionality():
    print("Testing Criteria Framework - Basic Functionality")
    print("=" * 50)
    
    # Test 1: Architect Criteria
    print("\n1. Testing Architect Criteria")
    print("-" * 30)
    
    architect = ArchitectCriteria()
    
    context = {
        "affected_services": ["orchestrator", "console", "database"],
        "security_factors": {"authentication": True, "authorization": True},
        "performance_factors": {"high_throughput": True, "low_latency_required": True},
        "complexity_factors": {"microservices_coordination": True, "event_driven_design": True}
    }
    
    result = architect.make_decision(context)
    print(f"Score: {result.total_score:.3f}")
    print(f"Should escalate: {result.should_escalate}")
    print(f"Reasons: {', '.join(result.primary_reasons)}")
    print(f"Service count: {len(context['affected_services'])}")
    
    # Test 2: Integrator Criteria  
    print("\n2. Testing Integrator Criteria")
    print("-" * 30)
    
    integrator = IntegratorCriteria()
    
    context = {
        "conflict_factors": {
            "multiple_service_conflicts": True,
            "api_contract_breaks": True,
            "data_model_conflicts": False
        },
        "boundary_factors": {
            "system_boundary_change": True,
            "api_version_mismatch": True,
            "deployment_coordination": True
        },
        "integration_factors": {
            "service_coupling": "high",
            "testing_complexity": "high",
            "deployment_complexity": "high"
        },
        "risk_factors": {
            "data_loss_risk": True,
            "service_disruption_risk": True,
            "rollback_complexity": True
        }
    }
    
    result = integrator.make_decision(context)
    print(f"Score: {result.total_score:.3f}")
    print(f"Should escalate: {result.should_escalate}")
    print(f"Reasons: {', '.join(result.primary_reasons)}")
    print(f"Conflict factors: {sum(1 for v in context['conflict_factors'].values() if v)}")
    
    # Test 3: Automated Escalation System
    print("\n3. Testing Automated Escalation System")
    print("-" * 30)
    
    config = ThresholdConfig(
        architect_threshold=0.75,
        integrator_threshold=0.80,
        architect_auto_escalate_threshold=0.90
    )
    
    system = AutomatedEscalationSystem(config)
    
    # Test architect decision
    context = {
        "affected_services": ["orchestrator", "console", "database"],
        "security_factors": {"authentication": True, "authorization": True},
        "performance_factors": {"high_throughput": True, "low_latency_required": True},
        "complexity_factors": {"microservices_coordination": True, "event_driven_design": True}
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="ARCH-001",
        context=context
    )
    
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Cost: ${decision.cost_estimate:.4f}")
    
    # Test 4: Simple case (should not escalate)
    print("\n4. Testing Simple Case (No Escalation)")
    print("-" * 30)
    
    context = {
        "affected_services": ["console"],
        "security_factors": {},
        "performance_factors": {},
        "complexity_factors": {}
    }
    
    decision = system.make_escalation_decision(
        role="architect",
        task_id="SIMPLE-001",
        context=context
    )
    
    print(f"Decision: {'ESCALATE' if decision.should_escalate else 'NO ESCALATE'}")
    print(f"Confidence: {decision.confidence.value}")
    print(f"Type: {decision.escalation_type.value}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Cost: ${decision.cost_estimate:.4f}")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    test_basic_functionality()