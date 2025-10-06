#!/usr/bin/env python3
"""
Integration Tests for Hybrid Model Escalation Logic

This module provides comprehensive integration tests for the escalation logic,
testing the complete workflow from trigger detection to model selection and execution.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any

# Import the test scenarios
from test_escalation_scenarios import EscalationTestScenarios, Role

class EscalationDecision:
    """Represents an escalation decision made by the system."""
    
    def __init__(self, 
                 role: str,
                 task_context: Dict[str, Any],
                 should_escalate: bool,
                 selected_model: str,
                 confidence: float,
                 reasoning: str):
        self.role = role
        self.task_context = task_context
        self.should_escalate = should_escalate
        self.selected_model = selected_model
        self.confidence = confidence
        self.reasoning = reasoning
        self.timestamp = time.time()
        self.execution_time = 0.0

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
    
    def evaluate_escalation(self, role: str, task_context: Dict[str, Any]) -> EscalationDecision:
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
        
        decision = EscalationDecision(
            role=role,
            task_context=task_context,
            should_escalate=should_escalate,
            selected_model=selected_model,
            confidence=confidence,
            reasoning="; ".join(reasoning) if reasoning else "No escalation criteria met"
        )
        
        decision.execution_time = time.time() - start_time
        return decision
    
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

class MockModelProvider:
    """Mock model provider for testing escalation workflows."""
    
    def __init__(self):
        self.response_times = {
            'glm-4.5': 5.0,
            'claude-4.1-opus': 15.0
        }
        self.costs_per_1k_tokens = {
            'glm-4.5': 0.002,
            'claude-4.1-opus': 0.015
        }
        self.call_count = {model: 0 for model in self.response_times}
    
    async def execute_task(self, model: str, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock execution of a task with specified model."""
        self.call_count[model] += 1
        
        # Simulate response time
        await asyncio.sleep(self.response_times[model] / 10.0)  # Speed up for testing
        
        # Calculate estimated cost
        estimated_tokens = len(str(context)) // 4  # Rough estimate
        cost = (self.costs_per_1k_tokens[model] * estimated_tokens) / 1000
        
        return {
            'model': model,
            'task': task,
            'response': f"Mock response from {model} for {task}",
            'estimated_cost_usd': cost,
            'estimated_tokens': estimated_tokens,
            'execution_time': self.response_times[model]
        }

