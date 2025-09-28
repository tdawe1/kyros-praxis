# Performance Monitoring and Optimization System

A comprehensive, real-time performance monitoring and optimization system for hybrid model architectures. This system provides intelligent model routing, automated performance tuning, resource monitoring, and benchmarking capabilities.

## Features

### 🎯 Real-time Performance Monitoring
- **Model Performance Tracking**: Monitor latency, throughput, error rates, costs, and quality scores
- **System Resource Monitoring**: Track CPU, memory, disk, network usage, and queue sizes
- **Redis-backed Storage**: High-performance metrics storage with TTL support
- **SQLite Persistence**: Long-term metrics storage for historical analysis

### 🧠 Intelligent Model Routing
- **Multi-strategy Optimization**: Choose from latency-focused, quality-focused, cost-effective, balanced, or adaptive strategies
- **Capability-based Selection**: Models selected based on task requirements (vision, code, creativity, reasoning)
- **Real-time Decision Making**: Adaptive routing based on current performance data
- **Confidence Scoring**: Quantified confidence in routing decisions

### 📊 Performance Benchmarking
- **Comparative Analysis**: Benchmark multiple models with identical test scenarios
- **Concurrency Testing**: Test performance under concurrent load
- **Load Testing**: Generate sustained load to test system limits
- **Trend Analysis**: Compare performance over time
- **Export Options**: JSON, CSV, and Markdown report formats

### ⚡ Automated Performance Tuning
- **Threshold Adjustment**: Automatically adjust alert thresholds based on observed patterns
- **Routing Optimization**: Continuously optimize model selection weights
- **Pattern Recognition**: Detect and respond to performance degradation patterns
- **Recommendation Engine**: Generate actionable optimization recommendations

### 🖥️ Resource Monitoring
- **Real-time Alerts**: Multi-level alerting (info, warning, critical, emergency)
- **Pattern Detection**: Identify spikes, gradual increases, and cyclical patterns
- **Scaling Recommendations**: Intelligent scaling decisions based on resource usage
- **Customizable Thresholds**: Flexible alert threshold configuration

## Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/kyros-ai/performance-monitoring.git
cd performance-monitoring
pip install -e .

# Install with optional dependencies
pip install -e ".[gpu,monitoring]"

# Install development dependencies
pip install -e ".[dev]"
```

### Basic Usage

```python
import asyncio
from performance_monitoring import (
    RedisPerformanceMonitor,
    ModelRouter,
    AutomatedTuner,
    ResourceMonitor
)

