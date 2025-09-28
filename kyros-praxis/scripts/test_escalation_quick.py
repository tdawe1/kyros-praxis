#!/usr/bin/env python3
"""
Quick validation test for escalation functionality
"""

import time
from typing import Dict, Any

class EscalationEngine:
    """Core escalation engine that evaluates triggers and makes decisions."""
    
    def __init__(self):
        self.architect_escalation_criteria = {
            'multi_service': lambda ctx: len(ctx.get('services_affected', [])) >= 3,
            'security_critical': lambda ctx: ctx.get('security_implications', False) and ctx.get('risk_level') in ['critical', 'high'],
            'performance_critical': lambda ctx: ctx.get('performance_critical', False) and ctx.get('expected_load', 0) > 1000,
            'system_boundary': lambda ctx: ctx.get('system_boundary_changes', False)
        }
        
        self.integrator_escalation_criteria = {
            'multi_service_conflict': lambda ctx: len(ctx.get('conflict_services', [])) >= 3,
            'system_boundary_conflict': lambda ctx: ctx.get('system_boundary_changes', False)
        }
    
    def evaluate_escalation(self, role: str, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate whether a task should escalate and return decision."""
        start_time = time.time()
        
        should_escalate = False
        reasoning = []
        
        if role == 'architect':
            for criterion_name, criterion_func in self.architect_escalation_criteria.items():
                if criterion_func(task_context):
                    should_escalate = True
                    reasoning.append(f"Met {criterion_name} criteria")
        
        elif role == 'integrator':
            for criterion_name, criterion_func in self.integrator_escalation_criteria.items():
                if criterion_func(task_context):
                    should_escalate = True
                    reasoning.append(f"Met {criterion_name} criteria")
        
        # Select model based on escalation decision
        selected_model = self._select_model(role, should_escalate)
        
        # Calculate confidence (simplified)
        confidence = self._calculate_confidence(role, task_context, should_escalate)
        
        return {
            'role': role,
            'task_context': task_context,
            'should_escalate': should_escalate,
            'selected_model': selected_model,
            'confidence': confidence,
            'reasoning': "; ".join(reasoning) if reasoning else "No escalation criteria met",
            'execution_time': time.time() - start_time
        }
    
    def _select_model(self, role: str, should_escalate: bool) -> str:
        """Select appropriate model based on role and escalation decision."""
        if should_escalate and role in ['architect', 'integrator']:
            return 'claude-4.1-opus'
        return 'glm-4.5'
    
    def _calculate_confidence(self, role: str, task_context: Dict[str, Any], should_escalate: bool) -> float:
        """Calculate confidence score for the decision."""
        base_confidence = 0.8
        
        # Increase confidence for clear-cut cases
        if role in ['architect', 'integrator'] and should_escalate:
            base_confidence += 0.1
        elif role not in ['architect', 'integrator'] and not should_escalate:
            base_confidence += 0.1
        
        # Adjust based on context completeness
        context_completeness = len(task_context) / 10.0  # Normalize
        base_confidence *= min(1.0, 0.8 + context_completeness * 0.2)
        
        return min(1.0, base_confidence)

def main():
    """Run quick validation tests."""
    print("🚀 Quick Escalation Validation Test")
    print("=" * 40)
    
    engine = EscalationEngine()
    test_cases = [
        {
            'name': 'Simple Architect Decision',
            'role': 'architect',
            'context': {
                'services_affected': ['console'],
                'security_implications': False
            },
            'expected_escalation': False,
            'expected_model': 'glm-4.5'
        },
        {
            'name': 'Complex Architect Decision',
            'role': 'architect',
            'context': {
                'services_affected': ['console', 'orchestrator', 'terminal-daemon'],
                'security_implications': True,
                'risk_level': 'critical'
            },
            'expected_escalation': True,
            'expected_model': 'claude-4.1-opus'
        },
        {
            'name': 'Simple Integrator Decision',
            'role': 'integrator',
            'context': {
                'conflict_services': ['console'],
                'conflict_types': ['formatting']
            },
            'expected_escalation': False,
            'expected_model': 'glm-4.5'
        },
        {
            'name': 'Complex Integrator Decision',
            'role': 'integrator',
            'context': {
                'conflict_services': ['console', 'orchestrator', 'terminal-daemon', 'packages/core'],
                'system_boundary_changes': True
            },
            'expected_escalation': True,
            'expected_model': 'claude-4.1-opus'
        },
        {
            'name': 'Non-escalating Role',
            'role': 'implementer',
            'context': {
                'services_affected': ['console', 'orchestrator', 'terminal-daemon'],
                'security_implications': True,
                'risk_level': 'critical'
            },
            'expected_escalation': False,
            'expected_model': 'glm-4.5'
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        
        decision = engine.evaluate_escalation(test_case['role'], test_case['context'])
        
        escalation_correct = decision['should_escalate'] == test_case['expected_escalation']
        model_correct = decision['selected_model'] == test_case['expected_model']
        
        if escalation_correct and model_correct:
            print(f"  ✅ PASSED - Escalation: {decision['should_escalate']}, Model: {decision['selected_model']}")
            print(f"     Confidence: {decision['confidence']:.2f}, Time: {decision['execution_time']:.3f}s")
            passed += 1
        else:
            print("  ❌ FAILED")
            print(f"     Expected: escalation={test_case['expected_escalation']}, model={test_case['expected_model']}")
            print(f"     Actual: escalation={decision['should_escalate']}, model={decision['selected_model']}")
            failed += 1
    
    print("\n📊 Test Summary:")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Escalation system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the escalation logic.")
        return 1

if __name__ == "__main__":
    exit(main())