class IntegrationTestSuite:
    """Comprehensive integration test suite for escalation workflows."""
    
    def __init__(self):
        self.escalation_engine = EscalationEngine()
        self.model_provider = MockModelProvider()
        self.test_scenarios = EscalationTestScenarios()
        self.test_results = []
    
    async def run_end_to_end_test(self, scenario_name: str) -> Dict[str, Any]:
        """Run end-to-end test for a specific scenario."""
        scenario = self.test_scenarios.get_scenario_by_name(scenario_name)
        if not scenario:
            return {'error': f'Scenario {scenario_name} not found'}
        
        test_result = {
            'scenario_name': scenario_name,
            'role': scenario.role.value,
            'triggers_tested': len(scenario.triggers),
            'results': []
        }
        
        for trigger in scenario.triggers:
            # Step 1: Evaluate escalation decision
            decision = self.escalation_engine.evaluate_escalation(
                trigger.role.value,
                trigger.task_context
            )
            
            # Step 2: Validate decision matches expected
            decision_correct = (
                decision.should_escalate == trigger.should_escalate and
                decision.selected_model == trigger.expected_model.value
            )
            
            # Step 3: Execute with selected model
            task_result = await self.model_provider.execute_task(
                decision.selected_model,
                f"Task for {scenario_name}",
                trigger.task_context
            )
            
            trigger_result = {
                'trigger_description': trigger.trigger_description,
                'expected_escalation': trigger.should_escalate,
                'actual_escalation': decision.should_escalate,
                'expected_model': trigger.expected_model.value,
                'actual_model': decision.selected_model,
                'decision_correct': decision_correct,
                'confidence': decision.confidence,
                'execution_time': decision.execution_time,
                'task_execution_time': task_result['execution_time'],
                'estimated_cost': task_result['estimated_cost_usd'],
                'reasoning': decision.reasoning
            }
            
            test_result['results'].append(trigger_result)
        
        # Calculate overall success rate
        success_count = sum(1 for r in test_result['results'] if r['decision_correct'])
        test_result['success_rate'] = success_count / len(test_result['results'])
        test_result['overall_success'] = test_result['success_rate'] == 1.0
        
        return test_result
    
    async def run_load_test(self, concurrent_requests: int = 10) -> Dict[str, Any]:
        """Run load test to validate performance under concurrent requests."""
        test_contexts = [
            {
                'role': 'architect',
                'task_context': {
                    'services_affected': ['orchestrator', 'console', 'terminal-daemon'],
                    'decision_type': 'multi_service_design'
                }
            },
            {
                'role': 'integrator',
                'task_context': {
                    'conflict_services': ['console', 'packages/core'],
                    'conflict_types': ['formatting']
                }
            },
            {
                'role': 'implementer',
                'task_context': {
                    'task_type': 'code_implementation',
                    'services_affected': ['console']
                }
            }
        ]
        
        start_time = time.time()
        tasks = []
        
        for i in range(concurrent_requests):
            context = test_contexts[i % len(test_contexts)]
            task = self.escalation_engine.evaluate_escalation(
                context['role'], 
                context['task_context']
            )
            tasks.append(task)
        
        # Run all tasks concurrently
        results = await asyncio.gather(*[asyncio.to_thread(
            lambda: self.escalation_engine.evaluate_escalation(
                test_contexts[i % len(test_contexts)]['role'],
                test_contexts[i % len(test_contexts)]['task_context']
            )
        ) for i in range(concurrent_requests)])
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        avg_response_time = sum(r.execution_time for r in results) / len(results)
        requests_per_second = concurrent_requests / total_time
        
        return {
            'concurrent_requests': concurrent_requests,
            'total_time': total_time,
            'avg_response_time': avg_response_time,
            'requests_per_second': requests_per_second,
            'escalation_count': sum(1 for r in results if r.should_escalate),
            'model_distribution': {
                model: sum(1 for r in results if r.selected_model == model)
                for model in ['glm-4.5', 'claude-4.1-opus']
            }
        }
    
    async def run_cost_analysis_test(self) -> Dict[str, Any]:
        """Run cost analysis test comparing hybrid vs. premium-only approach."""
        # Simulate typical workload
        test_scenarios = [
            ('architect', {'services_affected': ['console'], 'decision_type': 'single_service'}),
            ('architect', {'services_affected': ['orchestrator', 'console', 'terminal-daemon'], 'security_implications': True}),
            ('integrator', {'conflict_services': ['console'], 'conflict_types': ['formatting']}),
            ('integrator', {'conflict_services': ['orchestrator', 'console', 'packages/core'], 'system_boundary_changes': True}),
            ('implementer', {'task_type': 'bug_fix', 'services_affected': ['console']}),
            ('critic', {'task_type': 'code_review', 'complexity': 'low'})
        ]
        
        hybrid_costs = []
        premium_costs = []
        
        for role, context in test_scenarios:
            decision = self.escalation_engine.evaluate_escalation(role, context)
            
            # Hybrid approach cost
            hybrid_cost = self.model_provider.costs_per_1k_tokens[decision.selected_model]
            hybrid_costs.append(hybrid_cost)
            
            # Premium-only approach cost (always use Claude 4.1 Opus)
            premium_cost = self.model_provider.costs_per_1k_tokens['claude-4.1-opus']
            premium_costs.append(premium_cost)
        
        total_hybrid_cost = sum(hybrid_costs)
        total_premium_cost = sum(premium_costs)
        savings = total_premium_cost - total_hybrid_cost
        savings_percentage = (savings / total_premium_cost) * 100 if total_premium_cost > 0 else 0
        
        return {
            'total_hybrid_cost': total_hybrid_cost,
            'total_premium_cost': total_premium_cost,
            'savings': savings,
            'savings_percentage': savings_percentage,
            'scenarios_tested': len(test_scenarios),
            'hybrid_model_usage': {
                model: sum(1 for role, ctx in test_scenarios 
                          if self.escalation_engine.evaluate_escalation(role, ctx).selected_model == model)
                for model in ['glm-4.5', 'claude-4.1-opus']
            }
        }

# Pytest test functions
@pytest.fixture
def integration_suite():
    """Fixture providing integration test suite."""
    return IntegrationTestSuite()

@pytest.mark.asyncio
async def test_architect_escalation_scenarios(integration_suite):
    """Test architect escalation scenarios end-to-end."""
    scenarios = integration_suite.test_scenarios.get_scenarios_by_role(Role.ARCHITECT)
    
    for scenario in scenarios:
        result = await integration_suite.run_end_to_end_test(scenario.name)
        assert result['overall_success'], f"Scenario {scenario.name} failed"
        
        # Verify escalation decisions
        for trigger_result in result['results']:
            if trigger_result['expected_escalation']:
                assert trigger_result['actual_escalation'], f"Expected escalation for {trigger_result['trigger_description']}"
                assert trigger_result['actual_model'] == 'claude-4.1-opus', "Expected Claude 4.1 Opus for escalation"
            else:
                assert not trigger_result['actual_escalation'], f"Expected no escalation for {trigger_result['trigger_description']}"
                assert trigger_result['actual_model'] == 'glm-4.5', "Expected GLM-4.5 for non-escalation"

