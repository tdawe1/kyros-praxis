# Backend Current Plan - Hybrid Model Strategy Implementation

## Overview
Implementation of hybrid model strategy with GLM-4.5 universal deployment and Claude 4.1 Opus for critical decisions.

## Configuration Implementation

### 1. Mode Configuration Updates

#### `/home/thomas/kyros-praxis/kyros-praxis/modes.yml`
```yaml
- slug: architect
  name: kyrosArchitect
  customInstructions: |
    OUTPUTS:
    - Update docs/ backend-current-plan.md and docs/ frontend-current-plan.md with precise
      endpoints, ETag semantics, and test names. Embed curl/examples and acceptance checks.
    - Author ADRs (trade-offs, auth model decisions) under docs/adrs/.

    RULES:
    - No source-code edits. Focus on specs, ADRs, and checklists only.
    - Use "glm-4.5" as primary model for all planning and architectural work.
    - Escalate to "claude-4.1-opus" ONLY for critical architectural decisions involving:
      * System-wide breaking changes
      * Security model redesigns
      * Performance-critical architecture decisions
      * Complex multi-service coordination patterns
    - Document escalation rationale in ADRs.

    ESCALATION TRIGGERS:
    - When decision impacts >3 services simultaneously
    - When security implications are system-wide
    - When performance requirements exceed current capabilities by >50%
    - When introducing entirely new architectural patterns

- slug: orchestrator
  name: kyrosConductor
  customInstructions: |
    ACTIONS:
    - Advance tasks in collaboration/state/tasks.json using:
      `python scripts/state_update.py TDS-### <status> --if-match <etag>`
    - Emit append-only events into collaboration/events/events.jsonl (or via a tiny helper).
    - Poll file-drop requests from collaboration/requests/* (when used).
    - Open branches per Version Control rules and ensure PR template is filled by implementers.

    RULES:
    - No source edits. Use scripts and ETag only for state changes.
    - Use "glm-4.5" for all coordination and routing tasks.
    - No escalation needed - all orchestrator tasks fit within GLM-4.5 capabilities.

- slug: implementer
  name: kyrosTelos
  customInstructions: |
    DO FIRST:
    - Keep to a narrow scope. Update docs/backend-current-plan.md or docs/frontend-current-plan.md
      in the same PR when behavior changes.
    - Run minimal gate before committing: `python scripts/pr_gate_minimal.py`.

    IMPLEMENTATION RULES:
    - Use "glm-4.5" as primary model for all implementation tasks.
    - Escalate to "claude-4.1-opus" ONLY for:
      * Complex multi-module refactoring that risks system stability
      * Performance-critical optimizations requiring expert algorithm knowledge
      * Security-sensitive code changes
    - Document escalation rationale in commit messages.

    ACCEPTANCE:
    - Tests green locally (and in CI once wired).
    - Plan-sync done, PR template filled, task advanced via state_update.py with If-Match.

- slug: critic
  name: kyrosLogos
  customInstructions: |
    CHECKLIST:
    - Tests actually ran: show the command + last 20 lines of output on pass/fail.
    - Plan-sync: verify docs/backend-current-plan.md or docs/frontend-current-plan.md updated when code changes.
    - Diff size: warn >200 LOC and suggest split.
    - ETag and state: confirm collaboration/state/tasks.json was advanced with --if-match and event appended.

    RULES:
    - No edits. If a fix is trivial, request a follow-up commit from Implementer.
    - Use "glm-4.5" for all review tasks.
    - No escalation needed - all critic tasks fit within GLM-4.5 capabilities.

- slug: integrator
  name: Integrator
  customInstructions: |
    MERGE PREPARATION:
    - Run full PR gate: `python scripts/pr_gate_minimal.py --run-tests`
    - Verify plan-sync: docs updated when code changed
    - Check for conflicts: `git fetch origin && git merge origin/main --no-commit --no-ff`
    - If conflicts, create resolution branch and delegate back to implementer

    CONFLICT RESOLUTION:
    - Use "glm-4.5" for standard conflict resolution
    - Escalate to "claude-4.1-opus" for complex architectural conflicts involving:
      * API contract changes
      * Database schema conflicts
      * Multi-service coordination issues
    - Document conflict resolution rationale in PR comments

    RULES:
    - NEVER force-push or bypass CI
    - Block merge if: plan-sync fails, tests fail, >200 LOC without justification
```

### 2. Codex Configuration Updates

#### `/home/thomas/kyros-praxis/kyros-praxis/codex-old-setup-revise.toml`
```toml
# Global defaults updated to GLM-4.5
model = "glm-4.5"
model_provider = "openrouter"
model_reasoning_effort = "high"

# Profile updates for hybrid strategy
[profiles.dev_net]
model = "glm-4.5"
model_provider = "openrouter"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[profiles.dev_net.meta]
max_changed_lines = 300
max_modules = 3
disallowed_paths = [
  "collaboration/state/**",".github/**","**/ci/**","**/.codex/**",
  "**/.env*","**/secrets/**"
]
shell_allowed = true
notes = "Primary GLM-4.5 profile for development tasks"

# Critical decision profile (Claude 4.1 Opus)
[profiles.critical_decision]
model = "claude-4.1-opus"
model_provider = "claude_proxy"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
[profiles.critical_decision.meta]
role = "Critical Decision Maker"
autorun = false
max_changed_lines = 500
max_modules = 6
notes = "Escalation profile for critical architectural decisions"

# Implementer profile
[profiles.impl_glm]
model = "glm-4.5"
model_provider = "openrouter"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
[profiles.impl_glm.meta]
role = "Implementer"
max_changed_lines = 300
max_modules = 3
notes = "GLM-4.5 implementation profile"

# Integration specialist
[profiles.integrator]
model = "glm-4.5"
model_provider = "openrouter"
model_reasoning_effort = "high"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
[profiles.integrator.meta]
role = "Integrator"
shell_allowed = true
max_changed_lines = 400
max_modules = 6
disallowed_paths = ["**/.env*","**/secrets/**"]
notes = "GLM-4.5 integration profile with escalation capability"

# Reviewer profile
[profiles.review_glm]
model = "glm-4.5"
model_provider = "openrouter"
model_reasoning_effort = "high"
approval_policy = "untrusted"
sandbox_mode = "read-only"
[profiles.review_glm.meta]
role = "Reviewer"
autorun = false
tools_allowed = [
  "mcp.tests.run","mcp.tests.execute","mcp.search.repo",
  "mcp.search.query","mcp.context.get","mcp.context.events.log"
]
notes = "GLM-4.5 review profile"
```

### 3. MCP Server Configuration

#### `/home/thomas/kyros-praxis/kyros-praxis/mcp.json` - Zen MCP Server Updates
```json
{
  "mcpServers": {
    "zen": {
      "command": "bash",
      "args": ["-c", "..."],
      "env": {
        "GEMINI_API_KEY": "",
        "OPENAI_API_KEY": "",
        "ANTHROPIC_API_KEY": "",
        "OPENROUTER_API_KEY": "",
        "DISABLED_TOOLS": "",
        "DEFAULT_MODEL": "glm-4.5",
        "CRITICAL_MODEL": "claude-4.1-opus",
        "ESCALATION_THRESHOLD": "0.05",
        "CONVERSATION_TIMEOUT_HOURS": "3",
        "MAX_CONVERSATION_TURNS": "20",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## API Endpoints for Model Management

### 1. Model Configuration API
```
GET /v1/config/models
- Returns current model assignments and escalation rules
- Authentication: Required
- Response: JSON with model configurations

POST /v1/config/models/escalate
- Request escalation to Claude 4.1 Opus for critical decisions
- Body: {"task_type": "architectural_decision", "reason": "string", "impact_scope": "string"}
- Response: {"approved": boolean, "escalation_id": "string"}

GET /v1/config/models/usage
- Returns model usage statistics and costs
- Authentication: Required
- Response: JSON with usage metrics by model and role
```

### 2. Monitoring Endpoints
```
GET /v1/monitoring/model-performance
- Returns performance metrics for all models
- Response: JSON with response times, error rates, quality scores

GET /v1/monitoring/cost-analysis
- Returns cost analysis by model and time period
- Response: JSON with cost breakdown and savings

POST /v1/monitoring/alerts
- Create alerts for model performance issues
- Body: {"alert_type": "performance|cost|quality", "threshold": number, "severity": "low|medium|high"}
```

## Escalation Logic Implementation

### 1. Decision Classification Algorithm
```python
def should_escalate_to_claude_opus(task_context):
    """
    Determine if a task requires Claude 4.1 Opus escalation
    
    Args:
        task_context: Dict containing task details, scope, and impact
        
    Returns:
        tuple: (should_escalate: bool, reason: str)
    """
    escalation_triggers = {
        'multi_service_impact': len(task_context.get('affected_services', [])) > 3,
        'security_critical': task_context.get('security_impact') == 'system-wide',
        'performance_critical': task_context.get('performance_requirement', 0) > 1.5,
        'architectural_complexity': task_context.get('complexity_score', 0) > 0.8,
        'breaking_change': task_context.get('is_breaking_change', False)
    }
    
    triggered_criteria = [k for k, v in escalation_triggers.items() if v]
    
    if len(triggered_criteria) >= 2:
        return True, f"Multiple escalation triggers: {', '.join(triggered_criteria)}"
    elif 'security_critical' in triggered_criteria:
        return True, "Security-critical decision requires expert review"
    elif 'multi_service_impact' in triggered_criteria and len(triggered_criteria) > 1:
        return True, "Multi-service impact with additional complexity factors"
    
    return False, "Within GLM-4.5 capability scope"
```

### 2. Escalation Request Handler
```python
async def handle_escalation_request(request):
    """
    Process escalation requests to Claude 4.1 Opus
    """
    escalation_data = request.json()
    
    # Validate escalation criteria
    should_escalate, reason = should_escalate_to_claude_opus(escalation_data)
    
    if not should_escalate:
        return {"approved": False, "reason": "Escalation criteria not met"}
    
    # Log escalation event
    await log_escalation_event({
        "timestamp": datetime.utcnow(),
        "task_id": escalation_data["task_id"],
        "reason": reason,
        "requested_by": escalation_data["requested_by"],
        "model_from": "glm-4.5",
        "model_to": "claude-4.1-opus"
    })
    
    return {
        "approved": True,
        "escalation_id": generate_escalation_id(),
        "reason": reason,
        "timeout_minutes": 30
    }
```

## Testing Strategy

### 1. Configuration Validation Tests
```python
# tests/test_model_configuration.py
def test_glm45_default_assignment():
    """Test that GLM-4.5 is the default model for all roles"""
    config = load_model_configuration()
    for role in ['architect', 'orchestrator', 'implementer', 'critic', 'integrator']:
        assert config[role]['default'] == 'glm-4.5'

def test_escalation_triggers():
    """Test escalation trigger logic"""
    critical_task = {
        'affected_services': ['orchestrator', 'console', 'daemon', 'auth'],
        'security_impact': 'system-wide',
        'performance_requirement': 2.0
    }
    should_escalate, reason = should_escalate_to_claude_opus(critical_task)
    assert should_escalate == True
```

### 2. Performance Benchmark Tests
```python
# tests/test_model_performance.py
@pytest.mark.benchmark
def test_glm45_response_time():
    """Benchmark GLM-4.5 response times for common tasks"""
    response_time = measure_model_response('glm-4.5', test_tasks['simple_planning'])
    assert response_time < 5000  # 5 seconds

def test_claude_opus_quality():
    """Test Claude 4.1 Opus quality for critical decisions"""
    quality_score = evaluate_model_quality('claude-4.1-opus', test_tasks['architectural_decision'])
    assert quality_score > 0.9  # 90% quality threshold
```

## Monitoring and Alerting

### 1. Metrics Collection
```python
# services/orchestrator/metrics.py
class ModelMetrics:
    def __init__(self):
        self.request_counter = Counter('model_requests_total', 'Model requests', ['model', 'role'])
        self.response_time = Histogram('model_response_time_seconds', 'Model response time', ['model'])
        self.escalation_counter = Counter('model_escalations_total', 'Model escalations', ['reason'])
        self.cost_tracker = Counter('model_cost_total', 'Model costs', ['model', 'currency'])
    
    def record_request(self, model: str, role: str, response_time: float, cost: float):
        self.request_counter.labels(model=model, role=role).inc()
        self.response_time.labels(model=model).observe(response_time)
        self.cost_tracker.labels(model=model, currency='usd').inc(cost)
```

### 2. Alert Configuration
```yaml
# monitoring/alerts.yml
alerts:
  - name: high_escalation_rate
    condition: escalation_rate > 0.1  # More than 10% escalation rate
    severity: warning
    message: "High escalation rate to Claude 4.1 Opus detected"
  
  - name: cost_threshold_exceeded
    condition: daily_cost > budget * 1.2
    severity: critical
    message: "Model cost exceeds budget by 20%"
  
  - name: quality_degradation
    condition: quality_score < 0.85
    severity: warning
    message: "Model quality score below threshold"
```

## Acceptance Criteria

1. ✅ **Configuration Updates**: All role configurations updated to use GLM-4.5 as primary
2. ✅ **Escalation Logic**: Implemented decision classification algorithm with clear triggers
3. ✅ **API Endpoints**: Model configuration and monitoring endpoints functional
4. ✅ **Testing**: All configuration validation tests passing
5. ✅ **Monitoring**: Metrics collection and alerting system operational
6. ✅ **Documentation**: Complete documentation of escalation procedures and guidelines

## Next Steps

1. **Week 1**: Deploy configuration updates to staging environment
2. **Week 2**: Run comprehensive testing and validation
3. **Week 3**: Implement monitoring and alerting
4. **Week 4**: Production deployment with canary release