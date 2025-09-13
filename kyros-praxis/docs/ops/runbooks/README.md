# Operations Runbooks

This directory contains operational runbooks and procedures for managing the Kyros Praxis platform in production environments.

## 📚 Available Runbooks

### Deployment Runbooks
- [Deployment Guide](../deployment/deployment-guide.md) - Step-by-step deployment procedures
- [Rollback Procedures](../deployment/rollback.md) - Service rollback and recovery
- [Blue-Green Deployment](../deployment/blue-green.md) - Zero-downtime deployment strategies

### Incident Response Runbooks
- [Incident Response](../incident-response/README.md) - General incident handling procedures
- [Service Outages](../incident-response/service-outage.md) - Handling service failures
- [Performance Degradation](../incident-response/performance.md) - Performance issue resolution
- [Security Incidents](../incident-response/security.md) - Security breach response

### Maintenance Runbooks
- [System Maintenance](../maintenance/system-maintenance.md) - Scheduled maintenance procedures
- [Database Maintenance](../maintenance/database.md) - Database operations and optimization
- [Backup & Recovery](../maintenance/backup-restore.md) - Data backup and restoration

### Monitoring & Observability
- [Monitoring Setup](../monitoring/setup.md) - Monitoring system configuration
- [Alert Management](../monitoring/alerts.md) - Alert configuration and management
- [Log Management](../monitoring/logging.md) - Log aggregation and analysis

### Testing Runbooks
- [Testing Guide](testing.md) - Comprehensive testing procedures and DoD

## 🔧 Quick Reference

### Emergency Contacts
- **On-call Engineer**: oncall@kyros-praxis.com
- **Security Team**: security@kyros-praxis.com
- **Infrastructure Team**: infra@kyros-praxis.com

### Critical Commands
```bash
# Health check all services
./scripts/health-check.sh

# Restart all services
docker-compose restart

# View logs
docker-compose logs -f [service-name]

# Emergency stop
docker-compose down
```

### Status Dashboard
- **Production Status**: https://status.kyros-praxis.com
- **Internal Metrics**: https://metrics.kyros-praxis.com
- **Log Aggregation**: https://logs.kyros-praxis.com

## 🚨 Incident Response SLA

| Severity | Response Time | Resolution Time | Escalation |
|----------|---------------|-----------------|-------------|
| SEV-0 (Critical) | 15 minutes | 1 hour | Immediately |
| SEV-1 (High) | 30 minutes | 4 hours | 1 hour |
| SEV-2 (Medium) | 1 hour | 8 hours | 4 hours |
| SEV-3 (Low) | 4 hours | 24 hours | Next business day |

## 📋 Maintenance Windows

### Scheduled Maintenance
- **Weekly**: Sunday 2:00 AM - 4:00 AM UTC
- **Monthly**: First Sunday of month, full system maintenance
- **Quarterly**: Major version updates and infrastructure upgrades

### Change Freeze Periods
- **Holiday Season**: December 15 - January 5
- **Major Events**: During high-traffic periods (TBD)
- **Financial Year End**: As determined by finance team

## 🔄 Runbook Execution Process

1. **Assessment**: Evaluate situation and severity
2. **Communication**: Notify stakeholders via appropriate channels
3. **Execution**: Follow runbook procedures precisely
4. **Documentation**: Record actions taken and outcomes
5. **Review**: Conduct post-incident review
6. **Improvement**: Update runbooks based on lessons learned

## 📞 Support Channels

- **Slack**: #kyros-operations (primary), #kyros-alerts (critical)
- **Email**: operations@kyros-praxis.com
- **Phone**: Emergency contact list in internal wiki
- **PagerDuty**: On-call rotation management

## 🔗 Additional Resources

- [Architecture Overview](../../architecture/overview.md)
- [Security Guidelines](../../security/README.md)
- [API Documentation](../../api/README.md)
- [Internal Wiki](https://wiki.kyros-praxis.com)