@pytest.mark.asyncio
async def test_integrator_escalation_scenarios(integration_suite):
    """Test integrator escalation scenarios end-to-end."""
    scenarios = integration_suite.test_scenarios.get_scenarios_by_role(Role.INTEGRATOR)
    
    for scenario in scenarios:
        result = await integration_suite.run_end_to_end_test(scenario.name)
        assert result['overall_success'], f"Scenario {scenario.name} failed"

@pytest.mark.asyncio
async def test_load_performance(integration_suite):
    """Test load performance of escalation engine."""
    result = await integration_suite.run_load_test(concurrent_requests=20)
    
    # Performance assertions
    assert result['avg_response_time'] < 1.0, f"Average response time too high: {result['avg_response_time']}s"
    assert result['requests_per_second'] > 10, f"Throughput too low: {result['requests_per_second']} req/s"

@pytest.mark.asyncio
async def test_cost_savings(integration_suite):
    """Test cost savings analysis."""
    result = await integration_suite.run_cost_analysis_test()
    
    assert result['savings_percentage'] > 20, f"Cost savings too low: {result['savings_percentage']}%"
    assert result['hybrid_model_usage']['glm-4.5'] > 0, "GLM-4.5 should be used for cost optimization"

def test_escalation_decision_confidence():
    """Test that escalation decisions have appropriate confidence levels."""
    engine = EscalationEngine()
    
    # Test high-confidence scenarios
    high_confidence_context = {
        'services_affected': ['orchestrator', 'console', 'terminal-daemon'],
        'security_implications': True,
        'risk_level': 'critical'
    }
    decision = engine.evaluate_escalation('architect', high_confidence_context)
    assert decision.confidence > 0.85, f"High-confidence scenario should have high confidence: {decision.confidence}"
    
    # Test ambiguous scenarios
    ambiguous_context = {
        'services_affected': ['console'],
        'security_implications': False
    }
    decision = engine.evaluate_escalation('architect', ambiguous_context)
    assert decision.confidence > 0.7, f"Even ambiguous scenarios should have reasonable confidence: {decision.confidence}"

def test_non_escalating_roles():
    """Test that non-escalating roles never escalate."""
    engine = EscalationEngine()
    non_escalating_roles = ['orchestrator', 'implementer', 'critic']
    
    for role in non_escalating_roles:
        decision = engine.evaluate_escalation(role, {
            'services_affected': ['orchestrator', 'console', 'terminal-daemon'],
            'security_implications': True,
            'risk_level': 'critical'
        })
        
        assert not decision.should_escalate, f"Role {role} should never escalate"
        assert decision.selected_model == 'glm-4.5', f"Role {role} should always use GLM-4.5"

async def main():
    """Main function to run all integration tests."""
    print("🚀 Starting Integration Tests for Escalation Workflows")
    print("=" * 60)
    
    suite = IntegrationTestSuite()
    
    # Run scenario tests
    print("\n📋 Running scenario tests...")
    scenario_names = [
        "architect_multi_service_decision",
        "architect_security_critical", 
        "integrator_complex_conflict",
        "integrator_simple_conflict"
    ]
    
    scenario_results = []
    for scenario_name in scenario_names:
        result = await suite.run_end_to_end_test(scenario_name)
        scenario_results.append(result)
        status = "✅" if result['overall_success'] else "❌"
        print(f"  {status} {scenario_name}: {result['success_rate']:.1%} success rate")
    
    # Run load test
    print("\n⚡ Running load test...")
    load_result = await suite.run_load_test(concurrent_requests=10)
    print(f"  📊 Load test: {load_result['requests_per_second']:.1f} req/s, avg response: {load_result['avg_response_time']:.3f}s")
    
    # Run cost analysis
    print("\n💰 Running cost analysis...")
    cost_result = await suite.run_cost_analysis_test()
    print(f"  💸 Cost savings: {cost_result['savings_percentage']:.1f}% (${cost_result['savings']:.4f})")
    
    # Save comprehensive report
    report = {
        'test_timestamp': time.time(),
        'scenario_results': scenario_results,
        'load_test': load_result,
        'cost_analysis': cost_result,
        'model_usage_stats': suite.model_provider.call_count
    }
    
    with open('integration_test_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print("\n📄 Integration test report saved to: integration_test_report.json")
    
    # Run pytest
    print("\n🧪 Running pytest integration tests...")
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    asyncio.run(main())