"""
Performance Monitoring and Optimization Package

This package provides comprehensive performance monitoring, optimization, 
and resource management for hybrid model systems.

Features:
- Real-time performance monitoring for model selection decisions
- Intelligent model routing with optimization algorithms
- Performance benchmarking and analysis tools
- Automated performance tuning and threshold adjustment
- Resource usage monitoring and optimization

Quick Start:
    from performance_monitoring import (
        RedisPerformanceMonitor,
        ModelRouter, 
        PerformanceBenchmark,
        AutomatedTuner,
        ResourceMonitor
    )
    
    # Initialize components
    monitor = RedisPerformanceMonitor()
    router = ModelRouter()
    tuner = AutomatedTuner(monitor)
    resource_monitor = ResourceMonitor()
    
    # Start monitoring
    await monitor.initialize()
    await resource_monitor.start_monitoring()
"""

from .types import (
    ModelType,
    PerformanceMetric,
    ModelPerformanceMetrics,
    SystemResourceMetrics,
    PerformanceThreshold,
    OptimizationDecision
)

from .monitor import RedisPerformanceMonitor
from .storage import MetricsStorage
from .router import ModelRouter, OptimizationStrategy, ModelCapabilities
from .benchmark import PerformanceBenchmark, BenchmarkConfig, BenchmarkResult
from .tuning import AutomatedTuner, TuningConfiguration, TuningRecommendation
from .resource_monitor import (
    ResourceMonitor, 
    ResourceType, 
    AlertLevel,
    ScalingDecision
)

__version__ = "1.0.0"
__author__ = "Kyros Team"

__all__ = [
    # Types
    'ModelType',
    'PerformanceMetric', 
    'ModelPerformanceMetrics',
    'SystemResourceMetrics',
    'PerformanceThreshold',
    'OptimizationDecision',
    
    # Core Components
    'RedisPerformanceMonitor',
    'MetricsStorage',
    'ModelRouter',
    'PerformanceBenchmark',
    'AutomatedTuner',
    'ResourceMonitor',
    
    # Configuration Classes
    'OptimizationStrategy',
    'ModelCapabilities',
    'BenchmarkConfig',
    'BenchmarkResult',
    'TuningConfiguration',
    'TuningRecommendation',
    'ResourceType',
    'AlertLevel',
    'ScalingDecision'
]