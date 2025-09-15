# Kyros Hybrid Model System - Training Materials

## Table of Contents
- [Training Overview](#training-overview)
- [Getting Started Training](#getting-started-training)
- [Agent Role Training](#agent-role-training)
- [Advanced Usage Training](#advanced-usage-training)
- [Operations Training](#operations-training)
- [Best Practices Workshop](#best-practices-workshop)
- [Hands-on Labs](#hands-on-labs)
- [Assessment and Certification](#assessment-and-certification)

## Training Overview

### Training Objectives

By the end of this training, participants will be able to:
- Understand the Kyros Hybrid Model System architecture
- Effectively use all agent roles for appropriate tasks
- Monitor system performance and costs
- Troubleshoot common issues
- Apply best practices for optimal results
- Perform operational tasks efficiently

### Target Audience

**Primary:**
- Software Developers
- System Architects
- DevOps Engineers
- Project Managers
- Quality Assurance Engineers

**Secondary:**
- Product Managers
- Business Analysts
- Technical Writers
- Support Engineers

### Prerequisites

- Basic understanding of AI/ML concepts
- Familiarity with REST APIs
- Basic knowledge of Python and JavaScript
- Understanding of software development lifecycle
- Experience with version control (Git)

### Training Structure

**Module 1: System Fundamentals (2 hours)**
- Architecture overview
- Agent roles and responsibilities
- Hybrid model strategy
- Basic usage patterns

**Module 2: Practical Usage (3 hours)**
- Console UI walkthrough
- CLI tools usage
- Task creation and management
- Monitoring and reporting

**Module 3: Advanced Features (2 hours)**
- Escalation procedures
- Cost optimization
- Performance tuning
- Integration patterns

**Module 4: Operations (2 hours)**
- System administration
- Incident response
- Maintenance procedures
- Security practices

**Module 5: Hands-on Lab (3 hours)**
- Practical exercises
- Real-world scenarios
- Troubleshooting practice
- Certification assessment

## Getting Started Training

### Introduction to Kyros (30 minutes)

**What is Kyros?**
Kyros is a manifest-driven monorepo with a hybrid AI model system that combines GLM-4.5 (95% usage) with Claude 4.1 Opus (5% usage) for optimal cost-efficiency and quality.

**Key Concepts:**
```
Hybrid Model Strategy:
├── GLM-4.5 (Universal Model)
│   ├── Cost-effective
│   ├── High throughput
│   └── Handles 95% of tasks
├── Claude 4.1 Opus (Premium Model)
│   ├── High quality
│   ├── Complex reasoning
│   └── Handles 5% of critical tasks
└── Intelligent Escalation
    ├── Automatic detection
    ├── Cost-benefit analysis
    └── Quality assurance
```

**System Architecture:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Console       │    │  Orchestrator   │    │ Terminal Daemon │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Node.js)     │
│   User Interface│    │ Task Coordination│    │ Command Execution│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AI Models     │
                    │ GLM-4.5 + Opus  │
                    └─────────────────┘
```

### First Steps Lab (45 minutes)

**Exercise 1: System Setup**
```bash
# Clone repository
git clone <repository-url>
cd kyros-praxis

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d
./run-dev.sh

# Verify installation
curl http://localhost:3000/api/health
curl http://localhost:8000/healthz
```

**Exercise 2: Basic Task Creation**
```bash
# Create a simple task using CLI
python scripts/submit_task.py \
  --role implementer \
  --title "Add user profile page" \
  --description "Create a basic user profile page with name and email display" \
  --priority medium

# Monitor task progress
python scripts/monitor_task.py --follow

# Check results
python scripts/task_results.py --task-id <task_id>
```

**Exercise 3: Console UI Navigation**
1. Access http://localhost:3000
2. Navigate through dashboard sections
3. Create a task using the UI
4. Monitor task progress
5. View cost and usage metrics

### Basic Configuration (45 minutes)

**Agent Role Configuration**
```yaml
# .claude/custom_modes.yml
customModes:
  - slug: architect
    model: glm-4.5
    # Configuration for architectural tasks
    
  - slug: implementer
    model: glm-4.5
    # Configuration for implementation tasks
    
  - slug: critic
    model: glm-4.5
    # Configuration for review tasks
```

**Escalation Configuration**
```json
{
  "escalation_rules": {
    "security_critical": {
      "keywords": ["auth", "security", "encryption"],
      "min_confidence": 0.8,
      "max_cost": 50.0
    },
    "complexity_high": {
      "file_count_threshold": 3,
      "service_count_threshold": 2,
      "min_confidence": 0.7
    }
  }
}
```

## Agent Role Training

### Architect Role Training (1 hour)

**Role Overview:**
The Architect role is responsible for system design, technical planning, and architectural decisions. Uses GLM-4.5 for most tasks with escalation to Claude 4.1 Opus for complex architectural decisions.

**Key Responsibilities:**
- Create Architecture Decision Records (ADRs)
- Define system interfaces and contracts
- Plan technical roadmaps
- Evaluate technology choices
- Design system components

**When to Use Architect:**
- New feature planning
- System redesign decisions
- Technology selection
- Performance optimization planning
- Integration architecture design

**Practical Exercise:**
```bash
# Create an ADR
curl -X POST http://localhost:8000/collab/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "role": "architect",
    "type": "adr",
    "title": "Database Migration Strategy",
    "description": "Plan migration from SQLite to PostgreSQL",
    "context": "Current system uses SQLite, need to scale to multi-tenant",
    "options": ["PostgreSQL", "MySQL", "MongoDB"],
    "deadline": "2024-02-01"
  }'

# Monitor ADR creation
python scripts/monitor_task.py --task-id <task_id>

# Review generated ADR
cat docs/adrs/001-database-migration.md
```

**Best Practices for Architect:**
1. **Clear Requirements**: Provide detailed context and constraints
2. **Multiple Options**: Always evaluate multiple technology choices
3. **Impact Analysis**: Consider implementation complexity and business impact
4. **Documentation**: Maintain ADRs for all major decisions
5. **Review Process**: Have ADRs reviewed by team members

### Implementer Role Training (1 hour)

**Role Overview:**
The Implementer role handles code implementation, testing, and documentation. Primarily uses GLM-4.5 for all implementation tasks.

**Key Responsibilities:**
- Write production-quality code
- Create comprehensive tests
- Update documentation
- Follow coding standards
- Implement security best practices

**When to Use Implementer:**
- Feature implementation
- Bug fixes
- Test creation
- Documentation updates
- Code refactoring

**Practical Exercise:**
```bash
# Implement a feature
curl -X POST http://localhost:8000/collab/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "role": "implementer",
    "type": "implementation",
    "title": "Add user authentication endpoints",
    "description": "Implement JWT-based authentication with refresh tokens",
    "files_to_modify": [
      "services/orchestrator/auth.py",
      "services/orchestrator/routers/auth.py",
      "services/console/src/auth/index.ts"
    ],
    "acceptance_criteria": [
      "Users can register with email/password",
      "JWT tokens are properly generated and validated",
      "Refresh token mechanism works",
      "All endpoints are properly secured",
      "Tests cover all authentication flows"
    ],
    "priority": "high"
  }'

# Run tests after implementation
npm test
python -m pytest tests/test_auth.py

# Validate implementation
python scripts/pr_gate_minimal.py --run-tests
```

**Best Practices for Implementer:**
1. **Small Changes**: Keep implementations under 200 LOC when possible
2. **Test Coverage**: Maintain high test coverage for all changes
3. **Documentation**: Update documentation alongside code changes
4. **Security**: Follow security best practices in all implementations
5. **Performance**: Consider performance implications of changes

### Critic Role Training (45 minutes)

**Role Overview:**
The Critic role ensures code quality, enforces standards, and validates acceptance criteria. Uses GLM-4.5 for consistent, deterministic reviews.

**Key Responsibilities:**
- Review code quality
- Validate acceptance criteria
- Check for security issues
- Ensure standards compliance
- Provide constructive feedback

**When to Use Critic:**
- Code review requests
- Quality assurance checks
- Security validation
- Standards enforcement
- Pre-merge validation

**Practical Exercise:**
```bash
# Request code review
curl -X POST http://localhost:8000/collab/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "role": "critic",
    "type": "review",
    "title": "Review authentication implementation",
    "files_to_review": [
      "services/orchestrator/auth.py",
      "services/orchestrator/routers/auth.py"
    ],
    "acceptance_criteria": [
      "Code follows project standards",
      "No security vulnerabilities",
      "Proper error handling",
      "Adequate test coverage",
      "Documentation is updated"
    ]
  }'

# Run quality gates
python scripts/pr_gate_minimal.py --run-tests

# Review feedback
python scripts/task_results.py --task-id <task_id>
```

**Best Practices for Critic:**
1. **Comprehensive Review**: Check all aspects of code quality
2. **Security Focus**: Pay special attention to security implications
3. **Constructive Feedback**: Provide actionable improvement suggestions
4. **Standards Enforcement**: Ensure compliance with project standards
5. **Documentation**: Verify documentation matches implementation

### Orchestrator Role Training (45 minutes)

**Role Overview:**
The Orchestrator role manages task lifecycle, coordinates agent handoffs, and maintains system state. Uses GLM-4.5 for all coordination tasks.

**Key Responsibilities:**
- Create and manage tasks
- Coordinate agent workflows
- Track project state
- Enforce process rules
- Handle task transitions

**When to Use Orchestrator:**
- Task creation and assignment
- Progress monitoring
- Workflow management
- State coordination
- Process enforcement

**Practical Exercise:**
```bash
# Create and coordinate task
curl -X POST http://localhost:8000/collab/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "role": "orchestrator",
    "type": "coordination",
    "title": "Coordinate user authentication project",
    "description": "Manage implementation of user authentication system",
    "tasks": [
      {
        "role": "architect",
        "title": "Design authentication architecture",
        "deadline": "2024-01-15"
      },
      {
        "role": "implementer", 
        "title": "Implement authentication endpoints",
        "deadline": "2024-01-20"
      },
      {
        "role": "critic",
        "title": "Review authentication implementation",
        "deadline": "2024-01-22"
      }
    ]
  }'

# Monitor workflow progress
python scripts/monitor_workflow.py --workflow-id <workflow_id>

# Advance task states
python scripts/state_update.py TDS-123 approved --if-match abc123
```

**Best Practices for Orchestrator:**
1. **Clear Task Definition**: Provide detailed task descriptions and requirements
2. **Realistic Deadlines**: Set achievable deadlines based on complexity
3. **Progress Monitoring**: Track task progress and identify blockers
4. **State Management**: Keep task states synchronized
5. **Communication**: Ensure clear communication between agents

### Integrator Role Training (45 minutes)

**Role Overview:**
The Integrator role manages merge conflicts, coordinates deployments, and handles release management. Uses GLM-4.5 for standard integration tasks with escalation to Claude 4.1 Opus for complex conflicts.

**Key Responsibilities:**
- Manage pull requests
- Resolve merge conflicts
- Coordinate deployments
- Handle release management
- Update project state

**When to Use Integrator:**
- Pull request management
- Conflict resolution
- Deployment coordination
- Release management
- State updates

**Practical Exercise:**
```bash
# Request merge
curl -X POST http://localhost:8000/collab/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "role": "integrator",
    "type": "integration",
    "title": "Merge authentication feature branch",
    "pr_id": 123,
    "description": "Merge user authentication feature into main branch",
    "checks": [
      "All tests pass",
      "Documentation updated",
      "Code review approved",
      "No merge conflicts"
    ]
  }'

# Handle conflicts if any
git merge origin/main --no-commit --no-ff
# Resolve conflicts manually
git commit

# Update task state
python scripts/state_update.py TDS-123 done --if-match abc123
```

**Best Practices for Integrator:**
1. **Quality Gates**: Ensure all quality checks pass before merging
2. **Conflict Resolution**: Handle conflicts carefully, preserving both sides' intent
3. **Communication**: Keep team informed of merge status
4. **Documentation**: Update project documentation with releases
5. **Rollback Planning**: Always have rollback procedures ready

## Advanced Usage Training

### Escalation Management (1 hour)

**Understanding Escalation Triggers:**
The system automatically escalates to Claude 4.1 Opus based on:
- Task complexity analysis
- Security impact assessment
- Business impact evaluation
- Cost-benefit analysis

**Manual Escalation:**
```bash
# Request escalation
curl -X POST http://localhost:8000/v1/escalation/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Implement OAuth2 with SAML integration",
    "files_to_modify": [
      "auth.py",
      "security/saml.py",
      "config/security.py"
    ],
    "task_type": "implementation",
    "requester": "developer",
    "priority": "high",
    "justification": "Complex authentication system with security implications"
  }'

# Monitor escalation
curl http://localhost:8000/v1/escalation/status/{workflow_id}

# Review escalation decision
curl http://localhost:8000/v1/escalation/decisions/{decision_id}
```

**Escalation Best Practices:**
1. **Clear Justification**: Provide detailed reasoning for escalation requests
2. **Complete Context**: Include all relevant files and requirements
3. **Cost Awareness**: Consider cost implications of escalation
4. **Quality Focus**: Use escalation for quality-critical tasks only
5. **Monitor Results**: Track escalation effectiveness

### Cost Optimization (45 minutes)

**Cost Monitoring:**
```bash
# Daily cost report
python scripts/cost_report.py --period 1d

# Cost breakdown by model
python scripts/cost_breakdown.py --period 7d

# Cost optimization analysis
python scripts/cost_optimization.py

# Budget monitoring
python scripts/budget_monitor.py
```

**Optimization Strategies:**
1. **Model Selection**: Maximize GLM-4.5 usage for routine tasks
2. **Task Batching**: Group similar tasks together
3. **Caching**: Implement caching for repeated operations
4. **Escalation Control**: Limit unnecessary escalations
5. **Resource Optimization**: Optimize infrastructure usage

**Practical Exercise:**
```bash
# Analyze cost patterns
python scripts/cost_analysis.py --period 30d

# Identify optimization opportunities
python scripts/identify_optimization_opportunities.py

# Implement cost-saving measures
python scripts/implement_cost_savings.py

# Monitor results
python scripts/monitor_cost_savings.py
```

### Performance Tuning (45 minutes)

**Performance Monitoring:**
```bash
# Performance metrics
python scripts/performance_metrics.py

# Response time analysis
python scripts/response_time_analysis.py

# Bottleneck identification
python scripts/identify_bottlenecks.py

# Optimization recommendations
python scripts/optimization_recommendations.py
```

**Tuning Strategies:**
1. **Query Optimization**: Optimize database queries
2. **Index Optimization**: Add appropriate indexes
3. **Cache Optimization**: Implement effective caching
4. **Connection Pooling**: Optimize database connections
5. **Load Balancing**: Distribute load effectively

## Operations Training

### System Administration (1 hour)

**System Health Checks:**
```bash
# Comprehensive health check
python scripts/system_health_check.py

# Service-specific checks
python scripts/service_health.py --service orchestrator
python scripts/service_health.py --service console
python scripts/service_health.py --service terminal-daemon

# Database health
python scripts/database_health.py

# Network health
python scripts/network_health.py
```

**Log Management:**
```bash
# Log analysis
python scripts/log_analysis.py --period 24h

# Error tracking
python scripts/error_tracking.py

# Performance logging
python scripts/performance_logging.py

# Security logging
python scripts/security_logging.py
```

### Incident Response (45 minutes)

**Incident Handling:**
```bash
# Incident detection
python scripts/detect_incident.py

# Incident assessment
python scripts/assess_incident.py

# Incident response
python scripts/respond_to_incident.py

# Incident documentation
python scripts/document_incident.py
```

**Incident Scenarios:**
1. **System Outage**: Complete service unavailability
2. **Performance Degradation**: Slow response times
3. **Data Issues**: Data corruption or loss
4. **Security Incidents**: Unauthorized access or breaches
5. **Cost Overruns**: Unexpected cost increases

### Maintenance Procedures (45 minutes)

**Regular Maintenance:**
```bash
# Daily maintenance
python scripts/daily_maintenance.py

# Weekly maintenance
python scripts/weekly_maintenance.py

# Monthly maintenance
python scripts/monthly_maintenance.py

# Quarterly maintenance
python scripts/quarterly_maintenance.py
```

**Update Management:**
```bash
# System updates
python scripts/system_updates.py

# Dependency updates
python scripts/dependency_updates.py

# Security patches
python scripts/security_patches.py

# Configuration updates
python scripts/configuration_updates.py
```

## Best Practices Workshop

### Task Creation Best Practices (30 minutes)

**Effective Task Descriptions:**
1. **Clear Title**: Use descriptive, specific titles
2. **Detailed Description**: Provide context and requirements
3. **Acceptance Criteria**: Define clear success criteria
4. **File Lists**: Include all relevant files
5. **Priority Setting**: Set appropriate priorities

**Example Template:**
```
Title: [Verb] [Component] [Feature]

Description:
- Context and background
- Specific requirements
- Constraints and limitations
- Expected outcomes

Acceptance Criteria:
- [ ] Measurable criterion 1
- [ ] Measurable criterion 2
- [ ] Measurable criterion 3

Files to Modify:
- path/to/file1.py
- path/to/file2.ts

Priority: [low|medium|high|critical]
```

### Quality Assurance Best Practices (30 minutes)

**Code Quality:**
1. **Standards Compliance**: Follow project coding standards
2. **Test Coverage**: Maintain high test coverage
3. **Documentation**: Keep documentation updated
4. **Security**: Follow security best practices
5. **Performance**: Consider performance implications

**Review Process:**
1. **Self-Review**: Review own code before submission
2. **Peer Review**: Have code reviewed by peers
3. **Automated Checks**: Run automated quality checks
4. **Validation**: Validate against acceptance criteria
5. **Documentation**: Ensure documentation is complete

### Cost Management Best Practices (30 minutes)

**Cost-Effective Usage:**
1. **Model Selection**: Choose appropriate models for tasks
2. **Task Optimization**: Optimize task descriptions and context
3. **Batch Processing**: Group similar tasks together
4. **Caching**: Implement caching where appropriate
5. **Monitoring**: Monitor costs regularly

**Budget Management:**
1. **Budget Planning**: Set realistic budgets
2. **Cost Tracking**: Track costs by component
3. **Alerting**: Set up cost alerts
4. **Optimization**: Continuously optimize costs
5. **Reporting**: Report on cost efficiency

## Hands-on Labs

### Lab 1: System Setup and Configuration (45 minutes)

**Objectives:**
- Set up development environment
- Configure agent roles
- Verify system operation
- Create first task

**Steps:**
1. **Environment Setup**
```bash
# Clone and setup
git clone <repository>
cd kyros-praxis
cp .env.example .env
# Configure environment variables
```

2. **Service Startup**
```bash
# Start infrastructure
docker-compose up -d

# Start development environment
./run-dev.sh

# Verify operation
curl http://localhost:3000/api/health
curl http://localhost:8000/healthz
```

3. **Configuration**
```bash
# Review agent configuration
cat .claude/custom_modes.yml

# Validate configuration
python scripts/validate_config.py

# Test escalation rules
python scripts/test_escalation_rules.py
```

4. **First Task**
```bash
# Create simple task
python scripts/submit_task.py \
  --role implementer \
  --title "Test setup" \
  --description "Verify system is working correctly"
```

### Lab 2: Agent Role Workflow (60 minutes)

**Objectives:**
- Use all agent roles appropriately
- Coordinate multi-agent workflow
- Monitor task progress
- Validate results

**Scenario:**
Implement a simple user management feature

**Steps:**
1. **Architect Phase**
```bash
# Create architectural plan
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "architect", "title": "Design user management API"}'
```

2. **Implementer Phase**
```bash
# Implement feature
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "implementer", "title": "Implement user management endpoints"}'
```

3. **Critic Phase**
```bash
# Review implementation
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "critic", "title": "Review user management implementation"}'
```

4. **Integrator Phase**
```bash
# Coordinate merge
curl -X POST http://localhost:8000/collab/tasks \
  -d '{"role": "integrator", "title": "Merge user management feature"}'
