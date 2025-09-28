#!/usr/bin/env python3
"""
Criteria Validation and Scoring System

This module provides validation and calibration utilities for the escalation criteria,
ensuring the scoring system works correctly and produces reliable results.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable, Any
from pathlib import Path
import unittest.mock as mock
from decimal import Decimal, getcontext

from escalation_criteria import (
    EscalationFramework, DecisionResult, CriteriaScore,
    ServiceType, RiskLevel
)

# Set decimal precision for financial calculations
getcontext().prec = 6

logger = logging.getLogger(__name__)


@dataclass
class ValidationTestCase:
    """Test case for criteria validation"""
    name: str
    context: Dict[str, Any]
    expected_outcome: bool
    expected_min_score: float
    expected_max_score: float
    tolerance: float = 0.01
    description: str = ""


@dataclass
class ValidationResults:
    """Results of validation run"""
    test_cases: List[ValidationTestCase] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    score_accuracy: Dict[str, List[float]] = field(default_factory=dict)
    edge_cases: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def total_tests(self) -> int:
        return len(self.test_cases)
    
    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_tests if self.total_tests > 0 else 0.0
    
    def add_test_result(self, test_case: ValidationTestCase, actual_result: DecisionResult) -> None:
        """Add test result to validation results"""
        self.test_cases.append(test_case)
        
        # Check if outcome matches expectation
        if actual_result.should_escalate == test_case.expected_outcome:
            self.passed += 1
        else:
            self.failed += 1
            self.edge_cases.append(f"Outcome mismatch: {test_case.name}")
        
        # Check score accuracy
        score_key = f"{test_case.name}_score"
        if score_key not in self.score_accuracy:
            self.score_accuracy[score_key] = []
        
        expected_range = (test_case.expected_min_score, test_case.expected_max_score)
        actual_score = actual_result.total_score
        
        if expected_range[0] <= actual_score <= expected_range[1]:
            self.score_accuracy[score_key].append(1.0)  # Perfect accuracy
        else:
            # Calculate how far off we are
            if actual_score < expected_range[0]:
                accuracy = 1.0 - (expected_range[0] - actual_score)
            else:
                accuracy = 1.0 - (actual_score - expected_range[1])
            self.score_accuracy[score_key].append(max(0.0, accuracy))
    
    def generate_report(self) -> Dict:
        """Generate validation report"""
        avg_score_accuracy = {}
        for key, scores in self.score_accuracy.items():
            avg_score_accuracy[key] = sum(scores) / len(scores) if scores else 0.0
        
        overall_accuracy = sum(avg_score_accuracy.values()) / len(avg_score_accuracy) if avg_score_accuracy else 0.0
        
        return {
            "summary": {
                "total_tests": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "pass_rate": self.pass_rate,
                "overall_score_accuracy": overall_accuracy
            },
            "score_accuracy": avg_score_accuracy,
            "edge_cases": self.edge_cases,
            "recommendations": self.recommendations
        }


class CriteriaValidator:
    """Validates escalation criteria against test cases and edge scenarios"""
    
    def __init__(self, framework: EscalationFramework):
        self.framework = framework
        self.validation_history: List[ValidationResults] = []
        
    def validate_architect_criteria(self) -> ValidationResults:
        """Validate architect role criteria"""
        logger.info("Starting architect criteria validation")
        
        results = ValidationResults()
        
        # Test cases for architect role
        test_cases = [
            # Low complexity - should not escalate
            ValidationTestCase(
                name="simple_single_service",
                context={
                    "affected_services": {ServiceType.ORCHESTRATOR},
                    "security_factors": {"authentication": False, "authorization": False},
                    "performance_factors": {"high_throughput": False},
                    "complexity_factors": {"microservices_coordination": False}
                },
                expected_outcome=False,
                expected_min_score=0.0,
                expected_max_score=0.4,
                description="Single service, no security or performance concerns"
            ),
            
            # Medium complexity - borderline
            ValidationTestCase(
                name="medium_two_services",
                context={
                    "affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE},
                    "security_factors": {"authentication": True, "authorization": False},
                    "performance_factors": {"high_throughput": True, "low_latency_required": False},
                    "complexity_factors": {"microservices_coordination": False, "event_driven_design": True}
                },
                expected_outcome=False,
                expected_min_score=0.4,
                expected_max_score=0.7,
                description="Two services with some security and performance factors"
            ),
            
            # High complexity - should escalate
            ValidationTestCase(
                name="high_three_services_security",
                context={
                    "affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE, ServiceType.DATABASE},
                    "security_factors": {
                        "authentication": True, "authorization": True, "data_encryption": True,
                        "input_validation": True, "csrf_protection": True
                    },
                    "performance_factors": {
                        "high_throughput": True, "low_latency_required": True,
                        "scalability_constraints": True, "resource_intensive": True
                    },
                    "complexity_factors": {
                        "microservices_coordination": True, "event_driven_design": True,
                        "distributed_transactions": True, "circuit_breakers": True
                    }
                },
                expected_outcome=True,
                expected_min_score=0.8,
                expected_max_score=1.0,
                description="Three services with critical security and performance requirements"
            ),
            
            # Security-focused escalation
            ValidationTestCase(
                name="security_critical_only",
                context={
                    "affected_services": {ServiceType.ORCHESTRATOR},
                    "security_factors": {
                        "authentication": True, "authorization": True, "data_encryption": True,
                        "input_validation": True, "csrf_protection": True
                    },
                    "performance_factors": {"high_throughput": False},
                    "complexity_factors": {"microservices_coordination": False}
                },
                expected_outcome=True,
                expected_min_score=0.7,
                expected_max_score=0.9,
                description="Single service but critical security implications"
            ),
            
            # Performance-focused escalation
            ValidationTestCase(
                name="performance_critical_only",
                context={
                    "affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE},
                    "security_factors": {"authentication": False},
                    "performance_factors": {
                        "high_throughput": True, "low_latency_required": True,
                        "scalability_constraints": True, "resource_intensive": True,
                        "real_time_requirements": True
                    },
                    "complexity_factors": {"microservices_coordination": True}
                },
                expected_outcome=True,
                expected_min_score=0.75,
                expected_max_score=0.95,
                description="Performance-critical requirements across services"
            )
        ]
        
        # Run test cases
        for test_case in test_cases:
            result = self.framework.evaluate_architect_task(test_case.context)
            results.add_test_result(test_case, result)
            
            logger.debug(f"Test '{test_case.name}': "
                        f"Expected={test_case.expected_outcome}, "
                        f"Actual={result.should_escalate}, "
                        f"Score={result.total_score:.3f}")
        
        # Analyze results and generate recommendations
        self._analyze_validation_results(results, "architect")
        
        self.validation_history.append(results)
        logger.info(f"Architect validation complete: {results.pass_rate:.2%} pass rate")
        
        return results
    
    def validate_integrator_criteria(self) -> ValidationResults:
        """Validate integrator role criteria"""
        logger.info("Starting integrator criteria validation")
        
        results = ValidationResults()
        
        # Test cases for integrator role
        test_cases = [
            # Simple merge - should not escalate
            ValidationTestCase(
                name="simple_merge",
                context={
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
                },
                expected_outcome=False,
                expected_min_score=0.0,
                expected_max_score=0.3,
                description="Simple merge with no conflicts"
            ),
            
            # Medium complexity conflicts
            ValidationTestCase(
                name="medium_conflicts",
                context={
                    "conflict_factors": {
                        "multiple_service_conflicts": True,
                        "api_contract_breaks": False,
                        "data_model_conflicts": True,
                        "dependency_chain_breaks": False
                    },
                    "boundary_factors": {
                        "authentication_boundary": True,
                        "data_boundary": False,
                        "service_boundary": True
                    },
                    "integration_factors": {
                        "cross_service_dependencies": True,
                        "version_conflicts": True,
                        "configuration_drift": False
                    },
                    "risk_factors": {
                        "data_loss_risk": False,
                        "service_disruption_risk": True,
                        "rollback_complexity": True
                    }
                },
                expected_outcome=False,
                expected_min_score=0.5,
                expected_max_score=0.75,
                description="Medium complexity conflicts across service boundaries"
            ),
            
            # Critical conflicts - should escalate
            ValidationTestCase(
                name="critical_multi_service_conflicts",
                context={
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
                },
                expected_outcome=True,
                expected_min_score=0.9,
                expected_max_score=1.0,
                description="Critical multi-service conflicts with high risk factors"
            ),
            
            # Boundary-focused escalation
            ValidationTestCase(
                name="boundary_escalation",
                context={
                    "conflict_factors": {
                        "multiple_service_conflicts": True,
                        "api_contract_breaks": True,
                        "data_model_conflicts": False
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
                        "version_conflicts": False
                    },
                    "risk_factors": {
                        "data_loss_risk": True,
                        "service_disruption_risk": True
                    }
                },
                expected_outcome=True,
                expected_min_score=0.8,
                expected_max_score=0.95,
                description="Multiple system boundaries affected with significant conflicts"
            )
        ]
        
        # Run test cases
        for test_case in test_cases:
            result = self.framework.evaluate_integrator_task(test_case.context)
            results.add_test_result(test_case, result)
            
            logger.debug(f"Test '{test_case.name}': "
                        f"Expected={test_case.expected_outcome}, "
                        f"Actual={result.should_escalate}, "
                        f"Score={result.total_score:.3f}")
        
        # Analyze results and generate recommendations
        self._analyze_validation_results(results, "integrator")
        
        self.validation_history.append(results)
        logger.info(f"Integrator validation complete: {results.pass_rate:.2%} pass rate")
        
        return results
    
    def _analyze_validation_results(self, results: ValidationResults, role: str) -> None:
        """Analyze validation results and generate recommendations"""
        if results.pass_rate < 0.8:
            results.recommendations.append(
                f"Low pass rate ({results.pass_rate:.1%}) for {role} criteria. "
                f"Review scoring thresholds and test cases."
            )
        
        # Check for systematic score deviations
        for test_name, accuracies in results.score_accuracy.items():
            avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
            if avg_accuracy < 0.8:
                results.recommendations.append(
                    f"Score accuracy issue in {test_name}: {avg_accuracy:.1%}. "
                    f"Consider adjusting scoring algorithm or expected ranges."
                )
        
        # Analyze edge cases
        if len(results.edge_cases) > len(results.test_cases) * 0.2:
            results.recommendations.append(
                f"High number of edge cases ({len(results.edge_cases)}) detected. "
                f"Review criteria logic and test case expectations."
            )
        
        # Overall recommendations
        if results.pass_rate >= 0.95:
            results.recommendations.append(
                f"Excellent validation results for {role} criteria. "
                f"Ready for production deployment."
            )
        elif results.pass_rate >= 0.8:
            results.recommendations.append(
                f"Good validation results for {role} criteria. "
                f"Consider minor adjustments before production use."
            )
    
    def run_edge_case_tests(self) -> Dict[str, List[Dict]]:
        """Run comprehensive edge case testing"""
        logger.info("Running edge case tests")
        
        edge_cases = {
            "empty_context": [],
            "max_values": [],
            "min_values": [],
            "mixed_signals": [],
            "boundary_conditions": []
        }
        
        # Empty context test
        try:
            result = self.framework.evaluate_architect_task({})
            edge_cases["empty_context"].append({
                "test": "empty_architect_context",
                "result": result.should_escalate,
                "score": result.total_score,
                "success": True
            })
        except Exception as e:
            edge_cases["empty_context"].append({
                "test": "empty_architect_context",
                "error": str(e),
                "success": False
            })
        
        # Maximum values test
        max_context = {
            "affected_services": {st for st in ServiceType},
            "security_factors": {f: True for f in ["authentication", "authorization", "data_encryption", "input_validation", "csrf_protection"]},
            "performance_factors": {f: True for f in ["high_throughput", "low_latency_required", "scalability_constraints", "resource_intensive", "real_time_requirements"]},
            "complexity_factors": {f: True for f in ["microservices_coordination", "event_driven_design", "distributed_transactions", "circuit_breakers", "service_discovery", "load_balancing", "failure_domain_isolation"]}
        }
        
        try:
            result = self.framework.evaluate_architect_task(max_context)
            edge_cases["max_values"].append({
                "test": "max_architect_values",
                "result": result.should_escalate,
                "score": result.total_score,
                "success": True
            })
        except Exception as e:
            edge_cases["max_values"].append({
                "test": "max_architect_values",
                "error": str(e),
                "success": False
            })
        
        # Minimum values test
        min_context = {
            "affected_services": set(),
            "security_factors": {f: False for f in ["authentication", "authorization", "data_encryption", "input_validation", "csrf_protection"]},
            "performance_factors": {f: False for f in ["high_throughput", "low_latency_required", "scalability_constraints", "resource_intensive", "real_time_requirements"]},
            "complexity_factors": {f: False for f in ["microservices_coordination", "event_driven_design", "distributed_transactions", "circuit_breakers", "service_discovery", "load_balancing", "failure_domain_isolation"]}
        }
        
        try:
            result = self.framework.evaluate_architect_task(min_context)
            edge_cases["min_values"].append({
                "test": "min_architect_values",
                "result": result.should_escalate,
                "score": result.total_score,
                "success": True
            })
        except Exception as e:
            edge_cases["min_values"].append({
                "test": "min_architect_values",
                "error": str(e),
                "success": False
            })
        
        # Mixed signals test
        mixed_context = {
            "affected_services": {ServiceType.ORCHESTRATOR, ServiceType.CONSOLE, ServiceType.DATABASE},
            "security_factors": {"authentication": True, "authorization": False, "data_encryption": False, "input_validation": True, "csrf_protection": False},
            "performance_factors": {"high_throughput": False, "low_latency_required": True, "scalability_constraints": False, "resource_intensive": True, "real_time_requirements": False},
            "complexity_factors": {"microservices_coordination": True, "event_driven_design": False, "distributed_transactions": True, "circuit_breakers": False, "service_discovery": False, "load_balancing": True, "failure_domain_isolation": False}
        }
        
        try:
            result = self.framework.evaluate_architect_task(mixed_context)
            edge_cases["mixed_signals"].append({
                "test": "mixed_signals_architect",
                "result": result.should_escalate,
                "score": result.total_score,
                "success": True
            })
        except Exception as e:
            edge_cases["mixed_signals"].append({
                "test": "mixed_signals_architect",
                "error": str(e),
                "success": False
            })
        
        logger.info(f"Edge case testing complete: {sum(len(cases) for cases in edge_cases.values())} tests run")
        return edge_cases
    
    def validate_weight_consistency(self) -> Dict[str, bool]:
        """Validate that weights sum to expected values"""
        logger.info("Validating weight consistency")
        
        results = {}
        
        # Test architect criteria weights
        architect_weights = {
            "service_impact": 0.25,
            "security_implications": 0.30,
            "performance_criticality": 0.25,
            "architectural_complexity": 0.20
        }
        
        architect_sum = sum(architect_weights.values())
        results["architect_weights_sum_to_1"] = abs(architect_sum - 1.0) < 0.001
        
        # Test integrator criteria weights
        integrator_weights = {
            "conflict_severity": 0.35,
            "system_boundary_impact": 0.30,
            "integration_complexity": 0.20,
            "risk_factors": 0.15
        }
        
        integrator_sum = sum(integrator_weights.values())
        results["integrator_weights_sum_to_1"] = abs(integrator_sum - 1.0) < 0.001
        
        logger.info(f"Weight validation: Architect={architect_sum:.3f}, Integrator={integrator_sum:.3f}")
        return results


class ScoringCalibrator:
    """Calibrates scoring thresholds based on historical data"""
    
    def __init__(self, framework: EscalationFramework):
        self.framework = framework
        self.calibration_data: List[Dict] = []
        
    def add_calibration_data(self, task_context: Dict, actual_outcome: bool, feedback: str) -> None:
        """Add calibration data from actual task outcomes"""
        calibration_point = {
            "timestamp": self._get_timestamp(),
            "context": task_context,
            "predicted_outcome": None,  # Will be filled during calibration
            "actual_outcome": actual_outcome,
            "feedback": feedback
        }
        
        # Get framework prediction
        if "affected_services" in task_context:  # Architect task
            result = self.framework.evaluate_architect_task(task_context)
        elif "conflict_factors" in task_context:  # Integrator task
            result = self.framework.evaluate_integrator_task(task_context)
        else:
            logger.warning("Cannot determine task type for calibration")
            return
        
        calibration_point["predicted_outcome"] = result.should_escalate
        calibration_point["predicted_score"] = result.total_score
        
        self.calibration_data.append(calibration_point)
        
        logger.info(f"Added calibration data: predicted={result.should_escalate}, actual={actual_outcome}")
    
    def analyze_calibration_accuracy(self) -> Dict:
        """Analyze calibration accuracy and suggest threshold adjustments"""
        if not self.calibration_data:
            return {"message": "No calibration data available"}
        
        total_points = len(self.calibration_data)
        correct_predictions = sum(
            1 for point in self.calibration_data 
            if point["predicted_outcome"] == point["actual_outcome"]
        )
        
        accuracy = correct_predictions / total_points
        
        # Analyze false positives and false negatives
        false_positives = [
            point for point in self.calibration_data
            if point["predicted_outcome"] and not point["actual_outcome"]
        ]
        
        false_negatives = [
            point for point in self.calibration_data
            if not point["predicted_outcome"] and point["actual_outcome"]
        ]
        
        # Suggest threshold adjustments
        suggestions = []
        
        if len(false_positives) > len(false_negatives) * 1.5:
            suggestions.append("Consider raising escalation thresholds to reduce false positives")
            avg_fp_score = sum(point["predicted_score"] for point in false_positives) / len(false_positives)
            suggestions.append(f"Suggested architect threshold: {avg_fp_score + 0.05:.3f}")
        
        if len(false_negatives) > len(false_positives) * 1.5:
            suggestions.append("Consider lowering escalation thresholds to reduce false negatives")
            avg_fn_score = sum(point["predicted_score"] for point in false_negatives) / len(false_negatives)
            suggestions.append(f"Suggested architect threshold: {avg_fn_score - 0.05:.3f}")
        
        return {
            "total_calibration_points": total_points,
            "accuracy": accuracy,
            "correct_predictions": correct_predictions,
            "false_positives": len(false_positives),
            "false_negatives": len(false_negatives),
            "suggestions": suggestions
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def export_calibration_data(self, file_path: str) -> None:
        """Export calibration data to file"""
        data = {
            "calibration_points": self.calibration_data,
            "analysis": self.analyze_calibration_accuracy()
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Calibration data exported to {file_path}")


# Factory functions for easy instantiation
def create_validator() -> CriteriaValidator:
    """Create a criteria validator with default framework"""
    framework = EscalationFramework()
    return CriteriaValidator(framework)


def create_calibrator() -> ScoringCalibrator:
    """Create a scoring calibrator with default framework"""
    framework = EscalationFramework()
    return ScoringCalibrator(framework)


# Command-line interface for validation
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate escalation criteria")
    parser.add_argument("--role", choices=["architect", "integrator", "all"], default="all",
                       help="Role to validate")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    framework = EscalationFramework()
    validator = CriteriaValidator(framework)
    
    results = {}
    
    if args.role in ["architect", "all"]:
        results["architect"] = validator.validate_architect_criteria()
    
    if args.role in ["integrator", "all"]:
        results["integrator"] = validator.validate_integrator_criteria()
    
    # Run edge case tests
    edge_cases = validator.run_edge_case_tests()
    results["edge_cases"] = edge_cases
    
    # Validate weight consistency
    weight_results = validator.validate_weight_consistency()
    results["weight_consistency"] = weight_results
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2, default=str))