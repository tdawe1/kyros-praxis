import asyncio
import time
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
from dataclasses import dataclass

from .types import (
    ModelType, 
    ModelPerformanceMetrics
)

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for performance benchmarks"""
    model_types: List[ModelType]
    test_prompts: List[str]
    iterations_per_model: int
    concurrency_levels: List[int]
    metrics_to_collect: List[str]
    warmup_iterations: int = 3
    timeout_per_request: float = 60.0


@dataclass
class BenchmarkResult:
    """Result of a benchmark run"""
    benchmark_id: str
    config: BenchmarkConfig
    start_time: datetime
    end_time: datetime
    results: Dict[str, Any]
    summary: Dict[str, Any]
    recommendations: List[str]


class PerformanceBenchmark:
    """Performance benchmarking tool for model comparison"""
    
    def __init__(self, 
                 model_client,  # Model execution client
                 monitor,       # Performance monitor
                 storage=None):
        self.model_client = model_client
        self.monitor = monitor
        self.storage = storage
        self.benchmark_history = []
    
    async def run_comparative_benchmark(self, 
                                     config: BenchmarkConfig) -> BenchmarkResult:
        """Run comparative benchmark across multiple models"""
        benchmark_id = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        logger.info(f"Starting benchmark {benchmark_id} with {len(config.model_types)} models")
        
        results = {}
        
        # Run benchmarks for each model
        for model_type in config.model_types:
            logger.info(f"Benchmarking {model_type.value}")
            
            model_results = await self._benchmark_single_model(model_type, config)
            results[model_type.value] = model_results
        
        end_time = datetime.now()
        
        # Generate summary and recommendations
        summary = await self._generate_summary(results, config)
        recommendations = await self._generate_recommendations(results, config)
        
        benchmark_result = BenchmarkResult(
            benchmark_id=benchmark_id,
            config=config,
            start_time=start_time,
            end_time=end_time,
            results=results,
            summary=summary,
            recommendations=recommendations
        )
        
        # Store benchmark result
        self.benchmark_history.append(benchmark_result)
        if self.storage:
            await self.storage.store_benchmark(benchmark_result)
        
        logger.info(f"Completed benchmark {benchmark_id}")
        return benchmark_result
    
    async def _benchmark_single_model(self, 
                                     model_type: ModelType, 
                                     config: BenchmarkConfig) -> Dict[str, Any]:
        """Benchmark a single model"""
        results = {
            'model_type': model_type.value,
            'executions': [],
            'concurrency_results': {}
        }
        
        # Warmup iterations
        for i in range(config.warmup_iterations):
            prompt = config.test_prompts[i % len(config.test_prompts)]
            await self._execute_model_request(model_type, prompt, warmup=True)
        
        # Sequential benchmarking
        for iteration in range(config.iterations_per_model):
            prompt = config.test_prompts[iteration % len(config.test_prompts)]
            
            execution_result = await self._execute_model_request(
                model_type, prompt, 
                request_id=f"{model_type.value}_seq_{iteration}",
                timeout=config.timeout_per_request
            )
            
            results['executions'].append(execution_result)
        
        # Concurrency testing
        for concurrency in config.concurrency_levels:
            concurrency_results = await self._benchmark_concurrency(
                model_type, config.test_prompts, concurrency
            )
            results['concurrency_results'][str(concurrency)] = concurrency_results
        
        return results
    
    async def _execute_model_request(self,
                                    model_type: ModelType,
                                    prompt: str,
                                    request_id: Optional[str] = None,
                                    timeout: float = 60.0,
                                    warmup: bool = False) -> Dict[str, Any]:
        """Execute a single model request and collect metrics"""
        start_time = time.time()
        request_id = request_id or f"{model_type.value}_{int(start_time)}"
        
        try:
            # Execute model request
            response = await asyncio.wait_for(
                self.model_client.generate(model_type, prompt),
                timeout=timeout
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Extract metrics from response
            input_tokens = getattr(response, 'input_tokens', len(prompt.split()))
            output_tokens = getattr(response, 'output_tokens', len(str(response).split()))
            cost = getattr(response, 'cost', 0.0)
            quality_score = getattr(response, 'quality_score', 0.8)  # Default
            
            # Create performance metrics
            metrics = ModelPerformanceMetrics(
                model_id=f"benchmark_{model_type.value}",
                model_type=model_type,
                timestamp=datetime.now(),
                execution_time=execution_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                success=True,
                cost=cost,
                quality_score=quality_score,
                request_id=request_id
            )
            
            # Record metrics if not warmup
            if not warmup and self.monitor:
                await self.monitor.record_model_performance(metrics)
            
            return {
                'request_id': request_id,
                'execution_time': execution_time,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost': cost,
                'quality_score': quality_score,
                'success': True,
                'response_length': len(str(response))
            }
            
        except asyncio.TimeoutError:
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Record failed metrics
            if not warmup and self.monitor:
                metrics = ModelPerformanceMetrics(
                    model_id=f"benchmark_{model_type.value}",
                    model_type=model_type,
                    timestamp=datetime.now(),
                    execution_time=execution_time,
                    input_tokens=len(prompt.split()),
                    output_tokens=0,
                    success=False,
                    error_message="Timeout",
                    request_id=request_id
                )
                await self.monitor.record_model_performance(metrics)
            
            return {
                'request_id': request_id,
                'execution_time': execution_time,
                'input_tokens': len(prompt.split()),
                'output_tokens': 0,
                'total_tokens': len(prompt.split()),
                'cost': 0.0,
                'quality_score': 0.0,
                'success': False,
                'error_message': "Timeout"
            }
        
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Record failed metrics
            if not warmup and self.monitor:
                metrics = ModelPerformanceMetrics(
                    model_id=f"benchmark_{model_type.value}",
                    model_type=model_type,
                    timestamp=datetime.now(),
                    execution_time=execution_time,
                    input_tokens=len(prompt.split()),
                    output_tokens=0,
                    success=False,
                    error_message=str(e),
                    request_id=request_id
                )
                await self.monitor.record_model_performance(metrics)
            
            return {
                'request_id': request_id,
                'execution_time': execution_time,
                'input_tokens': len(prompt.split()),
                'output_tokens': 0,
                'total_tokens': len(prompt.split()),
                'cost': 0.0,
                'quality_score': 0.0,
                'success': False,
                'error_message': str(e)
            }
    
    async def _benchmark_concurrency(self,
                                    model_type: ModelType,
                                    prompts: List[str],
                                    concurrency: int) -> Dict[str, Any]:
        """Benchmark model performance under concurrent load"""
        logger.info(f"Testing {model_type.value} with concurrency level {concurrency}")
        
        start_time = time.time()
        tasks = []
        
        # Create concurrent requests
        for i in range(concurrency):
            prompt = prompts[i % len(prompts)]
            task = self._execute_model_request(
                model_type, prompt,
                request_id=f"{model_type.value}_concurrent_{concurrency}_{i}"
            )
            tasks.append(task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get('success')]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get('success')]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        if successful_results:
            execution_times = [r['execution_time'] for r in successful_results]
            total_time = end_time - start_time
            
            return {
                'concurrency_level': concurrency,
                'total_requests': concurrency,
                'successful_requests': len(successful_results),
                'failed_requests': len(failed_results) + len(exceptions),
                'success_rate': len(successful_results) / concurrency,
                'total_execution_time': total_time,
                'avg_execution_time': statistics.mean(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'p95_execution_time': np.percentile(execution_times, 95),
                'requests_per_second': len(successful_results) / total_time,
                'throughput': sum(r['total_tokens'] for r in successful_results) / total_time
            }
        else:
            return {
                'concurrency_level': concurrency,
                'total_requests': concurrency,
                'successful_requests': 0,
                'failed_requests': concurrency,
                'success_rate': 0.0,
                'error': 'All requests failed'
            }
    
    async def _generate_summary(self, 
                               results: Dict[str, Any], 
                               config: BenchmarkConfig) -> Dict[str, Any]:
        """Generate benchmark summary statistics"""
        summary = {
            'benchmark_duration': (datetime.now() - datetime.now()).total_seconds(),  # Will be updated
            'models_tested': list(results.keys()),
            'model_performance': {},
            'rankings': {}
        }
        
        # Calculate performance metrics for each model
        model_scores = {}
        for model_type, model_results in results.items():
            executions = model_results.get('executions', [])
            
            if executions:
                successful_executions = [e for e in executions if e.get('success')]
                
                if successful_executions:
                    execution_times = [e['execution_time'] for e in successful_executions]
                    costs = [e['cost'] for e in successful_executions if e.get('cost')]
                    quality_scores = [e['quality_score'] for e in successful_executions if e.get('quality_score')]
                    
                    model_performance = {
                        'total_requests': len(executions),
                        'successful_requests': len(successful_executions),
                        'success_rate': len(successful_executions) / len(executions),
                        'avg_latency': statistics.mean(execution_times),
                        'min_latency': min(execution_times),
                        'max_latency': max(execution_times),
                        'p95_latency': np.percentile(execution_times, 95),
                        'avg_cost': statistics.mean(costs) if costs else 0.0,
                        'avg_quality_score': statistics.mean(quality_scores) if quality_scores else 0.0,
                        'tokens_per_second': sum(e['total_tokens'] for e in successful_executions) / sum(execution_times)
                    }
                else:
                    model_performance = {
                        'total_requests': len(executions),
                        'successful_requests': 0,
                        'success_rate': 0.0,
                        'error': 'All requests failed'
                    }
                
                summary['model_performance'][model_type] = model_performance
                
                # Calculate overall score (lower is better for latency, higher for quality)
                if successful_executions:
                    latency_score = 1.0 / (model_performance['avg_latency'] + 1)
                    quality_score = model_performance['avg_quality_score']
                    cost_score = 1.0 / (model_performance['avg_cost'] + 0.001)
                    
                    overall_score = (latency_score + quality_score + cost_score) / 3
                    model_scores[model_type] = overall_score
                else:
                    model_scores[model_type] = 0.0
        
        # Rank models by overall performance
        summary['rankings'] = dict(sorted(model_scores.items(), key=lambda x: x[1], reverse=True))
        
        return summary
    
    async def _generate_recommendations(self,
                                       results: Dict[str, Any],
                                       config: BenchmarkConfig) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Analyze performance patterns
        for model_type, model_results in results.items():
            executions = model_results.get('executions', [])
            
            if not executions:
                continue
            
            success_rate = sum(1 for e in executions if e.get('success')) / len(executions)
            
            if success_rate < 0.9:
                recommendations.append(f"{model_type}: Low success rate ({success_rate:.1%}), consider reliability improvements")
            
            # Check concurrency performance
            concurrency_results = model_results.get('concurrency_results', {})
            for concurrency, conc_data in concurrency_results.items():
                if isinstance(conc_data, dict) and conc_data.get('success_rate', 0) < 0.8:
                    recommendations.append(
                        f"{model_type}: Poor performance under concurrency level {concurrency} "
                        f"({conc_data.get('success_rate', 0):.1%} success rate)"
                    )
        
        # General recommendations
        if len(results) > 1:
            best_model = max(results.keys(), 
                           key=lambda m: results[m].get('executions', []))
            recommendations.append(f"Best overall performance: {best_model}")
        
        return recommendations
    
    async def generate_performance_report(self, 
                                        benchmark_result: BenchmarkResult,
                                        output_format: str = 'json') -> str:
        """Generate detailed performance report"""
        if output_format == 'json':
            return json.dumps({
                'benchmark_id': benchmark_result.benchmark_id,
                'config': {
                    'model_types': [m.value for m in benchmark_result.config.model_types],
                    'iterations_per_model': benchmark_result.config.iterations_per_model,
                    'concurrency_levels': benchmark_result.config.concurrency_levels
                },
                'summary': benchmark_result.summary,
                'recommendations': benchmark_result.recommendations,
                'timestamp': benchmark_result.start_time.isoformat()
            }, indent=2)
        
        elif output_format == 'markdown':
            report = f"""