```

### Lab 3: Escalation Scenarios (45 minutes)

**Objectives:**
- Understand escalation triggers
- Practice manual escalation
- Monitor escalation results
- Optimize escalation usage

**Scenarios:**
1. **Security Critical Task**
2. **Complex Architecture Decision**
3. **Multi-Service Integration**
4. **Performance Optimization**

**Exercise:**
```bash
# Test escalation scenarios
python scripts/test_escalation_scenarios.py

# Create escalation request
curl -X POST http://localhost:8000/v1/escalation/submit \
  -d '{
    "task_description": "Implement OAuth2 with SSO integration",
    "files_to_modify": ["auth.py", "security/"],
    "justification": "Security-critical authentication system"
  }'

# Analyze results
python scripts/analyze_escalation_results.py
```

### Lab 4: Performance Optimization (45 minutes)

**Objectives:**
- Identify performance bottlenecks
- Implement optimizations
- Measure improvements
- Document results

**Steps:**
1. **Performance Analysis**
```bash
# Analyze current performance
python scripts/performance_analysis.py

# Identify bottlenecks
python scripts/identify_bottlenecks.py
```

2. **Optimization Implementation**
```bash
# Implement optimizations
python scripts/implement_optimizations.py

# Test improvements
python scripts/test_optimizations.py
```

3. **Results Documentation**
```bash
# Document results
python scripts/document_optimization_results.py

