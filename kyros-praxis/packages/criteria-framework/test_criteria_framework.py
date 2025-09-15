#!/usr/bin/env python3
"""
Comprehensive Test Suite for Criteria Framework

This module provides comprehensive unit tests for all components of the escalation
criteria framework, including edge cases, integration tests, and performance tests.
"""

import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from escalation_criteria import (
    EscalationFramework, DecisionResult, CriteriaScore,
    ServiceType, ArchitectCriteria, IntegratorCriteria,
    extract_service_context, extract_security_factors, extract_performance_factors
)
from validation_system import (
    CriteriaValidator, ValidationTestCase, ValidationResults,
    ScoringCalibrator
)
from decision_threshold import (
    AutomatedEscalationSystem, ThresholdConfig, EscalationDecision,
    ConfidenceLevel, EscalationType, DynamicThresholdManager,
    ConfidenceCalculator, CostEstimator
)


class TestArchitectCriteria(unittest.TestCase):
    """Test cases for architect role criteria"""
    
    def setUp(self):
        self.criteria = ArchitectCriteria()
    
    def test_service_impact_low(self):
        """Test service impact evaluation with low impact"""
        affected_services = {ServiceType.ORCHESTRATOR}
        
        score = self.criteria.evaluate_service_impact(affected_services)
        
        self.assertEqual(score.name, "service_impact")
        self.assertLess(score.score, 0.5)
        self.assertEqual(score.weight, 0.25)
        self.assertIn("low impact", score.justification)
    
    def test_service_impact_threshold(self):
        """Test service impact evaluation at threshold (3 services)"""
        affected_services = {
            ServiceType.ORCHESTRATOR,
            ServiceType.CONSOLE,
            ServiceType.DATABASE
        }
        
        score = self.criteria.evaluate_service_impact(affected_services)
        
        self.assertEqual(score.score, 1.0)
        self.assertIn("meets minimum threshold", score.justification)
    
    def test_security_implications_critical(self):
        """Test security implications with critical factors"""
        security_factors = {
            "authentication": True,
            "authorization": True,
            "data_encryption": True,
            "input_validation": True,
            "csrf_protection": True
        }
        
        score = self.criteria.evaluate_security_implications(security_factors)
        
        self.assertGreaterEqual(score.score, 0.7)
        self.assertIn("Critical security implications", score.justification)
    
    def test_security_implications_minimal(self):
        """Test security implications with minimal factors"""
        security_factors = {
            "authentication": False,
            "authorization": False,
            "data_encryption": False,
            "input_validation": False,
            "csrf_protection": False
        }
        
        score = self.criteria.evaluate_security_implications(security_factors)
        
        self.assertLess(score.score, 0.5)
        self.assertIn("Minor security considerations", score.justification)
    
    def test_performance_criticality_high(self):
        """Test performance criticality with high requirements"""
        perf_factors = {
            "high_throughput": True,
            "low_latency_required": True,
            "scalability_constraints": True,
            "resource_intensive": True,
            "real_time_requirements": True
        }
        
        score = self.criteria.evaluate_performance_criticality(perf_factors)
        
        self.assertGreaterEqual(score.score, 0.7)
        self.assertIn("High-performance requirements", score.justification)
    
    def test_architectural_complexity_high(self):
        """Test architectural complexity with complex patterns"""
        complexity_factors = {
            "microservices_coordination": True,
            "event_driven_design": True,
            "distributed_transactions": True,
            "circuit_breakers": True,
            "service_discovery": True,
            "load_balancing": True,
            "failure_domain_isolation": True
        }
        
        score = self.criteria.evaluate_architectural_complexity(complexity_factors)
        
        self.assertGreaterEqual(score.score, 0.6)
        self.assertIn("Complex architectural patterns", score.justification)
    
    def test_make_decision_no_escalation(self):
        """Test decision making with simple context (no escalation)"""
        context = {
            "affected_services": {ServiceType.ORCHESTRATOR},
            "security_factors": {"authentication": False, "authorization": False},
            "performance_factors": {"high_throughput": False},
            "complexity_factors": {"microservices_coordination": False}
        }
        
        result = self.criteria.make_decision(context)
        
        self.assertFalse(result.should_escalate)
        self.assertLess(result.total_score, self.criteria.min_escalation_threshold)
    
    def test_make_decision_escalation(self):
        """Test decision making with complex context (escalation)"""
        context = {
            "affected_services": {
                ServiceType.ORCHESTRATOR,
                ServiceType.CONSOLE,
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
                "scalability_constraints": True,
                "resource_intensive": True,
                "real_time_requirements": True
            },
            "complexity_factors": {
                "microservices_coordination": True,
                "event_driven_design": True,
                "distributed_transactions": True,
                "circuit_breakers": True,
                "service_discovery": True,
                "load_balancing": True,
                "failure_domain_isolation": True
            }
        }
        
        result = self.criteria.make_decision(context)
        
        self.assertTrue(result.should_escalate)
        self.assertGreaterEqual(result.total_score, self.criteria.min_escalation_threshold)
        self.assertIn("Affects 3+ services", result.primary_reasons)


