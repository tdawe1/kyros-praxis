#!/usr/bin/env python3
"""
Comprehensive Test Runner for Hybrid Model Escalation Workflows

This script runs all test scenarios, validation scripts, integration tests, and performance
benchmarks for the escalation workflow system. It provides a complete testing solution
with reporting and analysis.
"""

import argparse
import json
import sys
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

# Import test modules
from test_escalation_scenarios import EscalationTestScenarios, Role, EscalationModel
from test_escalation_integration import IntegrationTestSuite
from scripts.validate_escalation_workflows import EscalationWorkflowValidator
from scripts.benchmark_escalation_performance import PerformanceBenchmark

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_runner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """Main test runner for all escalation workflow tests."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("test_results")
        self.output_dir.mkdir(exist_ok=True)
        
        # Test suite results
        self.test_results = {
            'scenarios': {},
            'validation': {},
            'integration': {},
            'performance': {},
            'summary': {}
        }
        
        # Overall test status
        self.overall_success = True
        self.test_start_time = time.time()
    
    def run_scenario_tests(self) -> Dict[str, Any]:
        """Run escalation scenario tests."""
        logger.info("🎯 Running escalation scenario tests...")
        
        try:
            scenarios = EscalationTestScenarios()
            
            # Test escalation triggers for all roles
            architect_scenarios = scenarios.get_scenarios_by_role(Role.ARCHITECT)
            integrator_scenarios = scenarios.get_scenarios_by_role(Role.INTEGRATOR)
            
            results = {
                'total_scenarios': len(scenarios.test_scenarios),
                'architect_scenarios': len(architect_scenarios),
                'integrator_scenarios': len(integrator_scenarios),
                'escalation_scenarios': len(scenarios.get_escalation_scenarios()),
                'non_escalation_scenarios': len(scenarios.get_non_escalation_scenarios()),
                'scenarios_validated': 0,
                'validation_errors': []
            }
            
            # Validate each scenario
            for scenario in scenarios.test_scenarios:
                try:
                    # Validate escalation triggers
                    for trigger in scenario.triggers:
                        if trigger.should_escalate:
                            assert trigger.expected_model == EscalationModel.CLAUDE_41_OPUS, \
                                "Escalation scenario should use Claude 4.1 Opus"
                        else:
                            assert trigger.expected_model == EscalationModel.GLM_45, \
                                "Non-escalation scenario should use GLM-4.5"
                    
                    results['scenarios_validated'] += 1
                    
                except Exception as e:
                    results['validation_errors'].append(f"Scenario {scenario.name}: {str(e)}")
                    self.overall_success = False
            
            # Export scenarios for use in other tests
            scenarios.export_scenarios(self.output_dir / "test_scenarios_export.json")
            
            logger.info(f"✅ Scenario tests completed: {results['scenarios_validated']}/{results['total_scenarios']} validated")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Scenario tests failed: {e}")
            self.overall_success = False
            return {'error': str(e)}
    
    def run_validation_tests(self) -> Dict[str, Any]:
        """Run workflow validation tests."""
        logger.info("🔧 Running workflow validation tests...")
        
        try:
            validator = EscalationWorkflowValidator()
            report = validator.run_comprehensive_validation()
            
            # Save detailed report
            report_path = self.output_dir / "validation_report.json"
            validator.save_report(report, report_path)
            
            # Check for failures
            validation_success = report['failed'] == 0
            if not validation_success:
                self.overall_success = False
                logger.warning(f"⚠️ Validation found {report['failed']} failures")
            
            logger.info(f"✅ Validation completed: {report['passed']} passed, {report['failed']} failed")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Validation tests failed: {e}")
            self.overall_success = False
            return {'error': str(e)}
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        logger.info("🔗 Running integration tests...")
        
        try:
            integration_suite = IntegrationTestSuite()
            integration_results = {}
            
            # Test key scenarios
            test_scenarios = [
                "architect_multi_service_decision",
                "architect_security_critical",
                "architect_performance_critical",
                "integrator_complex_conflict",
                "integrator_simple_conflict"
            ]
            
            for scenario_name in test_scenarios:
                try:
                    result = asyncio.run(integration_suite.run_end_to_end_test(scenario_name))
                    integration_results[scenario_name] = result
                    
                    if not result['overall_success']:
                        self.overall_success = False
                        
                except Exception as e:
                    logger.error(f"❌ Integration test {scenario_name} failed: {e}")
                    integration_results[scenario_name] = {'error': str(e)}
                    self.overall_success = False
            
            # Run load test
            try:
                load_result = asyncio.run(integration_suite.run_load_test(concurrent_requests=20))
                integration_results['load_test'] = load_result
                
                # Check load test performance
                if load_result['avg_response_time'] > 1.0:
                    logger.warning("⚠️ Load test response time above threshold")
                    self.overall_success = False
                
            except Exception as e:
                logger.error(f"❌ Load test failed: {e}")
                integration_results['load_test'] = {'error': str(e)}
                self.overall_success = False
            
            # Run cost analysis
            try:
                cost_result = asyncio.run(integration_suite.run_cost_analysis_test())
                integration_results['cost_analysis'] = cost_result
                
                # Check cost savings
                if cost_result['savings_percentage'] < 20:
                    logger.warning("⚠️ Cost savings below target")
                    self.overall_success = False
                
            except Exception as e:
                logger.error(f"❌ Cost analysis failed: {e}")
                integration_results['cost_analysis'] = {'error': str(e)}
                self.overall_success = False
            
            logger.info(f"✅ Integration tests completed for {len(test_scenarios)} scenarios")
            
            return integration_results
            
        except Exception as e:
            logger.error(f"❌ Integration tests failed: {e}")
            self.overall_success = False
            return {'error': str(e)}
    
    def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        logger.info("⚡ Running performance benchmarks...")
        
        try:
            benchmark = PerformanceBenchmark(self.output_dir)
            
            # Run light load benchmark
            light_suite = asyncio.run(benchmark.run_concurrent_benchmark('light_load'))
            
            # Run medium load benchmark  
            medium_suite = asyncio.run(benchmark.run_concurrent_benchmark('medium_load'))
            
            results = {
                'light_load': {
                    'throughput': light_suite.summary_statistics['throughput'],
                    'avg_response_time': light_suite.summary_statistics['execution_time_stats']['mean'],
                    'success_rate': light_suite.summary_statistics['success_rate'],
                    'accuracy': light_suite.summary_statistics['accuracy_analysis']['average_accuracy']
                },
                'medium_load': {
                    'throughput': medium_suite.summary_statistics['throughput'],
                    'avg_response_time': medium_suite.summary_statistics['execution_time_stats']['mean'],
                    'success_rate': medium_suite.summary_statistics['success_rate'],
                    'accuracy': medium_suite.summary_statistics['accuracy_analysis']['average_accuracy']
                }
            }
            
            # Check performance thresholds
            if medium_suite.summary_statistics['execution_time_stats']['mean'] > 2.0:
                logger.warning("⚠️ Medium load response time above threshold")
                self.overall_success = False
            
            if medium_suite.summary_statistics['success_rate'] < 0.95:
                logger.warning("⚠️ Medium load success rate below threshold")
                self.overall_success = False
            
            logger.info("✅ Performance benchmarks completed")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Performance benchmarks failed: {e}")
            self.overall_success = False
            return {'error': str(e)}
    
    def run_pytest_suite(self) -> Dict[str, Any]:
        """Run pytest test suite."""
        logger.info("🧪 Running pytest suite...")
        
        try:
            # Run pytest on our test files
            test_files = [
                "tests/test_escalation_scenarios.py",
                "tests/test_escalation_integration.py"
            ]
            
            pytest_results = {}
            
            for test_file in test_files:
                if Path(test_file).exists():
                    result = subprocess.run(
                        ["python", "-m", "pytest", test_file, "-v", "--json-report"],
                        capture_output=True,
                        text=True
                    )
                    
                    pytest_results[test_file] = {
                        'returncode': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'success': result.returncode == 0
                    }
                    
                    if result.returncode != 0:
                        logger.warning(f"⚠️ Pytest {test_file} failed with return code {result.returncode}")
                        self.overall_success = False
                else:
                    logger.warning(f"⚠️ Test file {test_file} not found")
                    pytest_results[test_file] = {'error': 'File not found'}
            
            logger.info("✅ Pytest suite completed")
            
            return pytest_results
            
        except Exception as e:
            logger.error(f"❌ Pytest suite failed: {e}")
            self.overall_success = False
            return {'error': str(e)}
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        logger.info("📊 Generating comprehensive report...")
        
        total_execution_time = time.time() - self.test_start_time
        
        report = {
            'test_run_timestamp': datetime.now().isoformat(),
            'total_execution_time': total_execution_time,
            'overall_success': self.overall_success,
            'test_results': self.test_results,
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'warning_tests': 0,
                'performance_metrics': {}
            }
        }
        
        # Calculate summary statistics
        for category, results in self.test_results.items():
            if isinstance(results, dict) and 'total_tests' in results:
                report['summary']['total_tests'] += results['total_tests']
                report['summary']['passed_tests'] += results.get('passed', 0)
                report['summary']['failed_tests'] += results.get('failed', 0)
                report['summary']['warning_tests'] += results.get('warnings', 0)
        
        # Add performance metrics
        if 'performance' in self.test_results:
            report['summary']['performance_metrics'] = self.test_results['performance']
        
        # Generate recommendations
        report['recommendations'] = self.generate_recommendations()
        
        # Save report
        report_path = self.output_dir / "comprehensive_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"💾 Comprehensive report saved to {report_path}")
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Analyze test results
        if not self.overall_success:
            recommendations.append("🚨 Overall test failure detected. Review all failed tests and address underlying issues.")
        
        # Check scenario validation
        if 'scenarios' in self.test_results:
            scenarios = self.test_results['scenarios']
            if 'validation_errors' in scenarios and scenarios['validation_errors']:
                recommendations.extend([
                    f"❌ Found {len(scenarios['validation_errors'])} scenario validation errors:",
                    "  - Review escalation trigger logic",
                    "  - Verify model selection criteria",
                    "  - Update test scenarios as needed"
                ])
        
        # Check validation results
        if 'validation' in self.test_results:
            validation = self.test_results['validation']
            if validation.get('failed', 0) > 0:
                recommendations.append(f"⚠️ Validation found {validation['failed']} failures. Address configuration and logic issues.")
        
        # Check integration results
        if 'integration' in self.test_results:
            integration = self.test_results['integration']
            for scenario_name, result in integration.items():
                if isinstance(result, dict) and not result.get('overall_success', True):
                    recommendations.append(f"❌ Integration test {scenario_name} failed. Review workflow implementation.")
        
        # Check performance
        if 'performance' in self.test_results:
            performance = self.test_results['performance']
            if 'medium_load' in performance:
                medium = performance['medium_load']
                if medium.get('avg_response_time', 0) > 2.0:
                    recommendations.append("🐌 Performance degradation under medium load. Consider optimization.")
                if medium.get('success_rate', 1.0) < 0.95:
                    recommendations.append("⚠️ Low success rate under load. Review error handling and resilience.")
        
        # General recommendations
        recommendations.extend([
            "📊 Set up continuous testing and monitoring.",
            "🔄 Implement automated regression testing.",
            "📈 Regular performance reviews and optimization.",
            "🔍 Monitor cost optimization and model usage patterns.",
            "🛡️ Ensure escalation criteria remain aligned with business requirements."
        ])
        
        return recommendations
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites."""
        logger.info("🚀 Starting comprehensive test suite for escalation workflows")
        print("=" * 70)
        
        # Run scenario tests
        print("\n🎯 Phase 1: Escalation Scenario Tests")
        print("-" * 40)
        self.test_results['scenarios'] = self.run_scenario_tests()
        
        # Run validation tests
        print("\n🔧 Phase 2: Workflow Validation Tests")
        print("-" * 40)
        self.test_results['validation'] = self.run_validation_tests()
        
        # Run integration tests
        print("\n🔗 Phase 3: Integration Tests")
        print("-" * 40)
        self.test_results['integration'] = self.run_integration_tests()
        
        # Run performance benchmarks
        print("\n⚡ Phase 4: Performance Benchmarks")
        print("-" * 40)
        self.test_results['performance'] = self.run_performance_benchmarks()
        
        # Run pytest suite
        print("\n🧪 Phase 5: Pytest Suite")
        print("-" * 40)
        self.test_results['pytest'] = self.run_pytest_suite()
        
        # Generate comprehensive report
        print("\n📊 Phase 6: Report Generation")
        print("-" * 40)
        report = self.generate_comprehensive_report()
        
        # Print summary
        self.print_summary(report)
        
        return report
    
    def print_summary(self, report: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("🏁 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        # Overall status
        status_icon = "✅" if self.overall_success else "❌"
        print(f"{status_icon} Overall Status: {'PASSED' if self.overall_success else 'FAILED'}")
        print(f"⏱️  Total Execution Time: {report['total_execution_time']:.1f} seconds")
        print(f"📅 Test Run: {report['test_run_timestamp']}")
        
        # Summary statistics
        summary = report['summary']
        print("\n📊 Test Statistics:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  ✅ Passed: {summary['passed_tests']}")
        print(f"  ❌ Failed: {summary['failed_tests']}")
        print(f"  ⚠️  Warnings: {summary['warning_tests']}")
        
        # Phase summaries
        print("\n📋 Phase Results:")
        phases = {
            'scenarios': 'Scenario Tests',
            'validation': 'Validation Tests',
            'integration': 'Integration Tests',
            'performance': 'Performance Benchmarks',
            'pytest': 'Pytest Suite'
        }
        
        for phase_key, phase_name in phases.items():
            if phase_key in self.test_results:
                result = self.test_results[phase_key]
                if isinstance(result, dict):
                    if 'total_tests' in result:
                        passed = result.get('passed', 0)
                        failed = result.get('failed', 0)
                        status = "✅" if failed == 0 else "❌"
                        print(f"  {status} {phase_name}: {passed} passed, {failed} failed")
                    elif 'error' in result:
                        print(f"  ❌ {phase_name}: ERROR - {result['error']}")
        
        # Recommendations
        if report['recommendations']:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print(f"\n📁 Detailed reports saved to: {self.output_dir}")
        
        # Exit code
        exit_code = 0 if self.overall_success else 1
        print(f"\n🔚 Exit Code: {exit_code}")

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Comprehensive test runner for escalation workflows')
    parser.add_argument('--output-dir', type=Path, default=Path('test_results'),
                       help='Output directory for test results')
    parser.add_argument('--phase', choices=['scenarios', 'validation', 'integration', 'performance', 'pytest', 'all'],
                       default='all', help='Run specific test phase')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    runner = ComprehensiveTestRunner(args.output_dir)
    
    try:
        if args.phase == 'all':
            runner.run_all_tests()
        else:
            # Run specific phase
            phase_methods = {
                'scenarios': runner.run_scenario_tests,
                'validation': runner.run_validation_tests,
                'integration': runner.run_integration_tests,
                'performance': runner.run_performance_benchmarks,
                'pytest': runner.run_pytest_suite
            }
            
            if args.phase in phase_methods:
                result = phase_methods[args.phase]()
                runner.test_results[args.phase] = result
                runner.generate_comprehensive_report()
                runner.print_summary(runner.generate_comprehensive_report())
            else:
                logger.error(f"Unknown phase: {args.phase}")
                return 1
        
        return 0 if runner.overall_success else 1
        
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())