# Kyros Hybrid Model System - Operations Manual

## Table of Contents
- [System Architecture](#system-architecture)
- [Daily Operations](#daily-operations)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Maintenance Procedures](#maintenance-procedures)
- [Incident Response](#incident-response)
- [Performance Optimization](#performance-optimization)
- [Cost Management](#cost-management)
- [Security Procedures](#security-procedures)
- [Backup and Recovery](#backup-and-recovery)

## System Architecture

### Core Components

**Service Layer:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Console       │    │  Orchestrator   │    │ Terminal Daemon │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Node.js)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 8787    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   MCP Servers   │
                    │   (AI Models)   │
                    └─────────────────┘
```

**Data Layer:**
- **PostgreSQL**: Primary database for orchestration and state
- **Redis**: Caching and session management
- **File Storage**: Configuration files, logs, and artifacts

**AI Model Integration:**
- **GLM-4.5**: Universal default model (95% usage)
- **Claude 4.1 Opus**: Premium model for critical decisions (5% usage)
- **MCP Protocol**: Standardized interface for model communication

### Communication Patterns

**API Communication:**
```
Console → Orchestrator: REST API (HTTP/JSON)
Orchestrator → Agents: Internal message bus
Agents → MCP Servers: Model Context Protocol
Terminal Daemon → Agents: WebSocket (PTY sessions)
```

**Event Flow:**
```
User Request → Console → Orchestrator → Agent Selection → Model Processing → Response → User
```

## Daily Operations

### Morning Checklist (9:00 AM)

**System Health Check:**
```bash
# Check all services are running
docker-compose ps

# Health check endpoints
curl -f http://localhost:3000/api/health || echo "Console unhealthy"
curl -f http://localhost:8000/healthz || echo "Orchestrator unhealthy"
curl -f http://localhost:8787/health || echo "Terminal Daemon unhealthy"

# Check database connectivity
python scripts/check_db.py

# Verify MCP servers
./scripts/mcp-status.sh
```

**Performance Metrics Review:**
```bash
# Check response times
python scripts/performance_report.py --period 24h

# Review error rates
python scripts/error_analysis.py --period 24h

# Check model usage
python scripts/model_usage_report.py --period 24h

# Cost analysis
python scripts/cost_report.py --period 24h
```

**Alert Status:**
```bash
# Check active alerts
curl http://localhost:8000/v1/alerts/active

# Review resolved alerts
curl http://localhost:8000/v1/alerts/resolved?period=24h

# Alert response times
python scripts/alert_response_times.py
```

### Mid-Day Monitoring (12:00 PM, 3:00 PM)

**Resource Utilization:**
```bash
# System resources
docker stats --no-stream

# Database performance
python scripts/db_performance.py

# Memory usage
python scripts/memory_analysis.py

# Disk space
df -h
```

**Model Performance:**
```bash
# Model response times
curl http://localhost:8000/v1/models/performance

# Escalation rates
python scripts/escalation_rates.py

# Success rates by model
python scripts/model_success_rates.py

# Quality metrics
python scripts/quality_metrics.py
```

### End-of-Day Procedures (5:00 PM)

**Daily Reports:**
```bash
# Generate daily summary
python scripts/daily_summary.py

# Cost report
python scripts/cost_report.py --period 1d --output reports/daily_cost.md

# Performance report
python scripts/performance_report.py --period 1d --output reports/daily_performance.md

# Quality report
python scripts/quality_report.py --period 1d --output reports/daily_quality.md
```

**System Backup:**
```bash
# Database backup
python scripts/backup_db.py

# Configuration backup
python scripts/backup_config.py

# Logs backup
python scripts/backup_logs.py
```

## Monitoring and Alerting

### Monitoring Dashboard

**Key Metrics to Monitor:**

**System Health:**
- Service availability (>99.5%)
- Response times (<3s average)
- Error rates (<1%)
- Database latency (<100ms)

**Model Performance:**
- GLM-4.5 usage percentage (target: 95%)
- Claude 4.1 Opus escalation rate (target: <5%)
- Model response times
- Task success rates

**Cost Management:**
- Daily costs vs budget
- Cost per task by model
- ROI metrics
- Trend analysis

**Setup Monitoring:**
```bash
# Start monitoring dashboard
python scripts/start_dashboard.py

# Configure alerts
python scripts/configure_alerts.py --config monitoring/alerts.yml

# Test alert system
python scripts/test_alerts.py
```

### Alert Configuration

**Critical Alerts (Immediate Notification):**
- System downtime >5 minutes
- Error rate >5%
- Security incidents
- Data corruption detected

**Warning Alerts (Email/Slack):**
- Performance degradation
- Cost overruns >20%
- High escalation rates
- Low disk space

**Info Alerts (Daily Digest):**
- Cost summaries
- Performance trends
- Usage statistics

**Alert Configuration Example:**
```yaml
# monitoring/alerts.yml
alerts:
  system_down:
    condition: "services_unhealthy >= 2"
    severity: critical
    channels: [pagerduty, slack, email]
    cooldown: 300
    
  high_error_rate:
    condition: "error_rate > 0.05"
    severity: warning
    channels: [slack, email]
    cooldown: 600
    
  cost_overrun:
    condition: "daily_cost > budget * 1.2"
    severity: warning
    channels: [email]
    cooldown: 3600
    
  escalation_spike:
    condition: "escalation_rate > 0.1"
    severity: info
    channels: [slack]
    cooldown: 1800
```

## Maintenance Procedures

### Weekly Maintenance (Sundays 2:00 AM - 4:00 AM)

**System Updates:**
```bash
# Backup before maintenance
python scripts/pre_maintenance_backup.py

# Stop services
docker-compose down

# Update dependencies
cd services/console && npm update
cd services/orchestrator && pip update -r requirements.txt
cd services/terminal-daemon && npm update

# Apply database migrations
python scripts/run_migrations.py

# Restart services
docker-compose up -d

# Post-maintenance validation
python scripts/post_maintenance_check.py
```

**Performance Optimization:**
```bash
# Database optimization
python scripts/optimize_database.py

# Cache cleanup
python scripts/clear_cache.py

# Log rotation
python scripts/rotate_logs.py

# Index optimization
python scripts/optimize_indexes.py
```

### Monthly Maintenance (First Sunday of Month)

**Deep System Analysis:**
```bash
# Comprehensive performance analysis
python scripts/performance_analysis.py --period 30d

# Cost optimization analysis
python scripts/cost_optimization.py --period 30d

# Quality trends analysis
python scripts/quality_analysis.py --period 30d

# Security audit
python scripts/security_audit.py
```

**Configuration Review:**
```bash
# Review escalation rules
python scripts/review_escalation_rules.py

# Update model configurations
python scripts/update_model_configs.py

# Optimize alert thresholds
python scripts/optimize_alerts.py

# Update documentation
python scripts/update_docs.py
```

### Quarterly Maintenance

**Major System Updates:**
- Database schema upgrades
- Major dependency updates
- Infrastructure scaling review
- Security patching
- Performance tuning

**Capacity Planning:**
```bash
# Analyze growth trends
python scripts/growth_analysis.py --period 90d

# Capacity planning
python scripts/capacity_planning.py

# Resource optimization
python scripts/resource_optimization.py

# Budget planning
python scripts/budget_planning.py
```

## Incident Response

### Incident Classification

**Severity Levels:**

**SEV-0 (Critical):**
- Complete system outage
- Data loss or corruption
- Security breach
- Major financial impact

**SEV-1 (High):**
- Significant performance degradation
- Partial system outage
- High error rates
- Cost overruns

**SEV-2 (Medium):**
- Minor performance issues
- Feature unavailability
- Configuration issues
- User complaints

**SEV-3 (Low):**
- Documentation issues
- Minor bugs
- UI improvements
- Enhancement requests

### Incident Response Procedure

**Immediate Actions (First 5 Minutes):**
```bash
# Assess impact
python scripts/assess_impact.py

# Notify stakeholders
python scripts/notify_stakeholders.py --severity sev_level

# Start incident bridge
python scripts/start_incident_bridge.py

# Begin logging
python scripts/start_incident_logging.py
```

**Investigation (First 30 Minutes):**
```bash
# Gather diagnostics
python scripts/gather_diagnostics.py

# Check recent changes
python scripts/check_recent_changes.py

# Analyze logs
python scripts/analyze_logs.py --period 1h

# Identify root cause
python scripts/root_cause_analysis.py
```

**Resolution (Varies by Severity):**
```bash
# Implement fix
python scripts/implement_fix.py

# Test resolution
python scripts/test_resolution.py

# Deploy fix
python scripts/deploy_fix.py

# Monitor impact
python scripts/monitor_impact.py
```

**Post-Incident:**
```bash
# Complete incident report
python scripts/incident_report.py

# Update runbooks
python scripts/update_runbooks.py

# Schedule post-mortem
python scripts/schedule_post_mortem.py

# Implement preventive measures
python scripts/implement_preventive_measures.py
```

### Communication Templates

**Initial Notification:**
```
Subject: SEV-{level} Incident: {incident_title}

Impact: {description}
Affected Services: {services}
Current Status: {status}
Next Update: {time}
```

**Status Update:**
```
Subject: SEV-{level} Update: {incident_title}

Status: {current_status}
Progress: {progress_description}
ETA: {estimated_resolution}
Customer Impact: {impact_description}
```

**Resolution Notification:**
```
Subject: SEV-{level} Resolved: {incident_title}

Resolution Time: {duration}
Root Cause: {cause}
Resolution: {fix_description}
Preventive Measures: {prevention}
Post-Mortem Scheduled: {date}
```

## Performance Optimization

### Performance Monitoring

**Key Performance Indicators:**
- API response times (P50, P90, P99)
- Database query performance
- Model response times
- Memory and CPU utilization
- Network latency
- Task throughput

**Monitoring Commands:**
```bash
# Real-time performance monitoring
python scripts/performance_monitor.py --real-time

# Performance analysis
python scripts/performance_analysis.py --period 24h

# Bottleneck identification
python scripts/identify_bottlenecks.py

# Optimization recommendations
python scripts/optimization_recommendations.py
```

### Optimization Strategies

**Database Optimization:**
```bash
# Query optimization
python scripts/optimize_queries.py

# Index optimization
python scripts/optimize_indexes.py

# Connection pool tuning
python scripts/tune_connection_pools.py

# Cache optimization
python scripts/optimize_cache.py
```

**Model Optimization:**
```bash
# Model usage optimization
python scripts/optimize_model_usage.py

# Escalation rule optimization
python scripts/optimize_escalation_rules.py

# Response time optimization
python scripts/optimize_response_times.py

# Cost-performance balance
python scripts/optimize_cost_performance.py
```

**Infrastructure Optimization:**
```bash
# Resource allocation optimization
python scripts/optimize_resources.py

# Network optimization
python scripts/optimize_network.py

# Load balancing optimization
python scripts/optimize_load_balancing.py

# Scaling optimization
python scripts/optimize_scaling.py
```

## Cost Management

### Cost Tracking

**Cost Components:**
- AI model usage (GLM-4.5, Claude 4.1 Opus)
- Infrastructure costs (compute, storage, network)
- Operational costs (monitoring, alerting, backups)
- Maintenance costs (updates, patches, optimizations)

**Cost Monitoring:**
```bash
# Daily cost report
python scripts/cost_report.py --period 1d

# Cost trends analysis
python scripts/cost_trends.py --period 30d

# Cost breakdown by component
python scripts/cost_breakdown.py --period 7d

# ROI calculation
python scripts/roi_calculation.py
```

### Cost Optimization

**Cost Reduction Strategies:**
- Optimize model selection (maximize GLM-4.5 usage)
- Implement intelligent caching
- Optimize infrastructure utilization
- Reduce unnecessary escalations
- Implement cost-aware scheduling

**Optimization Commands:**
```bash
# Cost optimization analysis
python scripts/cost_optimization.py

# Model usage optimization
python scripts/optimize_model_usage.py

# Infrastructure cost optimization
python scripts/optimize_infrastructure_costs.py

# Budget optimization
python scripts/optimize_budget.py
```

### Budget Management

**Budget Planning:**
```bash
# Monthly budget planning
python scripts/budget_planning.py --month current

# Quarterly budget review
python scripts/budget_review.py --period 3m

# Annual budget forecasting
python scripts/budget_forecast.py --period 1y

# Cost allocation
python scripts/cost_allocation.py
```

**Budget Alerting:**
```bash
# Budget monitoring
python scripts/budget_monitor.py

# Budget alerts
python scripts/budget_alerts.py

# Cost overrun prevention
python scripts/prevent_cost_overrun.py
```

## Security Procedures

### Security Monitoring

**Security Metrics:**
- Authentication success/failure rates
- Authorization violations
- API security incidents
- Data access patterns
- Encryption compliance
- Vulnerability scan results

**Monitoring Commands:**
```bash
# Security monitoring
python scripts/security_monitor.py

# Authentication analysis
python scripts/auth_analysis.py

# Authorization audit
python scripts/auth_audit.py

# Vulnerability scanning
python scripts/vulnerability_scan.py
```

### Incident Response

**Security Incident Response:**
```bash
# Security incident detection
python scripts/detect_security_incident.py

# Incident containment
python scripts/contain_security_incident.py

# Incident investigation
python scripts/investigate_security_incident.py

# Incident resolution
python scripts/resolve_security_incident.py
```

### Compliance Management

**Compliance Monitoring:**
```bash
# Compliance checking
python scripts/compliance_check.py

# Audit trail monitoring
python scripts/audit_trail_monitor.py

# Data protection monitoring
python scripts/data_protection_monitor.py

# Regulatory compliance
python scripts/regulatory_compliance.py
```

## Backup and Recovery

### Backup Procedures

**Backup Types:**
- **Full Backups**: Complete system state (daily)
- **Incremental Backups**: Changes since last backup (hourly)
- **Configuration Backups**: System configuration (before changes)
- **Database Backups**: Database state (every 6 hours)

**Backup Commands:**
```bash
# Full system backup
python scripts/full_backup.py

# Incremental backup
python scripts/incremental_backup.py

# Configuration backup
python scripts/config_backup.py

# Database backup
python scripts/database_backup.py
```

### Recovery Procedures

**Recovery Scenarios:**

**Partial System Recovery:**
```bash
# Restore specific service
python scripts/restore_service.py --service orchestrator

# Restore configuration
python scripts/restore_config.py --timestamp 2024-01-15-10:00

# Restore database
python scripts/restore_database.py --backup 2024-01-15-10:00
```

**Complete System Recovery:**
```bash
# Disaster recovery
python scripts/disaster_recovery.py

# Data center failover
python scripts/datacenter_failover.py

# Cloud migration
python scripts/cloud_migration.py
```

### Testing

**Backup Testing:**
```bash
# Test backup integrity
python scripts/test_backup_integrity.py

# Test recovery procedures
python scripts/test_recovery.py

# Test disaster recovery
python scripts/test_disaster_recovery.py

# Test backup performance
python/scripts/test_backup_performance.py
```

---

## Contact Information

**Primary Contacts:**
- System Administrator: admin@kyros.com
- Database Administrator: dba@kyros.com
- Security Officer: security@kyros.com
- Network Administrator: network@kyros.com

**Emergency Contacts:**
- Critical Incident: pagerduty@kyros.com
- Security Incident: security-emergency@kyros.com
- Data Center Issues: datacenter@kyros.com

**Documentation:**
- Runbooks: `/docs/runbooks/`
- Configuration: `/etc/kyros/`
- Logs: `/var/log/kyros/`
- Backups: `/backups/kyros/`

**Support Channels:**
- Internal Wiki: `https://wiki.kyros.com`
- Slack Channel: `#kyros-ops`
- Jira Board: `https://kyros.atlassian.net`
- Monitoring Dashboard: `https://monitor.kyros.com`