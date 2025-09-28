#!/usr/bin/env python3
"""
Performance Benchmarking for Hybrid Model Escalation Decisions

This module provides comprehensive performance benchmarking tools for measuring
escalation decision performance, including latency, throughput, accuracy, and cost analysis.
"""

import time
import json
import asyncio
import statistics
import matplotlib.pyplot as plt
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import numpy as np
import logging

# Import our escalation components
from test_escalation_integration import EscalationEngine, MockModelProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Result of a single benchmark test."""
    test_name: str
    execution_time: float
    success: bool
    memory_usage_mb: float
    cpu_usage_percent: float
    tokens_processed: int
    cost_usd: float
    accuracy_score: float
    additional_metrics: Dict[str, Any] = None

@dataclass
class BenchmarkSuite:
    """Complete benchmark suite with multiple test runs."""
    name: str
    description: str
    test_config: Dict[str, Any]
    results: List[BenchmarkResult]
    summary_statistics: Dict[str, Any]
    timestamp: datetime

class PerformanceBenchmark:
    """Main performance benchmarking class for escalation workflows."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("benchmark_results")
        self.output_dir.mkdir(exist_ok=True)
        
        self.escalation_engine = EscalationEngine()
        self.model_provider = MockModelProvider()
        
        # Benchmark configurations
        self.benchmark_configs = {
            'light_load': {
                'concurrent_requests': 5,
                'iterations': 100,
                'think_time': 0.1,
                'description': 'Light load simulation (5 concurrent requests)'
            },
            'medium_load': {
                'concurrent_requests': 20,
                'iterations': 200,
                'think_time': 0.05,
                'description': 'Medium load simulation (20 concurrent requests)'
            },
            'heavy_load': {
                'concurrent_requests': 50,
                'iterations': 500,
                'think_time': 0.02,
                'description': 'Heavy load simulation (50 concurrent requests)'
            },
            'stress_test': {
                'concurrent_requests': 100,
                'iterations': 1000,
                'think_time': 0.01,
                'description': 'Stress test (100 concurrent requests)'
            }
        }
        
        # Test scenarios with varying complexity
        self.test_scenarios = [
            {
                'name': 'simple_architect_decision',
                'role': 'architect',
                'context': {
                    'services_affected': ['console'],
                    'decision_type': 'single_service_design',
                    'complexity': 'low'
                },
                'expected_escalation': False,
                'expected_model': 'glm-4.5'
            },
            {
                'name': 'complex_architect_decision',
                'role': 'architect',
                'context': {
                    'services_affected': ['orchestrator', 'console', 'terminal-daemon', 'packages/core'],
                    'security_implications': True,
                    'risk_level': 'critical',
                    'performance_critical': True,
                    'expected_load': 10000,
                    'complexity': 'high'
                },
                'expected_escalation': True,
                'expected_model': 'claude-4.1-opus'
            },
            {
                'name': 'simple_integrator_conflict',
                'role': 'integrator',
                'context': {
                    'conflict_services': ['console'],
                    'conflict_types': ['formatting'],
                    'complexity': 'low'
                },
                'expected_escalation': False,
                'expected_model': 'glm-4.5'
            },
            {
                'name': 'complex_integrator_conflict',
                'role': 'integrator',
                'context': {
                    'conflict_services': ['orchestrator', 'console', 'terminal-daemon', 'packages/core'],
                    'conflict_types': ['api_contract', 'data_model', 'dependency'],
                    'system_boundary_changes': True,
                    'complexity': 'high'
                },
                'expected_escalation': True,
                'expected_model': 'claude-4.1-opus'
            },
            {
                'name': 'implementer_task',
                'role': 'implementer',
                'context': {
                    'task_type': 'bug_fix',
                    'services_affected': ['console'],
                    'complexity': 'medium'
                },
                'expected_escalation': False,
                'expected_model': 'glm-4.5'
            }
        ]
    
    def run_single_benchmark(self, scenario: Dict[str, Any]) -> BenchmarkResult:
        """Run a single benchmark test for a scenario."""
        start_time = time.time()
        success = True
        
        try:
            # Evaluate escalation decision
            decision = self.escalation_engine.evaluate_escalation(
                scenario['role'],
                scenario['context']
            )
            
            # Validate decision accuracy
            accuracy = 1.0 if (
                decision.should_escalate == scenario['expected_escalation'] and
                decision.selected_model == scenario['expected_model']
            ) else 0.0
            
            # Simulate model execution cost
            estimated_tokens = len(str(scenario['context'])) // 4
            cost = (self.model_provider.costs_per_1k_tokens[decision.selected_model] * estimated_tokens) / 1000
            
            # Get resource usage (simulated)
            memory_usage = self._estimate_memory_usage(scenario['context'])
            cpu_usage = self._estimate_cpu_usage(decision.execution_time)
            
            execution_time = time.time() - start_time
            
            return BenchmarkResult(
                test_name=scenario['name'],
                execution_time=execution_time,
                success=success,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
                tokens_processed=estimated_tokens,
                cost_usd=cost,
                accuracy_score=accuracy,
                additional_metrics={
                    'decision_confidence': decision.confidence,
                    'model_selected': decision.selected_model,
                    'should_escalate': decision.should_escalate,
                    'reasoning': decision.reasoning
                }
            )
            
        except Exception as e:
            logger.error(f"Benchmark failed for {scenario['name']}: {e}")
            return BenchmarkResult(
                test_name=scenario['name'],
                execution_time=time.time() - start_time,
                success=False,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                tokens_processed=0,
                cost_usd=0,
                accuracy_score=0,
                additional_metrics={'error': str(e)}
            )
    
    def _estimate_memory_usage(self, context: Dict[str, Any]) -> float:
        """Estimate memory usage for a scenario."""
        # Simulated memory usage based on context complexity
        base_memory = 10.0  # MB
        complexity_multiplier = len(str(context)) / 1000.0
        return base_memory * (1 + complexity_multiplier)
    
    def _estimate_cpu_usage(self, execution_time: float) -> float:
        """Estimate CPU usage percentage."""
        # Simulated CPU usage based on execution time
        if execution_time < 0.01:
            return 20.0
        elif execution_time < 0.1:
            return 50.0
        else:
            return 80.0
    
    async def run_concurrent_benchmark(self, config_name: str) -> BenchmarkSuite:
        """Run concurrent benchmark test with specified configuration."""
        config = self.benchmark_configs[config_name]
        
        logger.info(f"🚀 Running {config_name} benchmark: {config['description']}")
        
        results = []
        start_time = time.time()
        
        # Create tasks for concurrent execution
        tasks = []
        for i in range(config['iterations']):
            # Cycle through test scenarios
            scenario = self.test_scenarios[i % len(self.test_scenarios)]
            
            if config['concurrent_requests'] == 1:
                # Sequential execution
                result = self.run_single_benchmark(scenario)
                results.append(result)
            else:
                # Concurrent execution
                tasks.append(asyncio.create_task(
                    asyncio.to_thread(self.run_single_benchmark, scenario)
                ))
        
        # Execute concurrent tasks in batches
        if config['concurrent_requests'] > 1:
            for i in range(0, len(tasks), config['concurrent_requests']):
                batch = tasks[i:i + config['concurrent_requests']]
                batch_results = await asyncio.gather(*batch)
                results.extend(batch_results)
                
                # Simulate think time between batches
                if config['think_time'] > 0:
                    await asyncio.sleep(config['think_time'])
        
        total_time = time.time() - start_time
        
        # Calculate summary statistics
        summary = self._calculate_summary_statistics(results, total_time, config)
        
        return BenchmarkSuite(
            name=config_name,
            description=config['description'],
            test_config=config,
            results=results,
            summary_statistics=summary,
            timestamp=datetime.now()
        )
    
    def _calculate_summary_statistics(self, results: List[BenchmarkResult], 
                                   total_time: float, config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for benchmark results."""
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return {
                'error': 'No successful results',
                'total_tests': len(results),
                'success_rate': 0.0
            }
        
        execution_times = [r.execution_time for r in successful_results]
        memory_usage = [r.memory_usage_mb for r in successful_results]
        cpu_usage = [r.cpu_usage_percent for r in successful_results]
        costs = [r.cost_usd for r in successful_results]
        accuracies = [r.accuracy_score for r in successful_results]
        
        # Basic statistics
        stats = {
            'total_tests': len(results),
            'successful_tests': len(successful_results),
            'success_rate': len(successful_results) / len(results),
            'total_execution_time': total_time,
            'throughput': len(successful_results) / total_time,
            
            'execution_time_stats': {
                'min': min(execution_times),
                'max': max(execution_times),
                'mean': statistics.mean(execution_times),
                'median': statistics.median(execution_times),
                'std_dev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                'p95': np.percentile(execution_times, 95),
                'p99': np.percentile(execution_times, 99)
            },
            
            'memory_usage_stats': {
                'min': min(memory_usage),
                'max': max(memory_usage),
                'mean': statistics.mean(memory_usage),
                'median': statistics.median(memory_usage)
            },
            
            'cpu_usage_stats': {
                'min': min(cpu_usage),
                'max': max(cpu_usage),
                'mean': statistics.mean(cpu_usage),
                'median': statistics.median(cpu_usage)
            },
            
            'cost_analysis': {
                'total_cost': sum(costs),
                'average_cost_per_request': statistics.mean(costs),
                'min_cost': min(costs),
                'max_cost': max(costs)
            },
            
            'accuracy_analysis': {
                'average_accuracy': statistics.mean(accuracies),
                'min_accuracy': min(accuracies),
                'max_accuracy': max(accuracies),
                'perfect_decisions': sum(1 for a in accuracies if a == 1.0)
            }
        }
        
        # Model usage statistics
        model_usage = {}
        escalation_count = 0
        for result in successful_results:
            model = result.additional_metrics.get('model_selected', 'unknown')
            model_usage[model] = model_usage.get(model, 0) + 1
            if result.additional_metrics.get('should_escalate', False):
                escalation_count += 1
        
        stats['model_usage'] = model_usage
        stats['escalation_rate'] = escalation_count / len(successful_results)
        
        # Performance targets
        stats['performance_targets'] = {
            'target_throughput': config['concurrent_requests'],
            'target_success_rate': 0.99,
            'target_accuracy': 0.95,
            'target_avg_response_time': 1.0,  # seconds
            'target_cost_efficiency': 0.8  # vs premium model only
        }
        
        # Check if targets met
        stats['targets_met'] = {
            'throughput': stats['throughput'] >= stats['performance_targets']['target_throughput'],
            'success_rate': stats['success_rate'] >= stats['performance_targets']['target_success_rate'],
            'accuracy': stats['accuracy_analysis']['average_accuracy'] >= stats['performance_targets']['target_accuracy'],
            'response_time': stats['execution_time_stats']['mean'] <= stats['performance_targets']['target_avg_response_time']
        }
        
        return stats
    
    def run_comprehensive_benchmark(self) -> Dict[str, BenchmarkSuite]:
        """Run comprehensive benchmark across all configurations."""
        logger.info("🚀 Starting comprehensive performance benchmarking")
        
        results = {}
        
        # Run all benchmark configurations
        for config_name in self.benchmark_configs.keys():
            suite = asyncio.run(self.run_concurrent_benchmark(config_name))
            results[config_name] = suite
            
            # Save individual benchmark results
            self.save_benchmark_suite(suite)
        
        # Generate comparison report
        comparison_report = self.generate_comparison_report(results)
        
        return results
    
    def save_benchmark_suite(self, suite: BenchmarkSuite):
        """Save benchmark suite results to file."""
        filename = f"benchmark_{suite.name}_{suite.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        # Convert to serializable format
        suite_data = {
            'name': suite.name,
            'description': suite.description,
            'test_config': suite.test_config,
            'timestamp': suite.timestamp.isoformat(),
            'summary_statistics': suite.summary_statistics,
            'results': [asdict(result) for result in suite.results]
        }
        
        with open(filepath, 'w') as f:
            json.dump(suite_data, f, indent=2, default=str)
        
        logger.info(f"💾 Saved benchmark results to {filepath}")
    
    def generate_comparison_report(self, results: Dict[str, BenchmarkSuite]) -> Dict[str, Any]:
        """Generate comparison report across all benchmark configurations."""
        logger.info("📊 Generating comparison report")
        
        comparison = {
            'report_timestamp': datetime.now().isoformat(),
            'benchmark_count': len(results),
            'configurations': list(results.keys()),
            'performance_comparison': {},
            'cost_analysis': {},
            'recommendations': []
        }
        
        # Extract key metrics for comparison
        for config_name, suite in results.items():
            stats = suite.summary_statistics
            
            comparison['performance_comparison'][config_name] = {
                'throughput': stats['throughput'],
                'avg_response_time': stats['execution_time_stats']['mean'],
                'success_rate': stats['success_rate'],
                'accuracy': stats['accuracy_analysis']['average_accuracy'],
                'escalation_rate': stats['escalation_rate']
            }
            
            comparison['cost_analysis'][config_name] = {
                'total_cost': stats['cost_analysis']['total_cost'],
                'avg_cost_per_request': stats['cost_analysis']['average_cost_per_request'],
                'glm_usage_percentage': stats['model_usage'].get('glm-4.5', 0) / stats['successful_tests'] * 100,
                'claude_usage_percentage': stats['model_usage'].get('claude-4.1-opus', 0) / stats['successful_tests'] * 100
            }
        
        # Generate recommendations
        comparison['recommendations'] = self._generate_benchmark_recommendations(comparison)
        
        # Save comparison report
        report_path = self.output_dir / "benchmark_comparison_report.json"
        with open(report_path, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)
        
        logger.info(f"💾 Saved comparison report to {report_path}")
        
        return comparison
    
    def _generate_benchmark_recommendations(self, comparison: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on benchmark results."""
        recommendations = []
        
        # Analyze performance trends
        perf_data = comparison['performance_comparison']
        
        # Check throughput scaling
        throughputs = [data['throughput'] for data in perf_data.values()]
        if max(throughputs) / min(throughputs) < 5:
            recommendations.append("⚠️ Limited throughput scaling observed. Consider optimizing concurrent processing.")
        
        # Check response time consistency
        response_times = [data['avg_response_time'] for data in perf_data.values()]
        if max(response_times) > 2.0:
            recommendations.append("🐌 High response times detected under heavy load. Consider caching or optimization.")
        
        # Check cost efficiency
        cost_data = comparison['cost_analysis']
        for config, cost_info in cost_data.items():
            glm_usage = cost_info['glm_usage_percentage']
            if glm_usage < 70:
                recommendations.append(f"💰 Low GLM-4.5 usage in {config} ({glm_usage:.1f}%). Consider optimizing escalation criteria.")
        
        # Check accuracy
        accuracies = [data['accuracy'] for data in perf_data.values()]
        avg_accuracy = sum(accuracies) / len(accuracies)
        if avg_accuracy < 0.95:
            recommendations.append("🎯 Low accuracy detected. Review escalation criteria and model selection logic.")
        
        # General recommendations
        recommendations.extend([
            "📊 Set up continuous monitoring of escalation performance.",
            "🔄 Implement automated scaling based on load patterns.",
            "💡 Consider implementing request queuing for high-load scenarios.",
            "🔍 Regular performance reviews and optimization cycles."
        ])
        
        return recommendations
    
    def generate_visualizations(self, results: Dict[str, BenchmarkSuite]):
        """Generate performance visualization charts."""
        logger.info("📈 Generating performance visualizations")
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Escalation Workflow Performance Benchmark Results', fontsize=16)
        
        configs = list(results.keys())
        
        # Throughput comparison
        throughputs = [results[config].summary_statistics['throughput'] for config in configs]
        axes[0, 0].bar(configs, throughputs)
        axes[0, 0].set_title('Throughput (requests/second)')
        axes[0, 0].set_ylabel('Requests/sec')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Response time comparison
        response_times = [results[config].summary_statistics['execution_time_stats']['mean'] for config in configs]
        axes[0, 1].bar(configs, response_times)
        axes[0, 1].set_title('Average Response Time')
        axes[0, 1].set_ylabel('Seconds')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Cost comparison
        costs = [results[config].summary_statistics['cost_analysis']['average_cost_per_request'] for config in configs]
        axes[1, 0].bar(configs, costs)
        axes[1, 0].set_title('Average Cost per Request')
        axes[1, 0].set_ylabel('USD')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Accuracy comparison
        accuracies = [results[config].summary_statistics['accuracy_analysis']['average_accuracy'] for config in configs]
        axes[1, 1].bar(configs, accuracies)
        axes[1, 1].set_title('Decision Accuracy')
        axes[1, 1].set_ylabel('Accuracy Score')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].set_ylim(0, 1)
        
        plt.tight_layout()
        
        # Save visualization
        viz_path = self.output_dir / "performance_comparison.png"
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"💾 Saved performance visualization to {viz_path}")
    
    def run_benchmark_and_report(self) -> Dict[str, Any]:
        """Run complete benchmark suite and generate comprehensive report."""
        logger.info("🚀 Starting comprehensive benchmark suite")
        
        # Run benchmarks
        results = self.run_comprehensive_benchmark()
        
        # Generate comparison report
        comparison_report = self.generate_comparison_report(results)
        
        # Generate visualizations
        self.generate_visualizations(results)
        
        # Print summary
        print("\n📊 Benchmark Summary")
        print("=" * 50)
        for config_name, suite in results.items():
            stats = suite.summary_statistics
            print(f"\n{config_name.upper()}:")
            print(f"  📈 Throughput: {stats['throughput']:.1f} req/sec")
            print(f"  ⏱️  Avg Response: {stats['execution_time_stats']['mean']:.3f}s")
            print(f"  ✅ Success Rate: {stats['success_rate']:.1%}")
            print(f"  🎯 Accuracy: {stats['accuracy_analysis']['average_accuracy']:.1%}")
            print(f"  💰 Cost/Request: ${stats['cost_analysis']['average_cost_per_request']:.6f}")
            print(f"  🔼 Escalation Rate: {stats['escalation_rate']:.1%}")
        
        print("\n💡 Recommendations:")
        for i, rec in enumerate(comparison_report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        return {
            'benchmark_results': results,
            'comparison_report': comparison_report,
            'output_directory': str(self.output_dir)
        }

def main():
    """Main execution function."""
    benchmark = PerformanceBenchmark()
    
    print("🚀 Hybrid Model Escalation Performance Benchmark")
    print("=" * 60)
    
    # Run comprehensive benchmark
    results = benchmark.run_benchmark_and_report()
    
    print(f"\n📁 Benchmark results saved to: {results['output_directory']}")
    
    return 0

if __name__ == "__main__":
    exit(main())