# Create performance report
python scripts/performance_report.py
```

### Lab 5: Incident Response (60 minutes)

**Objectives:**
- Handle system incidents
- Follow incident response procedures
- Communicate effectively
- Document incidents

**Scenarios:**
1. **System Outage**
2. **Performance Degradation**
3. **Security Incident**
4. **Data Corruption**

**Exercise:**
```bash
# Simulate incident
python scripts/simulate_incident.py --type outage

# Respond to incident
python scripts/respond_to_incident.py

# Document incident
python scripts/document_incident.py

# Review procedures
python scripts/review_incident_response.py
```

## Assessment and Certification

### Knowledge Assessment

**Multiple Choice Questions:**
1. What percentage of tasks should GLM-4.5 handle?
   a) 50%
   b) 75%
   c) 95%
   d) 100%

2. When should you escalate to Claude 4.1 Opus?
   a) For all tasks
   b) For complex architectural decisions
   c) Only for security tasks
   d) Never

3. What is the maximum recommended diff size?
   a) 100 LOC
   b) 200 LOC
   c) 500 LOC
   d) No limit

**Practical Exercises:**
1. Create a complete workflow using all agent roles
2. Implement and review a simple feature
3. Handle an incident scenario
4. Optimize system performance

### Certification Levels

**Kyros Certified User (KCU):**
- Basic system usage
- Understanding of agent roles
- Task creation and management
- Basic troubleshooting

**Kyros Certified Professional (KCP):**
- Advanced system usage
- Escalation management
- Performance optimization
- Incident response

**Kyros Certified Expert (KCE):**
- System architecture
- Advanced operations
- Training and mentoring
- System optimization

### Continuing Education

**Recertification:**
- Annual recertification required
- Continuing education credits
- Practical assessment
- Updated system knowledge

**Advanced Training:**
- System architecture deep dive
- Advanced operations
- Security specialization
- Performance optimization

---

## Training Resources

**Documentation:**
- User Guide: `/docs/user-guide/`
- Operations Manual: `/docs/operations/`
- API Documentation: `/docs/api/`
- FAQ: `/docs/faq.md`

**Tools and Scripts:**
- Training scripts: `/scripts/training/`
- Lab exercises: `/scripts/labs/`
- Assessment tools: `/scripts/assessment/`
- Demo data: `/data/training/`

**Support:**
- Training coordinator: training@kyros.com
- Technical support: support@kyros.com
- Community forum: https://forum.kyros.com
- Knowledge base: https://kb.kyros.com