# Hybrid Model Escalation Workflows - Testing Framework

This comprehensive testing framework validates the escalation workflows for the hybrid model system, ensuring that GLM-4.5 and Claude 4.1 Opus are selected appropriately based on defined triggers and criteria.

## 🎯 Overview

The testing framework provides:

1. **Escalation Scenario Tests** - Validates trigger conditions and model selection logic
2. **Workflow Validation Scripts** - Comprehensive validation of configuration and integration
3. **Integration Tests** - End-to-end testing of escalation workflows
4. **Performance Benchmarking** - Performance analysis and optimization insights
5. **Comprehensive Test Runner** - Unified execution and reporting

## 📋 Test Coverage

### 1. Escalation Triggers Tested

#### Architect Role (Escalates to Claude 4.1 Opus when:):
- ✅ Decision affects 3+ services
- ✅ Major security implications (critical/high risk)
- ✅ Performance-critical infrastructure design
- ✅ Complex system boundary changes
- ✅ High-risk/high-reward architectural choices

#### Integrator Role (Escalates to Claude 4.1 Opus when:):
- ✅ Complex multi-service conflict resolution
- ✅ System boundary changes during merge
- ✅ Complex dependency relationship issues

#### Non-Escalating Roles (Always use GLM-4.5):
- ✅ Orchestrator - No escalation needed
- ✅ Implementer - No escalation needed  
- ✅ Critic - No escalation needed

### 2. Validation Categories

- **Configuration Validation** - YAML/JSON config files and escalation rules
- **Trigger Logic** - Escalation criteria evaluation accuracy
- **Model Selection** - Correct model assignment based on role and context
- **Cost Tracking** - Monitoring script functionality and cost analysis
- **Performance Metrics** - Response times, throughput, and resource usage
- **Integration Testing** - End-to-end workflow validation

### 3. Performance Benchmarks

- **Load Testing** - Concurrent request handling (5, 20, 50, 100 concurrent)
- **Response Time Analysis** - P50, P95, P99 latency measurements
- **Cost Efficiency** - Hybrid vs. premium-only cost comparison
- **Accuracy Validation** - Decision accuracy and confidence scoring
- **Resource Usage** - Memory and CPU utilization monitoring

## 🚀 Quick Start

### Run All Tests

```bash
# Run comprehensive test suite
python scripts/run_escalation_tests.py

# Run with custom output directory
python scripts/run_escalation_tests.py --output-dir test_results

# Run specific phase only
python scripts/run_escalation_tests.py --phase scenarios
python scripts/run_escalation_tests.py --phase validation
python scripts/run_escalation_tests.py --phase integration
python scripts/run_escalation_tests.py --phase performance
```

### Individual Test Components

#### 1. Escalation Scenarios
```bash
# Run scenario tests
python tests/test_escalation_scenarios.py

# Export test scenarios
python -c "from test_escalation_scenarios import EscalationTestScenarios; EscalationTestScenarios().export_scenarios(Path('scenarios.json'))"
```

#### 2. Workflow Validation
```bash
# Run comprehensive validation
python scripts/validate_escalation_workflows.py

# View validation report
cat validation_report.json
```

#### 3. Integration Tests
```bash
# Run integration tests
python tests/test_escalation_integration.py

# Run async integration tests
python -m pytest tests/test_escalation_integration.py -v
```

#### 4. Performance Benchmarks
```bash
# Run performance benchmarks
python scripts/benchmark_escalation_performance.py

# Run specific load level
python scripts/benchmark_escalation_performance.py light_load
python scripts/benchmark_escalation_performance.py medium_load
```

## 📊 Test Results and Reports

### Output Structure

```
test_results/
├── comprehensive_test_report.json     # Main test summary
├── validation_report.json             # Workflow validation results
├── integration_test_report.json       # Integration test results
├── benchmark_comparison_report.json   # Performance comparison
├── performance_comparison.png         # Performance visualizations
├── test_scenarios_export.json         # Exported test scenarios
└── benchmark_*/                       # Individual benchmark results
    ├── benchmark_light_load_*.json
    ├── benchmark_medium_load_*.json
    └── performance_comparison.png
```

### Key Metrics Tracked

- **Success Rate**: Percentage of tests passing (target: >99%)
- **Decision Accuracy**: Escalation decision correctness (target: >95%)
- **Response Time**: Average decision time (target: <1s)
- **Cost Efficiency**: Savings vs premium-only approach (target: >35%)
- **Throughput**: Requests per second under load
- **Model Distribution**: GLM-4.5 vs Claude 4.1 Opus usage ratio

### Report Structure

```json
{
  "test_run_timestamp": "2025-09-13T10:00:00",
  "total_execution_time": 45.2,
  "overall_success": true,
  "test_results": {
    "scenarios": {...},
    "validation": {...},
    "integration": {...},
    "performance": {...}
  },
  "summary": {
    "total_tests": 150,
    "passed_tests": 148,
    "failed_tests": 2,
    "warning_tests": 0
  },
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2"
  ]
}
```

## 🔧 Configuration

### Test Configuration

The framework uses configuration files from the hybrid model system:

- `.claude/custom_modes.yml` - Role configurations and escalation rules
- `.claude/model-config.json` - Global model selection strategy
- `modes.yml` - Mode definitions and model assignments

### Custom Test Scenarios

Add new test scenarios by extending the `EscalationTestScenarios` class:

```python
# Add to test_escalation_scenarios.py
def _load_custom_scenarios(self):
    scenario = TestScenario(
        name="custom_security_audit",
        description="Custom security audit scenario",
        role=Role.ARCHITECT,
        triggers=[
            EscalationTrigger(
                role=Role.ARCHITECT,
                trigger_description="Custom security trigger",
                should_escalate=True,
                expected_model=EscalationModel.CLAUDE_41_OPUS,
                task_context={
                    "custom_security_criteria": True,
                    "risk_level": "critical"
                }
            )
        ],
        setup_actions=[...],
        validation_checks=[...]
    )
    self.test_scenarios.append(scenario)
```

## 🎯 Acceptance Criteria

### Must Pass (Critical):

1. **Escalation Accuracy**: 100% correct model selection for defined triggers
2. **Configuration Validation**: All YAML/JSON configs valid and consistent
3. **Integration Success**: End-to-end workflows complete without errors
4. **Cost Tracking**: Monitoring script functional and accurate

### Should Pass (Important):

1. **Performance Targets**: <1s average response time, >95% success rate
2. **Cost Savings**: >35% savings vs premium-only approach
3. **Load Testing**: Maintain performance under concurrent load
4. **Decision Confidence**: >90% confidence in escalation decisions

### Nice to Have (Optimization):

1. **Resource Efficiency**: Optimal memory and CPU usage
2. **Scalability**: Linear performance scaling with load
3. **Monitoring**: Comprehensive metrics and alerting
4. **Documentation**: Complete test coverage and documentation

## 🐛 Troubleshooting

### Common Issues

#### Test Failures
```bash
# Check test logs
cat test_runner.log

# Run individual failing test
python tests/test_escalation_scenarios.py

# Debug specific scenario
python -c "
from test_escalation_scenarios import EscalationTestScenarios
scenarios = EscalationTestScenarios()
scenario = scenarios.get_scenario_by_name('scenario_name')
print(scenario)
"
```

#### Performance Issues
```bash
# Check system resources
top -p $(pgrep -f python)

# Run memory profiling
python -m memory_profiler scripts/benchmark_escalation_performance.py

# Monitor system performance during tests
python scripts/benchmark_escalation_performance.py stress_test
```

#### Configuration Problems
```bash
# Validate configuration files
python scripts/validate_escalation_workflows.py

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.claude/custom_modes.yml'))"

# Verify model configuration
python -c "import json; print(json.load(open('.claude/model-config.json')))"
```

## 📈 Performance Benchmarks

### Expected Performance

| Metric | Target | Acceptable | Critical |
|--------|---------|------------|----------|
| Decision Time | <1.0s | <2.0s | >5.0s |
| Success Rate | >99% | >95% | <90% |
| Accuracy | >95% | >90% | <85% |
| Cost Savings | >35% | >20% | <10% |
| Throughput | 50 req/s | 20 req/s | <10 req/s |

### Load Testing Results

Example results from medium load test (20 concurrent requests):

```
📈 Medium Load Results:
  📊 Throughput: 18.5 req/sec
  ⏱️  Avg Response: 1.08s
  ✅ Success Rate: 98.5%
  🎯 Accuracy: 96.2%
  💰 Cost/Request: $0.0003
  🔼 Escalation Rate: 15.3%
```

## 🔍 Monitoring and Observability

### Real-time Monitoring

```bash
# Monitor test execution in real-time
tail -f test_runner.log

# Watch performance metrics
python scripts/benchmark_escalation_performance.py | grep -E "(throughput|response|success)"

# Track cost efficiency
python scripts/model-usage-monitor.py report
```

### Alerting Thresholds

Configure alerts for:
- Success rate < 95%
- Average response time > 2s
- Cost savings < 20%
- Escalation rate > 25% (unexpected)

## 📝 Contributing

### Adding New Tests

1. **Scenario Tests**: Add to `test_escalation_scenarios.py`
2. **Validation Tests**: Extend `validate_escalation_workflows.py`
3. **Integration Tests**: Add to `test_escalation_integration.py`
4. **Performance Tests**: Configure in `benchmark_escalation_performance.py`

### Test Data Management

- Use realistic test data that reflects production scenarios
- Include edge cases and boundary conditions
- Maintain test data in version control
- Regularly review and update test scenarios

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
name: Escalation Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run escalation tests
        run: python scripts/run_escalation_tests.py --phase all
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_results/
```

## 📚 Documentation

### API Reference

#### EscalationEngine
```python
engine = EscalationEngine()
decision = engine.evaluate_escalation(role, task_context)
```

#### IntegrationTestSuite
```python
suite = IntegrationTestSuite()
result = await suite.run_end_to_end_test(scenario_name)
```

#### PerformanceBenchmark
```python
benchmark = PerformanceBenchmark()
results = benchmark.run_comprehensive_benchmark()
```

### Example Usage

```python
# Example: Test an architectural decision
from test_escalation_integration import EscalationEngine

engine = EscalationEngine()
decision = engine.evaluate_escalation(
    role="architect",
    task_context={
        "services_affected": ["orchestrator", "console", "terminal-daemon"],
        "security_implications": True,
        "risk_level": "critical"
    }
)

print(f"Should escalate: {decision.should_escalate}")
print(f"Selected model: {decision.selected_model}")
print(f"Confidence: {decision.confidence}")
```

## 🎯 Success Metrics

### Primary Success Indicators
- ✅ All critical acceptance criteria met
- ✅ Test automation coverage >90%
- ✅ Performance within target thresholds
- ✅ Cost optimization objectives achieved
- ✅ No production incidents related to escalation logic

### Secondary Success Indicators
- ✅ Development team adoption
- ✅ Reduced manual testing overhead
- ✅ Improved decision quality metrics
- ✅ Cost savings sustained over time

---

This testing framework provides comprehensive validation of the hybrid model escalation workflows, ensuring reliable and efficient operation of the GLM-4.5 and Claude 4.1 Opus selection system. Regular execution of these tests helps maintain system quality and performance over time.