class TestIntegratorCriteria(unittest.TestCase):
    """Test cases for integrator role criteria"""
    
    def setUp(self):
        self.criteria = IntegratorCriteria()
    
    def test_conflict_severity_severe(self):
        """Test conflict severity evaluation with severe conflicts"""
        conflict_factors = {
            "multiple_service_conflicts": True,
            "api_contract_breaks": True,
            "data_model_conflicts": True,
            "dependency_chain_breaks": True,
            "migration_conflicts": True
        }
        
        score = self.criteria.evaluate_conflict_severity(conflict_factors)
        
        self.assertGreaterEqual(score.score, 0.7)
        self.assertIn("Severe conflicts", score.justification)
        self.assertEqual(score.weight, 0.35)
    
    def test_system_boundary_impact_high(self):
        """Test system boundary impact with multiple boundaries"""
        boundary_factors = {
            "authentication_boundary": True,
            "data_boundary": True,
            "service_boundary": True,
            "api_boundary": True,
            "infrastructure_boundary": True
        }
        
        score = self.criteria.evaluate_system_boundary_impact(boundary_factors)
        
        self.assertGreaterEqual(score.score, 0.6)
        self.assertIn("Multiple system boundaries", score.justification)
    
    def test_integration_complexity_high(self):
        """Test integration complexity with high complexity"""
        integration_factors = {
            "cross_service_dependencies": True,
            "version_conflicts": True,
            "schema_migrations": True,
            "configuration_drift": True,
            "test_integration": True,
            "deployment_coordination": True
        }
        
        score = self.criteria.evaluate_integration_complexity(integration_factors)
        
        self.assertGreaterEqual(score.score, 0.6)
        self.assertIn("High integration complexity", score.justification)
    
    def test_risk_factors_high(self):
        """Test risk factors with high risk"""
        risk_factors = {
            "data_loss_risk": True,
            "service_disruption_risk": True,
            "rollback_complexity": True,
            "deployment_failure_risk": True,
            "performance_regression_risk": True
        }
        
        score = self.criteria.evaluate_risk_factors(risk_factors)
        
        self.assertGreaterEqual(score.score, 0.6)
        self.assertIn("High-risk integration", score.justification)
    
    def test_make_decision_no_escalation(self):
        """Test decision making with simple context (no escalation)"""
        context = {
            "conflict_factors": {
                "multiple_service_conflicts": False,
                "api_contract_breaks": False,
                "data_model_conflicts": False
            },
            "boundary_factors": {
                "authentication_boundary": False,
                "data_boundary": False
            },
            "integration_factors": {
                "cross_service_dependencies": False,
                "version_conflicts": False
            },
            "risk_factors": {
                "data_loss_risk": False,
                "service_disruption_risk": False
            }
        }
        
        result = self.criteria.make_decision(context)
        
        self.assertFalse(result.should_escalate)
        self.assertLess(result.total_score, self.criteria.min_escalation_threshold)
    
    def test_make_decision_escalation(self):
        """Test decision making with complex context (escalation)"""
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
        
        result = self.criteria.make_decision(context)
        
        self.assertTrue(result.should_escalate)
        self.assertGreaterEqual(result.total_score, self.criteria.min_escalation_threshold)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions for context extraction"""
    
    def test_extract_service_context_orchestrator(self):
        """Test service context extraction for orchestrator files"""
        files = [
            "services/orchestrator/main.py",
            "services/orchestrator/models.py",
            "services/orchestrator/auth.py"
        ]
        
        services = extract_service_context(files)
        
        self.assertIn(ServiceType.ORCHESTRATOR, services)
        self.assertEqual(len(services), 1)
    
    def test_extract_service_context_multiple(self):
        """Test service context extraction for multiple services"""
        files = [
            "services/orchestrator/main.py",
            "services/console/app/page.tsx",
            "services/orchestrator/database/models.py"
        ]
        
        services = extract_service_context(files)
        
        expected_services = {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE, ServiceType.DATABASE}
        self.assertEqual(services, expected_services)
    
    def test_extract_security_factors_auth(self):
        """Test security factor extraction with authentication"""
        files = ["services/orchestrator/auth.py"]
        messages = ["Add JWT authentication for user login"]
        
        factors = extract_security_factors(files, messages)
        
        self.assertTrue(factors["authentication"])
        self.assertTrue(factors["authorization"])
    
    def test_extract_security_factors_encryption(self):
        """Test security factor extraction with encryption"""
        files = ["services/orchestrator/crypto.py"]
        messages = ["Implement data encryption for sensitive fields"]
        
        factors = extract_security_factors(files, messages)
        
        self.assertTrue(factors["data_encryption"])
    
    def test_extract_performance_factors_throughput(self):
        """Test performance factor extraction with throughput"""
        files = ["services/orchestrator/api.py"]
        messages = ["Optimize for high throughput and concurrent requests"]
        
        factors = extract_performance_factors(files, messages)
        
        self.assertTrue(factors["high_throughput"])
        self.assertTrue(factors["scalability_constraints"])
    
    def test_extract_performance_factors_latency(self):
        """Test performance factor extraction with latency"""
        files = ["services/console/components/realtime.tsx"]
        messages = ["Reduce response time for real-time updates"]
        
        factors = extract_performance_factors(files, messages)
        
        self.assertTrue(factors["low_latency_required"])


class TestValidationSystem(unittest.TestCase):
    """Test validation system functionality"""
    
    def setUp(self):
        self.framework = EscalationFramework()
        self.validator = CriteriaValidator(self.framework)
    
    def test_validate_architect_criteria_basic(self):
        """Test basic architect criteria validation"""
        results = self.validator.validate_architect_criteria()
        
        self.assertIsInstance(results, ValidationResults)
        self.assertGreater(results.total_tests, 0)
        self.assertGreaterEqual(results.pass_rate, 0.0)
        self.assertLessEqual(results.pass_rate, 1.0)
    
    def test_validate_integrator_criteria_basic(self):
        """Test basic integrator criteria validation"""
        results = self.validator.validate_integrator_criteria()
        
        self.assertIsInstance(results, ValidationResults)
        self.assertGreater(results.total_tests, 0)
        self.assertGreaterEqual(results.pass_rate, 0.0)
        self.assertLessEqual(results.pass_rate, 1.0)
    
    def test_validate_weight_consistency(self):
        """Test weight consistency validation"""
        results = self.validator.validate_weight_consistency()
        
        self.assertIn("architect_weights_sum_to_1", results)
        self.assertIn("integrator_weights_sum_to_1", results)
        self.assertTrue(results["architect_weights_sum_to_1"])
        self.assertTrue(results["integrator_weights_sum_to_1"])
    
    def test_edge_case_empty_context(self):
        """Test edge case with empty context"""
        edge_cases = self.validator.run_edge_case_tests()
        
        self.assertIn("empty_context", edge_cases)
        self.assertGreater(len(edge_cases["empty_context"]), 0)
        
        # Check that empty context doesn't crash
        empty_test = edge_cases["empty_context"][0]
        self.assertEqual(empty_test["success"], True)
    
    def test_validation_results_report(self):
        """Test validation results report generation"""
        results = ValidationResults()
        results.passed = 8
        results.failed = 2
        results.test_cases = [Mock() for _ in range(10)]
        
        report = results.generate_report()
        
        self.assertEqual(report["summary"]["total_tests"], 10)
        self.assertEqual(report["summary"]["passed"], 8)
        self.assertEqual(report["summary"]["failed"], 2)
        self.assertEqual(report["summary"]["pass_rate"], 0.8)


class TestDecisionThreshold(unittest.TestCase):
    """Test decision threshold and automated escalation system"""
    
    def setUp(self):
        self.config = ThresholdConfig()
        self.system = AutomatedEscalationSystem(self.config)
    
    def test_threshold_configuration(self):
        """Test threshold configuration setup"""
        self.assertEqual(self.config.architect_threshold, 0.75)
        self.assertEqual(self.config.integrator_threshold, 0.80)
        self.assertEqual(self.config.architect_auto_escalate_threshold, 0.90)
        self.assertEqual(self.config.integrator_auto_escalate_threshold, 0.95)
    
    def test_dynamic_threshold_manager(self):
        """Test dynamic threshold manager"""
        manager = DynamicThresholdManager(self.config)
        
        recent_performance = {"accuracy": 0.6, "false_positive_rate": 0.3, "false_negative_rate": 0.1}
        
        # Test threshold adjustment
        new_threshold = manager.calculate_dynamic_threshold("architect", recent_performance)
        
        # Should be lower due to poor accuracy
        self.assertLess(new_threshold, self.config.architect_threshold)
    
    def test_confidence_calculator(self):
        """Test confidence calculator"""
        calculator = ConfidenceCalculator()
        
        # Mock decision result
        decision_result = Mock()
        decision_result.total_score = 0.8
        decision_result.threshold = 0.75
        
        context = {
            "affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE},
            "security_factors": {"authentication": True, "authorization": True},
            "performance_factors": {"high_throughput": True},
            "complexity_factors": {"microservices_coordination": True}
        }
        
        confidence_level, confidence_score = calculator.calculate_confidence(
            decision_result, context, []
        )
        
        self.assertIsInstance(confidence_level, ConfidenceLevel)
        self.assertGreaterEqual(confidence_score, 0.0)
        self.assertLessEqual(confidence_score, 1.0)
    
    def test_cost_estimator(self):
        """Test cost estimator"""
        estimator = CostEstimator()
        
        # Mock decision result
        decision_result = Mock()
        decision_result.total_score = 0.8
        decision_result.criteria_scores = []
        
        cost = estimator.estimate_cost(decision_result)
        
        self.assertGreater(cost, 0.0)
        self.assertIsInstance(cost, float)
    
    def test_cost_justification(self):
        """Test cost justification logic"""
        estimator = CostEstimator()
        
        # High risk should justify cost
        context = {"security_factors": {"authentication": True}}
        justified = estimator.is_cost_justified(0.5, 0.9, context)
        self.assertTrue(justified)
        
        # Low risk may not justify high cost
        context = {"security_factors": {}}
        justified = estimator.is_cost_justified(2.0, 0.3, context)
        self.assertFalse(justified)
    
    def test_automated_escalation_decision(self):
        """Test automated escalation decision making"""
        context = {
            "affected_services": {
                ServiceType.ORCHESTRATOR,
                ServiceType.CONSOLE,
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
                "scalability_constraints": True,
                "resource_intensive": True,
                "real_time_requirements": True
            },
            "complexity_factors": {
                "microservices_coordination": True,
                "event_driven_design": True,
                "distributed_transactions": True,
                "circuit_breakers": True,
                "service_discovery": True,
                "load_balancing": True,
                "failure_domain_isolation": True
            }
        }
        
        decision = self.system.make_escalation_decision(
            role="architect",
            task_id="TEST-001",
            context=context
        )
        
        self.assertIsInstance(decision, EscalationDecision)
        self.assertIn(decision.escalation_type, [EscalationType.AUTOMATIC, EscalationType.RECOMMENDED, EscalationType.NONE])
        self.assertGreaterEqual(decision.certainty_score, 0.0)
        self.assertLessEqual(decision.certainty_score, 1.0)
    
    def test_force_escalation_override(self):
        """Test force escalation override"""
        decision = self.system.make_escalation_decision(
            role="architect",
            task_id="TEST-002",
            context={},
            force_escalation=True
        )
        
        self.assertTrue(decision.should_escalate)
        self.assertEqual(decision.escalation_type, EscalationType.AUTOMATIC)
        self.assertFalse(decision.override_allowed)
    
    def test_prevent_escalation_override(self):
        """Test prevent escalation override"""
        decision = self.system.make_escalation_decision(
            role="architect",
            task_id="TEST-003",
            context={},
            prevent_escalation=True
        )
        
        self.assertFalse(decision.should_escalate)
        self.assertEqual(decision.escalation_type, EscalationType.NONE)
        self.assertFalse(decision.override_allowed)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Fill up recent escalations
        for _ in range(self.config.max_escalations_per_hour + 5):
            self.system.recent_escalations.append(datetime.utcnow())
        
        decision = self.system.make_escalation_decision(
            role="architect",
            task_id="TEST-004",
            context={"affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE, ServiceType.DATABASE}}
        )
        
        # Should be blocked due to rate limit
        self.assertFalse(decision.should_escalate)
        reasoning_text = " ".join(decision.reasoning)
        self.assertIn("Rate limit exceeded", reasoning_text)
    
    def test_decision_analytics(self):
        """Test decision analytics"""
        # Make some test decisions
        for i in range(5):
            context = {
                "affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE},
                "security_factors": {"authentication": True},
                "performance_factors": {"high_throughput": True},
                "complexity_factors": {"microservices_coordination": True}
            }
            
            self.system.make_escalation_decision(
                role="architect",
                task_id=f"TEST-{i:03d}",
                context=context
            )
        
        analytics = self.system.get_decision_analytics()
        
        self.assertIn("summary", analytics)
        self.assertIn("total_decisions", analytics["summary"])
        self.assertGreater(analytics["summary"]["total_decisions"], 0)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios and real-world use cases"""
    
    def setUp(self):
        self.framework = EscalationFramework()
        self.system = AutomatedEscalationSystem()
    
    def test_real_world_architect_scenario_security_critical(self):
        """Test real-world architect scenario: security-critical architecture"""
        # Scenario: Designing authentication system across multiple services
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
                "service_discovery": True
            }
        }
        
        decision = self.system.make_escalation_decision(
            role="architect",
            task_id="AUTH-DESIGN-001",
            context=context
        )
        
        # Should escalate due to security-critical nature and multi-service impact
        self.assertTrue(decision.should_escalate)
        self.assertIn("3+ services", decision.reasoning[0])
        self.assertIn("Critical security", " ".join(decision.reasoning))
    
    def test_real_world_integrator_scenario_major_merge(self):
        """Test real-world integrator scenario: major merge with conflicts"""
        # Scenario: Merging changes that affect API contracts and data models
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
                "api_boundary": True
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
                "deployment_failure_risk": True
            }
        }
        
        decision = self.system.make_escalation_decision(
            role="integrator",
            task_id="MERGE-CONFLICT-001",
            context=context
        )
        
        # Should escalate due to severe conflicts and high risk
        self.assertTrue(decision.should_escalate)
        reasoning_text = " ".join(decision.reasoning)
        self.assertIn("Severe conflicts", reasoning_text)
    
    def test_performance_edge_case(self):
        """Test performance-critical edge case"""
        context = {
            "affected_services": {ServiceType.ORCHESTRATOR},
            "security_factors": {"authentication": False},
            "performance_factors": {
                "high_throughput": True,
                "low_latency_required": True,
                "scalability_constraints": True,
                "resource_intensive": True,
                "real_time_requirements": True
            },
            "complexity_factors": {
                "microservices_coordination": False,
                "event_driven_design": True
            }
        }
        
        decision = self.system.make_escalation_decision(
            role="architect",
            task_id="PERF-EDGE-001",
            context=context
        )
        
        # Should escalate due to performance criticality
        self.assertTrue(decision.should_escalate)
        self.assertIn("performance", " ".join(decision.reasoning).lower())
    
    def test_cost_threshold_scenario(self):
        """Test scenario where cost threshold prevents escalation"""
        # Create a scenario with high estimated cost but low actual importance
        context = {
            "affected_services": {ServiceType.ORCHESTRATOR},
            "security_factors": {"authentication": False},
            "performance_factors": {"high_throughput": False},
            "complexity_factors": {"microservices_coordination": False}
        }
        
        decision = self.system.make_escalation_decision(
            role="architect",
            task_id="COST-TEST-001",
            context=context
        )
        
        # Should not escalate due to cost/benefit analysis
        self.assertFalse(decision.should_escalate)
        self.assertIn("Cost not justified", " ".join(decision.reasoning))


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        self.system = AutomatedEscalationSystem()
    
    def test_invalid_role(self):
        """Test handling of invalid role"""
        with self.assertRaises(ValueError):
            self.system.make_escalation_decision(
                role="invalid_role",
                task_id="TEST-ERROR-001",
                context={}
            )
    
    def test_empty_context(self):
        """Test handling of empty context"""
        decision = self.system.make_escalation_decision(
            role="architect",
            task_id="TEST-EMPTY-001",
            context={}
        )
        
        # Should handle empty context gracefully
        self.assertIsInstance(decision, EscalationDecision)
        self.assertFalse(decision.should_escalate)
    
    def test_malformed_context(self):
        """Test handling of malformed context"""
        context = {
            "affected_services": "invalid_type",  # Should be a set
            "security_factors": None,  # Should be a dict
            "performance_factors": 123  # Should be a dict
        }
        
        # Should not crash, but should handle gracefully
        try:
            decision = self.system.make_escalation_decision(
                role="architect",
                task_id="TEST-MALFORMED-001",
                context=context
            )
            self.assertIsInstance(decision, EscalationDecision)
        except Exception as e:
            # If it does crash, it should be a graceful error
            self.assertIsInstance(e, (ValueError, TypeError, AttributeError))


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def test_decision_performance(self):
        """Test that decisions are made quickly"""
        system = AutomatedEscalationSystem()
        
        context = {
            "affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE, ServiceType.DATABASE},
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
                "scalability_constraints": True,
                "resource_intensive": True,
                "real_time_requirements": True
            },
            "complexity_factors": {
                "microservices_coordination": True,
                "event_driven_design": True,
                "distributed_transactions": True,
                "circuit_breakers": True,
                "service_discovery": True,
                "load_balancing": True,
                "failure_domain_isolation": True
            }
        }
        
        # Measure time for multiple decisions
        import time
        start_time = time.time()
        
        for i in range(100):
            system.make_escalation_decision(
                role="architect",
                task_id=f"PERF-TEST-{i:03d}",
                context=context
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100
        
        # Should be fast (less than 10ms per decision on average)
        self.assertLess(avg_time, 0.01, f"Average decision time too slow: {avg_time:.4f}s")
        
        print(f"Average decision time: {avg_time:.4f}s")


if __name__ == "__main__":
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run all tests
    unittest.main(verbosity=2)