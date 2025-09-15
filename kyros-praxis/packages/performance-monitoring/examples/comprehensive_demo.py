#!/usr/bin/env python3
"""
Example usage of the Performance Monitoring and Optimization System

This script demonstrates how to use the comprehensive performance monitoring
and optimization system for hybrid model architectures.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

# Import the performance monitoring components
from performance_monitoring import (
    RedisPerformanceMonitor,
    ModelRouter,
    PerformanceBenchmark,
    AutomatedTuner,
    ResourceMonitor,
    MetricsStorage,
    ModelType,
    OptimizationStrategy,
    BenchmarkConfig,
    TuningConfiguration,
    ModelPerformanceMetrics,
    SystemResourceMetrics
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockModelClient:
    """Mock model client for demonstration purposes"""
    
    def __init__(self):
        self.model_responses = {
            ModelType.GPT_4: {
                "latency_range": (2.0, 8.0),
                "quality_range": (0.8, 0.95),
                "cost_range": (0.02, 0.04)
            },
            ModelType.GPT_3_5: {
                "latency_range": (0.5, 3.0),
                "quality_range": (0.6, 0.8),
                "cost_range": (0.001, 0.002)
            },
            ModelType.CLAUDE: {
                "latency_range": (1.0, 5.0),
                "quality_range": (0.75, 0.9),
                "cost_range": (0.01, 0.02)
            },
            ModelType.GEMINI: {
                "latency_range": (0.8, 4.0),
                "quality_range": (0.7, 0.85),
                "cost_range": (0.0008, 0.0015)
            },
            ModelType.LOCAL_LLAMA: {
                "latency_range": (3.0, 15.0),
                "quality_range": (0.4, 0.7),
                "cost_range": (0.0, 0.0)
            }
        }
    
    async def generate(self, model_type: ModelType, prompt: str) -> Dict[str, Any]:
        """Generate mock response from model"""
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        model_config = self.model_responses[model_type]
        
        # Generate realistic response metrics
        execution_time = random.uniform(*model_config["latency_range"])
        quality_score = random.uniform(*model_config["quality_range"])
        cost = random.uniform(*model_config["cost_range"])
        
        input_tokens = len(prompt.split())
        output_tokens = int(input_tokens * random.uniform(1.5, 3.0))
        
        return {
            "content": f"Mock response from {model_type.value} for prompt: {prompt[:50]}...",
            "execution_time": execution_time,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "quality_score": quality_score,
            "cost": cost
        }


class PerformanceMonitoringExample:
    """Example demonstrating the complete performance monitoring system"""
    
    def __init__(self):
        self.model_client = MockModelClient()
        self.monitor = None
        self.router = None
        self.benchmark = None
        self.tuner = None
        self.resource_monitor = None
        self.storage = None
    
    async def initialize(self):
        """Initialize all monitoring components"""
        logger.info("Initializing Performance Monitoring System...")
        
        # Initialize storage
        self.storage = MetricsStorage("example_metrics.db")
        await self.storage.initialize()
        
        # Initialize performance monitor
        self.monitor = RedisPerformanceMonitor(
            redis_url="redis://localhost:6379",
            storage=self.storage
        )
        await self.monitor.initialize()
        
        # Initialize model router
        self.router = ModelRouter()
        
        # Initialize benchmark tool
        self.benchmark = PerformanceBenchmark(
            model_client=self.model_client,
            monitor=self.monitor,
            storage=self.storage
        )
        
        # Initialize automated tuner
        tuning_config = TuningConfiguration(
            enabled=True,
            tuning_interval_minutes=5,
            confidence_threshold=0.7,
            impact_threshold=0.1
        )
        self.tuner = AutomatedTuner(
            monitor=self.monitor,
            config=tuning_config
        )
        
        # Initialize resource monitor
        self.resource_monitor = ResourceMonitor(
            monitor_interval_seconds=10,
            alert_thresholds={
                'cpu': {'warning': 60, 'critical': 80, 'emergency': 90},
                'memory': {'warning': 70, 'critical': 85, 'emergency': 95}
            }
        )
        
        logger.info("Performance Monitoring System initialized successfully")
    
    async def demonstrate_real_time_monitoring(self):
        """Demonstrate real-time performance monitoring"""
        logger.info("\n=== Real-time Performance Monitoring Demo ===")
        
        test_prompts = [
            "Explain quantum computing in simple terms",
            "Write a Python function to calculate Fibonacci numbers",
            "What are the benefits of renewable energy?",
            "Create a SQL query to find duplicates in a table",
            "Summarize the key points of machine learning"
        ]
        
        # Simulate model requests with monitoring
        for i, prompt in enumerate(test_prompts):
            model_type = random.choice(list(ModelType))
            
            logger.info(f"Processing request {i+1} with {model_type.value}")
            
            # Generate model response
            start_time = time.time()
            response = await self.model_client.generate(model_type, prompt)
            execution_time = time.time() - start_time
            
            # Create and record performance metrics
            metrics = ModelPerformanceMetrics(
                model_id=f"demo_{model_type.value}",
                model_type=model_type,
                timestamp=datetime.now(),
                execution_time=response["execution_time"],
                input_tokens=response["input_tokens"],
                output_tokens=response["output_tokens"],
                success=True,
                cost=response["cost"],
                quality_score=response["quality_score"],
                request_id=f"req_{i}_{int(time.time())}"
            )
            
            await self.monitor.record_model_performance(metrics)
            
            # Get real-time metrics
            real_time_metrics = await self.monitor.get_real_time_metrics(model_type)
            logger.info(f"Real-time metrics for {model_type.value}: "
                       f"Avg latency: {real_time_metrics['last_hour'].get('avg_latency', 0):.2f}s, "
                       f"Success rate: {real_time_metrics['last_hour'].get('success_rate', 0):.1%}")
            
            await asyncio.sleep(1)  # Small delay between requests
    
    async def demonstrate_model_routing(self):
        """Demonstrate intelligent model routing"""
        logger.info("\n=== Model Routing Optimization Demo ===")
        
        # Test different request scenarios
        test_scenarios = [
            {
                "name": "Simple Query",
                "features": {
                    "estimated_tokens": 100,
                    "creativity_requirement": 0.3,
                    "reasoning_requirement": 0.4,
                    "requires_code": False,
                    "requires_vision": False
                }
            },
            {
                "name": "Complex Code Generation",
                "features": {
                    "estimated_tokens": 500,
                    "creativity_requirement": 0.5,
                    "reasoning_requirement": 0.9,
                    "requires_code": True,
                    "requires_vision": False
                }
            },
            {
                "name": "Creative Writing",
                "features": {
                    "estimated_tokens": 300,
                    "creativity_requirement": 0.9,
                    "reasoning_requirement": 0.6,
                    "requires_code": False,
                    "requires_vision": False
                }
            },
            {
                "name": "Image Analysis",
                "features": {
                    "estimated_tokens": 200,
                    "creativity_requirement": 0.4,
                    "reasoning_requirement": 0.7,
                    "requires_code": False,
                    "requires_vision": True
                }
            }
        ]
        
        available_models = list(ModelType)
        
        for scenario in test_scenarios:
            logger.info(f"\nTesting scenario: {scenario['name']}")
            
            # Get model routing decision
            decision = await self.router.select_model(
                request_features=scenario["features"],
                available_models=available_models,
                strategy=OptimizationStrategy.ADAPTIVE
            )
            
            logger.info(f"Selected model: {decision.selected_model.value}")
            logger.info(f"Confidence: {decision.confidence_score:.2f}")
            logger.info(f"Reasoning: {decision.reasoning}")
            
            # Get model recommendations
            recommendations = self.router.get_model_recommendations(
                request_features=scenario["features"],
                available_models=available_models,
                top_n=3
            )
            
            logger.info("Top recommendations:")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"  {i}. {rec.selected_model.value} "
                          f"(confidence: {rec.confidence_score:.2f})")
    
    async def demonstrate_benchmarking(self):
        """Demonstrate performance benchmarking"""
        logger.info("\n=== Performance Benchmarking Demo ===")
        
        # Configure benchmark
        config = BenchmarkConfig(
            model_types=[ModelType.GPT_4, ModelType.GPT_3_5, ModelType.CLAUDE],
            test_prompts=[
                "What is artificial intelligence?",
                "Explain the benefits of cloud computing",
                "Write a function to sort an array",
                "Describe the water cycle"
            ],
            iterations_per_model=3,
            concurrency_levels=[1, 2],
            metrics_to_collect=["latency", "quality", "cost", "throughput"],
            warmup_iterations=1
        )
        
        logger.info("Running comparative benchmark...")
        benchmark_result = await self.benchmark.run_comparative_benchmark(config)
        
        # Generate and display report
        report = await self.benchmark.generate_performance_report(
            benchmark_result, 
            output_format='markdown'
        )
        
        logger.info("\nBenchmark Summary:")
        logger.info(f"Duration: {benchmark_result.end_time - benchmark_result.start_time}")
        
        rankings = benchmark_result.summary.get('rankings', {})
        if rankings:
            logger.info("Model Rankings:")
            for i, (model, score) in enumerate(rankings.items(), 1):
                logger.info(f"  {i}. {model}: {score:.3f}")
        
        if benchmark_result.recommendations:
            logger.info("\nRecommendations:")
            for rec in benchmark_result.recommendations:
                logger.info(f"  - {rec}")
    
    async def demonstrate_automated_tuning(self):
        """Demonstrate automated performance tuning"""
        logger.info("\n=== Automated Performance Tuning Demo ===")
        
        # Simulate some performance data to trigger tuning
        await self._simulate_performance_data()
        
        # Run tuning cycle
        logger.info("Running automated tuning cycle...")
        recommendations = await self.tuner.run_tuning_cycle()
        
        if recommendations:
            logger.info(f"Found {len(recommendations)} tuning recommendations:")
            for rec in recommendations:
                logger.info(f"\nRecommendation: {rec.action.value}")
                logger.info(f"  Target: {rec.target}")
                logger.info(f"  Current: {rec.current_value}")
                logger.info(f"  Recommended: {rec.recommended_value}")
                logger.info(f"  Confidence: {rec.confidence:.2f}")
                logger.info(f"  Reasoning: {rec.reasoning}")
        else:
            logger.info("No tuning recommendations at this time")
        
        # Show tuning status
        status = await self.tuner.get_tuning_status()
        logger.info(f"\nTuning Status: {status['enabled']}")
        logger.info(f"Active tunings: {status['active_tunings']}")
    
    async def demonstrate_resource_monitoring(self):
        """Demonstrate resource monitoring"""
        logger.info("\n=== Resource Monitoring Demo ===")
        
        # Start resource monitoring
        await self.resource_monitor.start_monitoring()
        
        # Set up alert callback
        def on_alert(alert):
            logger.info(f"🚨 ALERT: {alert.alert_level.value} - {alert.message}")
        
        self.resource_monitor.add_callback('on_alert', on_alert)
        
        # Monitor for 30 seconds
        logger.info("Monitoring system resources for 30 seconds...")
        await asyncio.sleep(30)
        
        # Get resource summary
        summary = await self.resource_monitor.get_resource_summary(time_window_minutes=1)
        logger.info("\nResource Summary (last 1 minute):")
        logger.info(f"  CPU: {summary['cpu']['current']:.1f}% (avg: {summary['cpu']['average']:.1f}%)")
        logger.info(f"  Memory: {summary['memory']['current']:.1f}% (avg: {summary['memory']['average']:.1f}%)")
        logger.info(f"  Disk: {summary['disk']['current']:.1f}%")
        logger.info(f"  Queue: {summary['queue']['current']:.0f} (avg: {summary['queue']['average']:.1f})")
        
        # Get alerts
        alerts = await self.resource_monitor.get_alerts(resolved=False)
        if alerts:
            logger.info(f"\nActive alerts: {len(alerts)}")
        
        # Get optimization recommendations
        recommendations = await self.resource_monitor.get_optimization_recommendations()
        if recommendations:
            logger.info("\nOptimization Recommendations:")
            for rec in recommendations:
                logger.info(f"  - {rec['category']}: {rec['recommendation']}")
        
        # Stop monitoring
        self.resource_monitor.stop_monitoring()
    
    async def _simulate_performance_data(self):
        """Simulate performance data for tuning demonstration"""
        logger.info("Simulating performance data...")
        
        # Create some performance metrics with varying characteristics
        for i in range(20):
            model_type = random.choice(list(ModelType))
            
            # Simulate some performance issues for certain models
            if model_type == ModelType.LOCAL_LLAMA:
                execution_time = random.uniform(8.0, 20.0)  # Poor performance
                quality_score = random.uniform(0.3, 0.6)
            elif model_type == ModelType.GPT_4:
                execution_time = random.uniform(3.0, 12.0)  # Variable performance
                quality_score = random.uniform(0.85, 0.95)
            else:
                execution_time = random.uniform(1.0, 5.0)
                quality_score = random.uniform(0.6, 0.85)
            
            metrics = ModelPerformanceMetrics(
                model_id=f"sim_{model_type.value}",
                model_type=model_type,
                timestamp=datetime.now(),
                execution_time=execution_time,
                input_tokens=random.randint(50, 200),
                output_tokens=random.randint(100, 400),
                success=random.random() > 0.1,  # 10% failure rate
                cost=random.uniform(0.001, 0.03),
                quality_score=quality_score,
                request_id=f"sim_{i}_{int(time.time())}"
            )
            
            await self.monitor.record_model_performance(metrics)
            await asyncio.sleep(0.1)
    
    async def demonstrate_comprehensive_analysis(self):
        """Demonstrate comprehensive performance analysis"""
        logger.info("\n=== Comprehensive Performance Analysis Demo ===")
        
        # Generate comprehensive performance report
        logger.info("Generating comprehensive performance analysis...")
        
        # Get performance comparison across all models
        comparison_data = {}
        for model_type in ModelType:
            summary = await self.monitor.get_performance_summary(
                model_type, 
                timedelta(minutes=10)
            )
            if summary:
                comparison_data[model_type.value] = summary
        
        logger.info("\nModel Performance Comparison:")
        for model, data in comparison_data.items():
            if data.get('total_requests', 0) > 0:
                logger.info(f"\n{model}:")
                logger.info(f"  Requests: {data['total_requests']}")
                logger.info(f"  Success Rate: {data.get('success_rate', 0):.1%}")
                logger.info(f"  Avg Latency: {data.get('avg_latency', 0):.2f}s")
                logger.info(f"  P95 Latency: {data.get('p95_latency', 0):.2f}s")
                logger.info(f"  Avg Quality: {data.get('avg_quality_score', 0):.2f}")
                logger.info(f"  Avg Cost: ${data.get('avg_cost', 0):.4f}")
        
        # Export current configuration
        config_export = await self.tuner.export_configuration()
        logger.info(f"\nConfiguration exported with {len(config_export)} settings")
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("\nCleaning up resources...")
        
        if self.resource_monitor:
            self.resource_monitor.stop_monitoring()
        
        if self.monitor:
            await self.monitor.close()
        
        logger.info("Cleanup completed")


async def main():
    """Main demonstration function"""
    example = PerformanceMonitoringExample()
    
    try:
        # Initialize the system
        await example.initialize()
        
        # Run demonstrations
        await example.demonstrate_real_time_monitoring()
        await example.demonstrate_model_routing()
        await example.demonstrate_benchmarking()
        await example.demonstrate_automated_tuning()
        await example.demonstrate_resource_monitoring()
        await example.demonstrate_comprehensive_analysis()
        
        logger.info("\n✅ All demonstrations completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await example.cleanup()


if __name__ == "__main__":
    asyncio.run(main())