# Performance Benchmark Report

**Benchmark ID:** {benchmark_result.benchmark_id}  
**Date:** {benchmark_result.start_time.strftime('%Y-%m-%d %H:%M:%S')}  
**Duration:** {(benchmark_result.end_time - benchmark_result.start_time).total_seconds():.2f} seconds

## Configuration
- **Models Tested:** {', '.join(m.value for m in benchmark_result.config.model_types)}
- **Iterations per Model:** {benchmark_result.config.iterations_per_model}
- **Concurrency Levels:** {benchmark_result.config.concurrency_levels}

## Summary
"""
            
            # Add performance summary
            rankings = benchmark_result.summary.get('rankings', {})
            if rankings:
                report += "### Model Rankings\n\n"
                for i, (model, score) in enumerate(rankings.items(), 1):
                    report += f"{i}. **{model}** - Score: {score:.3f}\n"
            
            # Add recommendations
            if benchmark_result.recommendations:
                report += "\n## Recommendations\n\n"
                for rec in benchmark_result.recommendations:
                    report += f"- {rec}\n"
            
            return report
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    async def compare_models_over_time(self,
                                     model_types: List[ModelType],
                                     time_window: timedelta = timedelta(days=7)) -> Dict[str, Any]:
        """Compare model performance trends over time"""
        if not self.monitor:
            raise ValueError("Monitor not available for historical comparison")
        
        comparison = {}
        
        for model_type in model_types:
            # Get performance data over time
            performance_data = await self.monitor.get_recent_performance(
                model_type, time_window
            )
            
            if performance_data:
                # Calculate trend metrics
                execution_times = [p.execution_time for p in performance_data if p.success]
                success_rate = sum(1 for p in performance_data if p.success) / len(performance_data)
                
                comparison[model_type.value] = {
                    'total_requests': len(performance_data),
                    'success_rate': success_rate,
                    'avg_latency': statistics.mean(execution_times) if execution_times else 0,
                    'trend': self._calculate_trend(execution_times) if execution_times else 'stable',
                    'performance_data_count': len(performance_data)
                }
        
        return comparison
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg < first_avg * 0.9:
            return 'improving'
        elif second_avg > first_avg * 1.1:
            return 'degrading'
        else:
            return 'stable'
    
    async def load_test(self,
                       model_type: ModelType,
                       duration_seconds: int = 60,
                       max_concurrency: int = 10,
                       prompt: str = "Hello, world!") -> Dict[str, Any]:
        """Run a load test on a specific model"""
        logger.info(f"Starting load test for {model_type.value} - {duration_seconds}s duration")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        results = {
            'model_type': model_type.value,
            'duration_seconds': duration_seconds,
            'max_concurrency': max_concurrency,
            'requests_completed': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'execution_times': [],
            'throughput_data': []
        }
        
        async def worker():
            """Worker function for concurrent requests"""
            while time.time() < end_time:
                try:
                    result = await self._execute_model_request(
                        model_type, prompt,
                        request_id=f"load_test_{int(time.time())}_{results['requests_completed']}",
                        timeout=30.0
                    )
                    
                    results['requests_completed'] += 1
                    
                    if result.get('success'):
                        results['successful_requests'] += 1
                        results['execution_times'].append(result['execution_time'])
                    else:
                        results['failed_requests'] += 1
                    
                    # Calculate throughput
                    elapsed = time.time() - start_time
                    throughput = results['successful_requests'] / elapsed if elapsed > 0 else 0
                    results['throughput_data'].append({
                        'timestamp': elapsed,
                        'throughput': throughput,
                        'total_requests': results['requests_completed']
                    })
                    
                except Exception as e:
                    logger.error(f"Load test error: {e}")
                    results['failed_requests'] += 1
                    results['requests_completed'] += 1
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
        
        # Start concurrent workers
        workers = [worker() for _ in range(max_concurrency)]
        await asyncio.gather(*workers)
        
        # Calculate final statistics
        if results['execution_times']:
            results['avg_latency'] = statistics.mean(results['execution_times'])
            results['min_latency'] = min(results['execution_times'])
            results['max_latency'] = max(results['execution_times'])
            results['p95_latency'] = np.percentile(results['execution_times'], 95)
        
        results['total_throughput'] = results['successful_requests'] / duration_seconds
        results['success_rate'] = results['successful_requests'] / results['requests_completed'] if results['requests_completed'] > 0 else 0
        
        logger.info(f"Load test completed: {results['successful_requests']}/{results['requests_completed']} successful")
        return results