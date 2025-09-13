# Kyros Hybrid Model System - User Guide

## Table of Contents
- [System Overview](#system-overview)
- [Getting Started](#getting-started)
- [Using the Hybrid Model System](#using-the-hybrid-model-system)
- [Agent Roles and Responsibilities](#agent-roles-and-responsibilities)
- [Escalation Procedures](#escalation-procedures)
- [Monitoring and Operations](#monitoring-and-operations)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## System Overview

The Kyros Hybrid Model System uses **GLM-4.5 as the universal default model** (95% of tasks) with intelligent escalation to **Claude 4.1 Opus** (5% of tasks) for critical architectural decisions. This strategy balances cost efficiency with quality assurance.

### Key Benefits
- **35-50% Cost Reduction**: Achieved through strategic model selection
- **Maintained Quality**: Critical decisions handled by premium model
- **Automated Escalation**: Intelligent triggers determine when escalation is needed
- **Full Transparency**: Complete visibility into model usage and costs

### Architecture
- **Orchestrator Service**: FastAPI backend handling task coordination
- **Console Service**: Next.js frontend for user interaction
- **Terminal Daemon**: WebSocket service for command execution
- **MCP Servers**: Model Context Protocol for AI model integration
- **Agent Roles**: Specialized AI agents with defined responsibilities

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+ with pip/uv
- Docker and Docker Compose
- API keys for AI models (GLM-4.5, Claude 4.1 Opus)

### Environment Setup

1. **Clone and Configure**
```bash
git clone <repository-url>
cd kyros-praxis
cp .env.example .env
# Edit .env with your API keys and configuration
```

2. **Start Services**
```bash
# Start infrastructure
docker-compose up -d

# Start development environment
./run-dev.sh

# Or start individual services
cd services/console && npm run dev
cd services/orchestrator && python -m uvicorn main:app --reload
cd services/terminal-daemon && npm run dev
```

3. **Verify Installation**
```bash
# Health checks
curl http://localhost:8000/healthz
curl http://localhost:3000/api/health

# Test MCP servers
./scripts/mcp-up.sh
```

### First-Time Configuration

1. **Configure Agent Roles**
```bash
# View current configuration
cat .claude/custom_modes.yml

# Validate configuration
python scripts/validate_agent_config.py
```

2. **Set Up Monitoring**
```bash
# Start model usage monitoring
python scripts/model-usage-monitor.py

# View current metrics
curl http://localhost:8000/v1/escalation/statistics
```

3. **Configure Escalation Rules**
```bash
# View escalation configuration
cat services/orchestrator/escalation_config.json

# Test escalation triggers
python scripts/test_escalation_scenarios.py
```

## Using the Hybrid Model System

### Basic Workflow

1. **Create a Task**
```bash
# Submit task to orchestrator
curl -X POST http://localhost:8000/collab/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication system",
    "type": "implementation",
    "priority": "high"
  }'
```

2. **Monitor Progress**
```bash
# Check task status
curl http://localhost:8000/collab/tasks/{task_id}

# View model usage
python scripts/model-usage-monitor.py
```

3. **Review Results**
```bash
# Check escalation decisions
curl http://localhost:8000/v1/escalation/status/{workflow_id}

# View cost analysis
python scripts/analyze-cost-savings.py
```

### Agent Role Selection

| Role | Primary Model | When to Use | Key Responsibilities |
|------|--------------|-------------|---------------------|
| **Architect** | GLM-4.5 | Planning and design | Creates ADRs, defines interfaces, sets technical direction |
| **Orchestrator** | GLM-4.5 | Task coordination | Manages workflow, coordinates agents, tracks state |
| **Implementer** | GLM-4.5 | Code implementation | Writes code, creates tests, updates documentation |
| **Critic** | GLM-4.5 | Code review | Validates quality, enforces standards, checks acceptance |
| **Integrator** | GLM-4.5 | Merge coordination | Resolves conflicts, manages deployments, coordinates PRs |

### Interactive Usage

**Using the Console UI:**
1. Access http://localhost:3000
2. Select agent role from dashboard
3. Describe your task with clear requirements
4. Monitor real-time progress
5. Review results and provide feedback

**Using CLI Tools:**
```bash
# Submit task via CLI
python scripts/submit_task.py \
  --role implementer \
  --description "Fix authentication bug" \
  --priority high \
  --files "services/orchestrator/auth.py"

# Monitor task progress
python scripts/monitor_task.py --task-id {task_id}

# View cost analysis
python scripts/cost_analysis.py --period daily
```

## Agent Roles and Responsibilities

### Architect
**Primary Functions:**
- Creates architectural decisions (ADRs)
- Defines system interfaces and contracts
- Plans technical roadmaps
- Sets coding standards and patterns

**When to Use:**
- New feature planning
- System redesign decisions
- Technology selection
- Performance optimization planning

**Example Commands:**
```bash
# Create ADR
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "architect", "type": "adr", "title": "Database Migration Strategy"}'

# Plan architecture
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "architect", "type": "plan", "description": "Design microservice architecture"}'
```

### Orchestrator
**Primary Functions:**
- Manages task lifecycle
- Coordinates agent handoffs
- Tracks project state
- Enforces workflow rules

**When to Use:**
- Task creation and assignment
- Progress monitoring
- Workflow management
- State coordination

**Example Commands:**
```bash
# Create and assign task
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "orchestrator", "assign_to": "implementer", "title": "Bug fix"}'

# Advance task state
python scripts/state_update.py TDS-123 approved --if-match abc123
```

### Implementer
**Primary Functions:**
- Writes production code
- Creates unit tests
- Updates documentation
- Follows coding standards

**When to Use:**
- Feature implementation
- Bug fixes
- Test creation
- Documentation updates

**Example Commands:**
```bash
# Implement feature
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "implementer", "files": ["services/console/src/"], "description": "Add user profile page"}'

# Run tests
npm test
python -m pytest
```

### Critic
**Primary Functions:**
- Reviews code quality
- Validates acceptance criteria
- Checks for security issues
- Ensures standards compliance

**When to Use:**
- Code review requests
- Quality assurance
- Security validation
- Standards enforcement

**Example Commands:**
```bash
# Request code review
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "critic", "review_files": ["services/orchestrator/main.py"]}'

# Validate changes
python scripts/pr_gate_minimal.py
```

### Integrator
**Primary Functions:**
- Manages merge conflicts
- Coordinates deployments
- Updates project state
- Manages release process

**When to Use:**
- Pull request management
- Conflict resolution
- Deployment coordination
- Release management

**Example Commands:**
```bash
# Request merge
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "integrator", "pr_id": 123, "action": "merge"}'

# Resolve conflicts
git merge origin/main --no-commit --no-ff
# Manual resolution, then:
git commit
```

## Escalation Procedures

### Automatic Escalation Triggers

The system automatically escalates to Claude 4.1 Opus when:

**Security-Critical Tasks:**
- Authentication/authorization implementation
- Encryption/cryptography changes
- Security vulnerability fixes
- Compliance requirements

**High-Complexity Tasks:**
- Multi-file changes (>3 files)
- Cross-service dependencies
- Database schema migrations
- Complex algorithm implementations

**Business Impact:**
- Revenue-critical features
- Performance optimization
- API contract changes
- Migration strategies

### Manual Escalation

**Request Escalation:**
```bash
curl -X POST http://localhost:8000/v1/escalation/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Implement OAuth2 with JWT authentication",
    "files_to_modify": ["auth.py", "security/middleware.py"],
    "task_type": "implementation",
    "requester": "developer",
    "priority": "high",
    "justification": "Security-critical authentication system"
  }'
```

**Monitor Escalation:**
```bash
# Check escalation status
curl http://localhost:8000/v1/escalation/status/{workflow_id}

# View escalation statistics
curl http://localhost:8000/v1/escalation/statistics

# Analyze escalation patterns
python scripts/analyze_escalation_patterns.py
```

### Escalation Approval Process

1. **Automatic Analysis**: System analyzes task complexity and business impact
2. **Risk Assessment**: Evaluates security, performance, and business implications
3. **Cost-Benefit Analysis**: Determines if escalation provides sufficient value
4. **Decision**: Escalates if confidence score exceeds threshold (default: 0.7)
5. **Execution**: Routes task to Claude 4.1 Opus for processing
6. **Validation**: Confirms escalation decision was appropriate

## Monitoring and Operations

### Real-time Monitoring

**Dashboard Access:**
- Main Dashboard: http://localhost:3000/dashboard
- Model Usage: http://localhost:3000/models
- Task Status: http://localhost:3000/tasks
- Cost Analysis: http://localhost:3000/costs

**CLI Monitoring Tools:**
```bash
# Real-time model usage
python scripts/model-usage-monitor.py --real-time

# Cost tracking
python scripts/cost_analysis.py --live

# Task monitoring
python scripts/task_monitor.py --follow

# System health
python scripts/health_check.py --continuous
```

### Key Metrics

**Cost Metrics:**
- Daily cost per model
- Cost savings percentage
- ROI calculation
- Budget utilization

**Quality Metrics:**
- Task success rate
- Escalation accuracy
- Code quality scores
- User satisfaction

**Performance Metrics:**
- Response times by model
- Task completion rates
- System availability
- Error rates

### Alerting

**Configure Alerts:**
```yaml
# monitoring/alerts.yml
alerts:
  cost_overrun:
    threshold: 150% of budget
    notification: email + slack
  high_error_rate:
    threshold: 5% error rate
    notification: pagerduty
  escalation_spike:
    threshold: 10% escalation rate
    notification: slack + email
  system_unavailable:
    threshold: 99% availability
    notification: pagerduty + phone
```

**Respond to Alerts:**
```bash
# View active alerts
curl http://localhost:8000/v1/alerts/active

# Acknowledge alert
curl -X POST http://localhost:8000/v1/alerts/{alert_id}/acknowledge

# Resolve alert
curl -X POST http://localhost:8000/v1/alerts/{alert_id}/resolve
```

## Best Practices

### Task Creation

**Effective Task Descriptions:**
- Be specific about requirements and outcomes
- Include relevant keywords (security, performance, architecture)
- List all affected files and components
- Specify acceptance criteria clearly
- Include examples and expected behavior

**Example Good Task:**
```
Title: Implement JWT authentication with OAuth2 integration

Description:
- Add JWT-based authentication to user service
- Integrate with Google OAuth2 provider
- Implement refresh token mechanism
- Add rate limiting for auth endpoints
- Update all relevant API endpoints

Files to modify:
- services/orchestrator/auth.py
- services/console/src/auth/
- docs/api/authentication.md

Acceptance criteria:
- Users can login with Google OAuth2
- JWT tokens are properly validated
- Refresh tokens work correctly
- Auth endpoints are rate limited
- All tests pass
```

### Cost Optimization

**Strategies for Cost Control:**
- Use appropriate agent roles for each task
- Avoid unnecessary escalations
- Batch similar tasks together
- Monitor usage patterns
- Set budget alerts

**Cost-Saving Tips:**
- Use GLM-4.5 for routine tasks
- Reserve Claude 4.1 Opus for critical decisions
- Review escalation patterns regularly
- Optimize task descriptions to include context
- Use caching where appropriate

### Quality Assurance

**Ensuring High Quality:**
- Always run tests before committing
- Use the Critic role for code reviews
- Follow established coding standards
- Update documentation with code changes
- Monitor quality metrics regularly

**Quality Checks:**
```bash
# Run quality gates
python scripts/pr_gate_minimal.py --run-tests

# Check code standards
npm run lint
python -m flake8

# Validate documentation
python scripts/validate_docs.py

# Test escalation quality
python scripts/test_escalation_quality.py
```

## Troubleshooting

### Common Issues

**Task Not Processing:**
```bash
# Check orchestrator status
curl http://localhost:8000/healthz

# View task queue
curl http://localhost:8000/collab/tasks/queue

# Check agent availability
curl http://localhost:8000/v1/agents/status
```

**Escalation Not Triggering:**
```bash
# Check escalation configuration
curl http://localhost:8000/v1/escalation/config

# Test escalation triggers
python scripts/test_escalation_triggers.py

# View escalation logs
python scripts/escalation_logs.py --tail 50
```

**High Error Rates:**
```bash
# View error logs
python scripts/error_analysis.py

# Check system health
python scripts/health_check.py --detailed

# Restart affected services
docker-compose restart orchestrator
```

### Performance Issues

**Slow Response Times:**
```bash
# Monitor performance
python scripts/performance_monitor.py

# Check model response times
curl http://localhost:8000/v1/models/performance

# Optimize configuration
python scripts/optimize_performance.py
```

**Resource Utilization:**
```bash
# Monitor system resources
docker stats

# Check database performance
python scripts/db_performance.py

# Optimize queries
python scripts/optimize_queries.py
```

### Getting Help

**Documentation Resources:**
- [API Documentation](./api-documentation.md)
- [Deployment Guide](./deployment-guide.md)
- [Training Materials](./training-materials.md)
- [FAQ](./faq.md)

**Support Channels:**
- Internal Slack: #kyros-support
- Email: kyros-support@company.com
- Emergency: PagerDuty escalation

**Debug Mode:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# View detailed logs
python scripts/debug_logs.py

# Test specific components
python scripts/debug_component.py --component escalation
```

---

## Next Steps

1. **Complete Setup**: Finish environment configuration and testing
2. **First Task**: Submit a simple task to test the system
3. **Monitor Usage**: Set up monitoring and alerting
4. **Team Training**: Conduct training sessions for team members
5. **Optimize**: Review usage patterns and optimize configuration

For advanced usage and configuration, see the [Advanced Configuration Guide](./advanced-configuration.md).