async def main():
    # Initialize monitoring components
    monitor = RedisPerformanceMonitor(redis_url="redis://localhost:6379")
    await monitor.initialize()
    
    router = ModelRouter()
    tuner = AutomatedTuner(monitor=monitor)
    resource_monitor = ResourceMonitor()
    
    # Start resource monitoring
    await resource_monitor.start_monitoring()
    
    # Example model request with optimization
    request_features = {
        "estimated_tokens": 150,
        "creativity_requirement": 0.8,
        "reasoning_requirement": 0.7,
        "requires_code": True,
        "requires_vision": False
    }
    
    decision = await router.select_model(
        request_features=request_features,
        available_models=["gpt-4", "claude", "gemini-pro"],
        strategy="adaptive"
    )
    
    print(f"Selected model: {decision.selected_model}")
    print(f"Confidence: {decision.confidence_score}")
    print(f"Reasoning: {decision.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Core Components

### 1. Performance Monitor

```python
from performance_monitoring import RedisPerformanceMonitor, ModelPerformanceMetrics

# Initialize monitor
monitor = RedisPerformanceMonitor(redis_url="redis://localhost:6379")
await monitor.initialize()

# Record performance metrics
metrics = ModelPerformanceMetrics(
    model_id="gpt-4-instance-1",
    model_type=ModelType.GPT_4,
    timestamp=datetime.now(),
    execution_time=2.5,
    input_tokens=100,
    output_tokens=200,
    success=True,
    cost=0.03,
    quality_score=0.9,
    request_id="req_12345"
)

await monitor.record_model_performance(metrics)

# Get performance summary
summary = await monitor.get_performance_summary(
    ModelType.GPT_4, 
    timedelta(hours=24)
)
```

### 2. Model Router

```python
from performance_monitoring import ModelRouter, OptimizationStrategy

router = ModelRouter()

# Get model recommendations
recommendations = router.get_model_recommendations(
    request_features={
        "estimated_tokens": 300,
        "creativity_requirement": 0.9,
        "reasoning_requirement": 0.8,
        "requires_code": False,
        "requires_vision": True
    },
    available_models=list(ModelType),
    top_n=3
)

for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec.selected_model} (confidence: {rec.confidence_score:.2f})")
```

### 3. Performance Benchmarking

```python
from performance_monitoring import PerformanceBenchmark, BenchmarkConfig

# Configure benchmark
config = BenchmarkConfig(
    model_types=[ModelType.GPT_4, ModelType.CLAUDE, ModelType.GEMINI],
    test_prompts=[
        "What is artificial intelligence?",
        "Write a Python function to sort an array",
        "Explain quantum computing"
    ],
    iterations_per_model=10,
    concurrency_levels=[1, 2, 4],
    metrics_to_collect=["latency", "quality", "cost", "throughput"]
)

# Run benchmark
benchmark = PerformanceBenchmark(model_client, monitor)
result = await benchmark.run_comparative_benchmark(config)

# Generate report
report = await benchmark.generate_performance_report(result, format='markdown')
```

### 4. Automated Tuning

```python
from performance_monitoring import AutomatedTuner, TuningConfiguration

# Configure tuner
config = TuningConfiguration(
    enabled=True,
    tuning_interval_minutes=30,
    confidence_threshold=0.7,
    impact_threshold=0.1
)

tuner = AutomatedTuner(monitor=monitor, config=config)

# Run tuning cycle
recommendations = await tuner.run_tuning_cycle()

for rec in recommendations:
    print(f"Action: {rec.action}")
    print(f"Target: {rec.target}")
    print(f"Current: {rec.current_value}")
    print(f"Recommended: {rec.recommended_value}")
```

### 5. Resource Monitoring

```python
from performance_monitoring import ResourceMonitor

# Initialize resource monitor
resource_monitor = ResourceMonitor(
    monitor_interval_seconds=5,
    alert_thresholds={
        'cpu': {'warning': 70, 'critical': 85, 'emergency': 95},
        'memory': {'warning': 75, 'critical': 90, 'emergency': 95}
    }
)

# Start monitoring
await resource_monitor.start_monitoring()

# Set up alert callback
def on_alert(alert):
    print(f"🚨 {alert.alert_level.upper()}: {alert.message}")

resource_monitor.add_callback('on_alert', on_alert)

# Get resource summary
summary = await resource_monitor.get_resource_summary(time_window_minutes=60)
```

## Configuration

### Redis Configuration

```python
monitor = RedisPerformanceMonitor(
    redis_url="redis://localhost:6379",
    storage=MetricsStorage("metrics.db")
)
```

### Tuning Configuration

```python
config = TuningConfiguration(
    enabled=True,
    tuning_interval_minutes=15,        # How often to run tuning
    confidence_threshold=0.8,          # Minimum confidence for auto-adjustments
    impact_threshold=0.15,             # Minimum expected improvement
    max_concurrent_tunings=2,          # Maximum simultaneous adjustments
    learning_rate=0.1,                 # How aggressively to adjust
    safety_margin=0.2                  # Conservative adjustment buffer
)
```

### Resource Monitor Configuration

```python
resource_monitor = ResourceMonitor(
    monitor_interval_seconds=10,
    alert_thresholds={
        'cpu': {'warning': 60, 'critical': 80, 'emergency': 90},
        'memory': {'warning': 70, 'critical': 85, 'emergency': 95},
        'disk': {'warning': 80, 'critical': 90, 'emergency': 95},
        'network': {'warning': 80, 'critical': 90, 'emergency': 95}
    },
    enable_gpu_monitoring=True
)
```

## Optimization Strategies

### Lowest Latency
- **Goal**: Minimize response time
- **Weights**: Latency (70%), Quality (20%), Cost (10%)
- **Best for**: Real-time applications, chatbots

### Highest Quality
- **Goal**: Maximize response quality
- **Weights**: Latency (10%), Quality (80%), Cost (10%)
- **Best for**: Creative writing, complex reasoning

### Cost Effective
- **Goal**: Minimize operational costs
- **Weights**: Latency (20%), Quality (30%), Cost (50%)
- **Best for**: High-volume, cost-sensitive applications

### Balanced
- **Goal**: Equal consideration of all factors
- **Weights**: Latency (33%), Quality (33%), Cost (34%)
- **Best for**: General-purpose applications

### Adaptive
- **Goal**: Dynamic optimization based on context
- **Weights**: Context-aware balancing
- **Best for**: Variable workloads

## API Endpoints (FastAPI Integration)

The system includes a complete FastAPI integration with the following endpoints:

### Model Generation
```
POST /v1/models/generate
```
Generate responses with automatic model selection and performance monitoring.

### Performance Monitoring
```
GET /v1/performance/models/{model_type}
GET /v1/performance/summary
```
Retrieve performance metrics and summaries.

### Benchmarking
```
POST /v1/benchmark/run
```
Run comparative performance benchmarks.

### Automated Tuning
```
GET /v1/tuning/status
POST /v1/tuning/run
```
Manage automated performance tuning.

### Resource Monitoring
```
GET /v1/resources/summary
GET /v1/resources/alerts
```
Monitor system resources and alerts.

### Model Recommendations
```
GET /v1/models/recommendations
```
Get model recommendations for specific prompts.

## Model Types Supported

- **GPT-4**: High quality, supports vision and code
- **GPT-3.5**: Fast and cost-effective
- **Claude**: Balanced performance with strong reasoning
- **Gemini**: Fast with good quality
- **Local Llama**: Zero cost, lower quality

## Performance Metrics Tracked

### Model Metrics
- **Execution Time**: Request processing time
- **Input/Output Tokens**: Token usage
- **Success Rate**: Request success percentage
- **Quality Score**: Response quality (0.0-1.0)
- **Cost**: Operational cost per request
- **Error Rate**: Failure percentage

### System Metrics
- **CPU Usage**: Processor utilization
- **Memory Usage**: RAM utilization
- **Disk Usage**: Storage utilization
- **Network I/O**: Network traffic
- **Active Connections**: Concurrent connections
- **Queue Size**: Request queue length

## Examples

See the `examples/` directory for comprehensive demonstrations:

- `comprehensive_demo.py`: Complete system demonstration
- `fastapi_integration.py`: FastAPI web service integration

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=performance_monitoring --cov-report=html

# Run specific test categories
pytest -m "unit"
pytest -m "integration"
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/kyros-ai/performance-monitoring.git
cd performance-monitoring

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Architecture

```
performance_monitoring/
├── src/
│   └── performance_monitoring/
│       ├── __init__.py           # Main package exports
│       ├── types.py             # Core data types and enums
│       ├── monitor.py           # Real-time performance monitoring
│       ├── storage.py           # Metrics persistence
│       ├── router.py            # Intelligent model routing
│       ├── benchmark.py         # Performance benchmarking
│       ├── tuning.py            # Automated performance tuning
│       └── resource_monitor.py  # System resource monitoring
├── examples/
│   ├── comprehensive_demo.py    # Complete system demo
│   └── fastapi_integration.py   # Web service integration
├── tests/                       # Test suite
└── README.md                    # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For questions and support:
- Create an issue on GitHub
- Check the documentation
- Review the examples

## Roadmap

- [ ] Grafana dashboard integration
- [ ] Machine learning-based anomaly detection
- [ ] Multi-region performance monitoring
- [ ] Advanced pattern recognition
- [ ] Kubernetes integration
- [ ] Real-time performance optimization