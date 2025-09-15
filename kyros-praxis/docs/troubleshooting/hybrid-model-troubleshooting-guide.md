# Kyros Hybrid Model System - Troubleshooting Guide

## Table of Contents
- [Common Issues and Solutions](#common-issues-and-solutions)
- [Service-Specific Issues](#service-specific-issues)
- [Model and Escalation Issues](#model-and-escalation-issues)
- [Performance Issues](#performance-issues)
- [Security Issues](#security-issues)
- [Cost and Billing Issues](#cost-and-billing-issues)
- [Debugging Tools and Techniques](#debugging-tools-and-techniques)
- [Emergency Procedures](#emergency-procedures)
- [Contact Support](#contact-support)

## Common Issues and Solutions

### System Startup Issues

**Problem: Services fail to start**
```bash
# Symptom: docker-compose up fails with errors
docker-compose up -d
ERROR: Container orchestration failed

# Solutions:
1. Check Docker and Docker Compose installation
docker --version
docker-compose --version

2. Check system resources
docker info
free -h
df -h

3. Check port availability
netstat -tlnp | grep :3000
netstat -tlnp | grep :8000

4. Clean up existing containers
docker-compose down -v
docker system prune -f

5. Restart services
docker-compose up -d
```

**Problem: Environment variables not loaded**
```bash
# Symptom: Services complain about missing environment variables
ERROR: Missing required environment variable: DATABASE_URL

# Solutions:
1. Verify .env file exists
ls -la .env*

2. Check .env file format
cat .env

3. Set environment variables manually
export DATABASE_URL="postgresql://user:pass@localhost:5432/kyros"
export REDIS_URL="redis://localhost:6379"

4. Restart services with environment
docker-compose up -d --env-file .env
```

### Database Connectivity Issues

**Problem: Cannot connect to PostgreSQL**
```bash
# Symptom: Database connection errors
ERROR: Could not connect to PostgreSQL server

# Solutions:
1. Check PostgreSQL service status
docker-compose ps postgres
docker-compose logs postgres

2. Verify database is running
docker-compose exec postgres psql -U kyros -d kyros -c "SELECT 1"

3. Check connection string
echo $DATABASE_URL

4. Test connectivity
docker-compose exec orchestrator python -c "
from database import get_db
db = next(get_db())
print('Database connection successful')
"

5. Restart database service
docker-compose restart postgres
```

**Problem: Database migration errors**
```bash
# Symptom: Migration scripts fail
ERROR: Migration failed: relation already exists

# Solutions:
1. Check migration status
docker-compose exec orchestrator python -m alembic current
docker-compose exec orchestrator python -m alembic history

2. Clean database and restart migrations
docker-compose exec postgres psql -U kyros -d kyros -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

3. Run migrations manually
docker-compose exec orchestrator python -m alembic upgrade head

4. Check for migration conflicts
docker-compose exec orchestrator python -m alembic check
```

### Network and Connectivity Issues

**Problem: Services cannot communicate**
```bash
# Symptom: Connection refused errors between services
ERROR: Connection refused: http://orchestrator:8000

# Solutions:
1. Check network configuration
docker network ls
docker network inspect kyros_default

2. Verify service discovery
docker-compose exec orchestrator curl http://console:3000/api/health
docker-compose exec console curl http://orchestrator:8000/healthz

3. Check DNS resolution
docker-compose exec orchestrator nslookup console
docker-compose exec orchestrator nslookup postgres

4. Restart network
docker-compose down
docker network prune
docker-compose up -d
```

**Problem: External API connectivity issues**
```bash
# Symptom: Cannot reach AI model APIs
ERROR: Failed to connect to AI model provider

# Solutions:
1. Check internet connectivity
docker-compose exec orchestrator curl -I https://api.anthropic.com
docker-compose exec orchestrator curl -I https://api.openai.com

2. Verify API keys
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

3. Check proxy settings (if applicable)
echo $HTTP_PROXY
echo $HTTPS_PROXY

4. Test API connectivity
docker-compose exec orchestrator python -c "
import requests
response = requests.get('https://api.anthropic.com/v1/models', 
    headers={'Authorization': f'Bearer {ANTHROPIC_API_KEY}'})
print(f'Status: {response.status_code}')
"
```

## Service-Specific Issues

### Console Service Issues

**Problem: Console UI not loading**
```bash
# Symptom: Browser shows blank page or loading spinner
GET http://localhost:3000/ - ERR_EMPTY_RESPONSE

# Solutions:
1. Check console service status
docker-compose ps console
docker-compose logs console

2. Verify service is running
curl -I http://localhost:3000

3. Check Next.js build
docker-compose exec console npm run build

4. Clear Next.js cache
docker-compose exec console rm -rf .next
docker-compose restart console

5. Check environment variables
docker-compose exec console env | grep NEXT_
```

**Problem: Console API calls failing**
```bash
# Symptom: API calls from console return errors
ERROR: Network Error when connecting to orchestrator

# Solutions:
1. Check API endpoint configuration
docker-compose exec console cat .env.local | grep NEXT_PUBLIC_ADK_URL

2. Test connectivity to orchestrator
docker-compose exec console curl http://orchestrator:8000/healthz

3. Check CORS configuration
docker-compose exec orchestrator cat main.py | grep cors

4. Verify authentication
docker-compose exec console curl -H "Authorization: Bearer $TOKEN" http://orchestrator:8000/collab/tasks
```

### Orchestrator Service Issues

**Problem: Orchestrator not processing tasks**
```bash
# Symptom: Tasks created but not processed
curl http://localhost:8000/collab/tasks/queue
{"tasks": [], "processing": false}

# Solutions:
1. Check orchestrator logs
docker-compose logs orchestrator

2. Verify database connection
docker-compose exec orchestrator python -c "
from database import get_db
db = next(get_db())
print('Database OK')
"

3. Check task queue status
docker-compose exec orchestrator python -c "
from tasks import get_task_queue
queue = get_task_queue()
print(f'Queue size: {len(queue)}')
"

4. Restart orchestrator service
docker-compose restart orchestrator

5. Check for locked tasks
docker-compose exec orchestrator python -c "
from database import SessionLocal
from models import Task
with SessionLocal() as db:
    locked = db.query(Task).filter(Task.status == 'processing').all()
    print(f'Locked tasks: {len(locked)}')
"
```

**Problem: WebSocket connections failing**
```bash
# Symptom: WebSocket connection errors
ERROR: WebSocket connection failed: 1006

# Solutions:
1. Check WebSocket service status
docker-compose ps terminal-daemon
docker-compose logs terminal-daemon

2. Verify WebSocket endpoint
curl -I http://localhost:8787

3. Test WebSocket connection
docker-compose exec console npm run test:websocket

4. Check authentication
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me

5. Restart WebSocket service
docker-compose restart terminal-daemon
```

### Terminal Daemon Issues

**Problem: Terminal sessions not starting**
```bash
# Symptom: Terminal sessions fail to initialize
ERROR: Failed to start PTY session

# Solutions:
1. Check terminal daemon status
docker-compose logs terminal-daemon

2. Verify node-pty installation
docker-compose exec terminal-daemon npm list node-pty

3. Test PTY functionality
docker-compose exec terminal-daemon node -e "
const pty = require('node-pty');
console.log('PTY module OK');
"

4. Check permissions
docker-compose exec terminal-daemon ls -la /dev/ptmx

5. Restart terminal daemon
docker-compose restart terminal-daemon
```

## Model and Escalation Issues

### GLM-4.5 Model Issues

**Problem: GLM-4.5 model not responding**
```bash
# Symptom: Model calls timeout or fail
ERROR: Model request timeout after 30 seconds

# Solutions:
1. Check model configuration
curl http://localhost:8000/v1/models/status

2. Verify API connectivity
curl -H "Authorization: Bearer $GLM_API_KEY" https://api.glm.ai/v1/models

3. Test model directly
docker-compose exec orchestrator python -c "
from models.glm import GLMModel
model = GLMModel()
response = model.generate('Test prompt')
print(f'Response: {len(response)} chars')
"

4. Check rate limits
docker-compose exec orchestrator python -c "
from models.glm import GLMModel
model = GLMModel()
limits = model.get_rate_limits()
print(f'Rate limits: {limits}')
"

5. Restart model service
docker-compose restart orchestrator
```

**Problem: GLM-4.5 response quality issues**
```bash
# Symptom: Poor quality or irrelevant responses

# Solutions:
1. Check prompt configuration
docker-compose exec orchestrator cat config/prompts/glm-4.5.yml

2. Verify temperature settings
docker-compose exec orchestrator python -c "
from models.glm import GLMModel
model = GLMModel()
print(f'Temperature: {model.temperature}')
"

3. Test with different prompts
docker-compose exec orchestrator python -c "
from models.glm import GLMModel
model = GLMModel()
test_prompts = [
    'Write a simple function',
    'Explain this concept briefly',
    'Generate a list of items'
]
for prompt in test_prompts:
    response = model.generate(prompt)
    print(f'Prompt: {prompt[:20]}... -> Response: {len(response)} chars')
"

4. Update model configuration
docker-compose exec orchestrator python scripts/update_model_config.py --model glm-4.5
```

### Claude 4.1 Opus Escalation Issues

**Problem: Escalation not triggering**
```bash
# Symptom: Critical tasks not escalating to Claude 4.1 Opus
curl http://localhost:8000/v1/escalation/statistics
{"escalation_rate": 0.0}

# Solutions:
1. Check escalation configuration
curl http://localhost:8000/v1/escalation/config

2. Test escalation triggers
docker-compose exec orchestrator python scripts/test_escalation_triggers.py

3. Verify escalation criteria
docker-compose exec orchestrator python -c "
from escalation.criteria import EscalationCriteria
criteria = EscalationCriteria()
print(f'Criteria: {criteria.criteria}')
"

4. Check escalation logs
docker-compose logs orchestrator | grep escalation

5. Test manual escalation
curl -X POST http://localhost:8000/v1/escalation/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Critical security implementation",
    "justification": "Security-critical task requiring premium model"
  }'
```

**Problem: Escalation costs too high**
```bash
# Symptom: Escalation rate exceeds budget
curl http://localhost:8000/v1/escalation/statistics
{"escalation_rate": 0.15, "daily_cost": 150.0}

# Solutions:
1. Review escalation rules
docker-compose exec orchestrator python scripts/review_escalation_rules.py

2. Tighten escalation criteria
docker-compose exec orchestrator python scripts/tighten_escalation_criteria.py

3. Monitor escalation patterns
docker-compose exec orchestrator python scripts/analyze_escalation_patterns.py

4. Implement cost controls
docker-compose exec orchestrator python scripts/implement_cost_controls.py

5. Set budget alerts
docker-compose exec orchestrator python scripts/set_budget_alerts.py
```

### Model Selection Issues

**Problem: Wrong model selected for task**
```bash
# Symptom: Simple tasks using expensive models

# Solutions:
1. Check model selection logic
docker-compose exec orchestrator python -c "
from model_selection import select_model
print('Model selection logic loaded')
"

2. Review task classification
docker-compose exec orchestrator python scripts/review_task_classification.py

3. Test model selection
docker-compose exec orchestrator python -c "
from model_selection import select_model
task = {'description': 'Simple bug fix', 'complexity': 'low'}
model = select_model(task)
print(f'Selected model: {model}')
"

4. Update selection rules
docker-compose exec orchestrator python scripts/update_model_selection_rules.py

5. Monitor selection accuracy
docker-compose exec orchestrator python scripts/monitor_model_selection.py
```

## Performance Issues

### Slow Response Times

**Problem: High API response times**
```bash
# Symptom: API calls taking >3 seconds
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/healthz
time_namelookup: 0.001
time_connect: 0.002
time_appconnect: 0.003
time_pretransfer: 0.004
time_redirect: 0.000
time_starttransfer: 5.234  # <-- High
time_total: 5.235

# Solutions:
1. Identify bottleneck
docker-compose exec orchestrator python scripts/identify_bottlenecks.py

2. Check database queries
docker-compose exec orchestrator python scripts/analyze_db_queries.py

3. Monitor resource usage
docker stats orchestrator

4. Optimize configuration
docker-compose exec orchestrator python scripts/optimize_performance.py

5. Scale services
docker-compose up -d --scale orchestrator=2
```

**Problem: High memory usage**
```bash
# Symptom: Services consuming excessive memory
docker stats --no-stream
CONTAINER ID   NAME          CPU %     MEM USAGE / LIMIT     MEM %
abc123def456   orchestrator  15.2%     1.2GiB / 2GiB        60.0%  # <-- High

# Solutions:
1. Check memory leaks
docker-compose exec orchestrator python scripts/check_memory_leaks.py

2. Monitor memory patterns
docker-compose exec orchestrator python scripts/monitor_memory.py

3. Optimize memory usage
docker-compose exec orchestrator python scripts/optimize_memory.py

4. Restart service
docker-compose restart orchestrator

5. Increase memory limits
docker-compose up -d --memory-orchestrator=4g
```

### Database Performance Issues

**Problem: Slow database queries**
```bash
# Symptom: Database queries taking >100ms
docker-compose exec orchestrator python scripts/analyze_db_queries.py
Slow query (250ms): SELECT * FROM tasks WHERE status = 'processing'

# Solutions:
1. Add database indexes
docker-compose exec orchestrator python scripts/add_indexes.py

2. Optimize queries
docker-compose exec orchestrator python scripts/optimize_queries.py

3. Use connection pooling
docker-compose exec orchestrator python scripts/tune_connection_pool.py

4. Implement caching
docker-compose exec orchestrator python scripts/implement_caching.py

5. Consider read replicas
docker-compose up -d --scale postgres=2
```

**Problem: Database connection issues**
```bash
# Symptom: Connection pool exhaustion
ERROR: connection pool exhausted

# Solutions:
1. Check connection pool status
docker-compose exec orchestrator python scripts/check_connection_pool.py

2. Increase pool size
docker-compose exec orchestrator python scripts/increase_pool_size.py

3. Implement connection reuse
docker-compose exec orchestrator python scripts/implement_connection_reuse.py

4. Monitor connection patterns
docker-compose exec orchestrator python scripts/monitor_connections.py

5. Restart database
docker-compose restart postgres
```

## Security Issues

### Authentication Issues

**Problem: JWT token validation failing**
```bash
# Symptom: Authentication errors with JWT tokens
ERROR: Invalid token: signature verification failed

# Solutions:
1. Check JWT secret
echo $JWT_SECRET

2. Verify token generation
docker-compose exec orchestrator python -c "
from auth import create_access_token
token = create_access_token(data={'sub': 'test'})
print(f'Token created: {len(token)} chars')
"

3. Test token validation
docker-compose exec orchestrator python -c "
from auth import verify_token
token = 'test.token.here'
try:
    payload = verify_token(token)
    print('Token valid')
except Exception as e:
    print(f'Token invalid: {e}')
"

4. Check token expiration
docker-compose exec orchestrator python -c "
from auth import ACCESS_TOKEN_EXPIRE_MINUTES
print(f'Token expires in: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes')
"

5. Update JWT configuration
docker-compose exec orchestrator python scripts/update_jwt_config.py
```

**Problem: OAuth2 integration issues**
```bash
# Symptom: OAuth2 authentication flow failing
ERROR: OAuth2 callback failed: invalid_client

# Solutions:
1. Check OAuth2 configuration
docker-compose exec orchestrator cat config/oauth2.yml

2. Verify client credentials
echo $OAUTH2_CLIENT_ID
echo $OAUTH2_CLIENT_SECRET

3. Test OAuth2 endpoints
curl https://oauth2-provider.com/.well-known/openid-configuration

4. Check redirect URIs
docker-compose exec orchestrator python scripts/check_oauth2_redirects.py

5. Update OAuth2 configuration
docker-compose exec orchestrator python scripts/update_oauth2_config.py
```

### Authorization Issues

**Problem: Permission denied errors**
```bash
# Symptom: API calls returning 403 Forbidden
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/admin/users
HTTP/1.1 403 Forbidden

# Solutions:
1. Check user permissions
docker-compose exec orchestrator python -c "
from auth import get_current_user
from database import get_db
user = get_current_user('test_token')
print(f'User permissions: {user.permissions}')
"

2. Verify role assignments
docker-compose exec orchestrator python scripts/check_user_roles.py

3. Test authorization middleware
docker-compose exec orchestrator python scripts/test_auth_middleware.py

4. Update role permissions
docker-compose exec orchestrator python scripts/update_role_permissions.py

5. Check for permission caching
docker-compose exec orchestrator python scripts/clear_permission_cache.py
```

### Security Vulnerabilities

**Problem: Security scan detects vulnerabilities**
```bash
# Symptom: Security scanner reports issues
Vulnerability: SQL injection in user search endpoint
Severity: High

# Solutions:
1. Review affected code
docker-compose exec orchestrator cat services/orchestrator/routers/users.py

2. Implement parameterized queries
docker-compose exec orchestrator python scripts/fix_sql_injection.py

3. Add input validation
docker-compose exec orchestrator python scripts/add_input_validation.py

4. Test security fixes
docker-compose exec orchestrator python scripts/test_security_fixes.py

5. Run security scan again
docker-compose exec orchestrator python scripts/run_security_scan.py
```

## Cost and Billing Issues

### Unexpected High Costs

**Problem: Monthly costs exceed budget**
```bash
# Symptom: Cost report shows overruns
python scripts/cost_report.py --period 30d
Monthly cost: $1,250.00 (Budget: $1,000.00)
Overrun: 25.0%

# Solutions:
1. Analyze cost breakdown
python scripts/cost_breakdown.py --period 30d

2. Identify cost drivers
python scripts/identify_cost_drivers.py

3. Implement cost controls
python scripts/implement_cost_controls.py

4. Set spending alerts
python scripts/set_spending_alerts.py

5. Optimize usage patterns
python scripts/optimize_usage_patterns.py
```

### Model Cost Optimization

**Problem: High model usage costs**
```bash
# Symptom: Model costs disproportionately high
python scripts/model_cost_report.py
GLM-4.5: $500.00 (50% of total)
Claude 4.1 Opus: $500.00 (50% of total)  # <-- Should be lower

# Solutions:
1. Review model selection
python scripts/review_model_selection.py

2. Optimize escalation criteria
python scripts/optimize_escalation_criteria.py

3. Implement model caching
python scripts/implement_model_caching.py

4. Batch similar requests
python scripts/implement_request_batching.py

5. Monitor cost per task
python scripts/monitor_cost_per_task.py
```

## Debugging Tools and Techniques

### Logging and Monitoring

**Enable Debug Logging:**
```bash
# Set debug level
export LOG_LEVEL=DEBUG

# View specific service logs
docker-compose logs -f orchestrator
docker-compose logs -f console

# Filter logs by component
docker-compose logs orchestrator | grep escalation
docker-compose logs orchestrator | grep model

# View structured logs
docker-compose logs orchestrator | jq '.'
```

**Performance Monitoring:**
```bash
# Monitor performance metrics
python scripts/performance_monitor.py

# Track response times
python scripts/response_time_tracker.py

# Monitor resource usage
python scripts/resource_monitor.py

# Analyze performance trends
python scripts/performance_analysis.py
```

### Debug Scripts

**Database Debugging:**
```bash
# Check database connections
python scripts/debug_db_connections.py

# Analyze query performance
python scripts/debug_queries.py

# Check database locks
python scripts/debug_db_locks.py

# Verify data integrity
python scripts/debug_data_integrity.py
```

**Model Debugging:**
```bash
# Test model connectivity
python scripts/debug_model_connectivity.py

# Analyze model responses
python scripts/debug_model_responses.py

# Check model selection
python scripts/debug_model_selection.py

# Verify escalation logic
python scripts/debug_escalation_logic.py
```

**Service Debugging:**
```bash
# Test service health
python scripts/debug_service_health.py

# Analyze service dependencies
python scripts/debug_service_dependencies.py

# Check service communication
python scripts/debug_service_communication.py

# Verify service configuration
python scripts/debug_service_config.py
```

### Interactive Debugging

**Python Debug Console:**
```bash
# Start debug console
docker-compose exec orchestrator python -i
>>> from models.glm import GLMModel
>>> model = GLMModel()
>>> response = model.generate("Test")
>>> print(response)
```

**Database Console:**
```bash
# Start database console
docker-compose exec postgres psql -U kyros -d kyros

# Check tables
\dt

# Query tasks
SELECT * FROM tasks LIMIT 10;

# Check performance
EXPLAIN ANALYZE SELECT * FROM tasks WHERE status = 'processing';
```

## Emergency Procedures

### System Outage Response

**Immediate Actions:**
```bash
# 1. Assess impact
python scripts/assess_impact.py

# 2. Notify stakeholders
python scripts/notify_stakeholders.py --severity critical

# 3. Start incident bridge
python scripts/start_incident_bridge.py

# 4. Begin logging
python scripts/start_incident_logging.py

# 5. Check all services
python scripts/emergency_health_check.py
```

**Service Recovery:**
```bash
# Restart all services
docker-compose down
docker-compose up -d

# Restore from backup (if needed)
python scripts/emergency_restore.py

# Verify system operation
python scripts/emergency_verification.py

# Monitor stability
python scripts/emergency_monitoring.py
```

### Data Recovery Procedures

**Database Recovery:**
```bash
# 1. Identify backup
python scripts/find_latest_backup.py

# 2. Stop database
docker-compose stop postgres

# 3. Restore backup
python scripts/restore_database.py --backup 2024-01-15-10:00

# 4. Start database
docker-compose start postgres

# 5. Verify data
python scripts/verify_data_integrity.py
```

**Configuration Recovery:**
```bash
# Restore configuration
python scripts/restore_config.py --timestamp 2024-01-15-10:00

# Verify configuration
python scripts/verify_config.py

# Restart services
docker-compose restart

# Test functionality
python scripts/test_system_functionality.py
```

### Security Incident Response

**Immediate Containment:**
```bash
# 1. Isolate affected systems
python scripts/isolate_systems.py

# 2. Change credentials
python scripts/rotate_credentials.py

# 3. Disable affected accounts
python scripts/disable_accounts.py

# 4. Preserve evidence
python scripts/preserve_evidence.py

# 5. Notify security team
python scripts/notify_security_team.py
```

**Investigation and Resolution:**
```bash
# 1. Analyze logs
python scripts/analyze_security_logs.py

# 2. Identify attack vector
python scripts/identify_attack_vector.py

# 3. Patch vulnerabilities
python scripts/patch_vulnerabilities.py

# 4. Verify fixes
python scripts/verify_security_fixes.py

# 5. Document incident
python scripts/document_security_incident.py
```

## Contact Support

### Support Channels

**Emergency Support:**
- **Critical Issues**: pagerduty@kyros.com
- **Security Incidents**: security-emergency@kyros.com
- **Production Outages**: production-emergency@kyros.com

**Standard Support:**
- **Technical Issues**: support@kyros.com
- **Documentation**: docs@kyros.com
- **Training**: training@kyros.com

**Community Support:**
- **Forum**: https://forum.kyros.com
- **Discord**: https://discord.gg/kyros
- **Stack Overflow**: https://stackoverflow.com/questions/tagged/kyros

### Support Information Needed

When contacting support, please provide:

1. **System Information:**
   - Kyros version
   - Operating system
   - Docker/Docker Compose versions
   - Python/Node.js versions

2. **Issue Description:**
   - Detailed problem description
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs

3. **Environment Details:**
   - Configuration files (redact sensitive data)
   - Environment variables (redact sensitive data)
   - Database version and size
   - Network configuration

4. **Troubleshooting Performed:**
   - Steps already taken
   - Results of diagnostics
   - Any temporary workarounds

### Bug Reporting

**Report Bugs:**
- GitHub Issues: https://github.com/kyros/kyros-praxis/issues
- Bug Template: Use provided bug report template
- Include reproduction steps
- Attach relevant logs and screenshots

**Feature Requests:**
- GitHub Discussions: https://github.com/kyros/kyros-praxis/discussions
- Feature Request Template: Use provided template
- Include use cases and requirements
- Provide examples and mockups

### Getting Help

**Self-Service Resources:**
- Documentation: `/docs/`
- API Reference: `/docs/api/`
- FAQ: `/docs/faq.md`
- Troubleshooting: `/docs/troubleshooting/`

**Community Resources:**
- Blog: https://blog.kyros.com
- Newsletter: https://newsletter.kyros.com
- YouTube Channel: https://youtube.com/kyros
- Twitter: https://twitter.com/kyros

**Professional Services:**
- Consulting: consulting@kyros.com
- Training: training@kyros.com
- Support Contracts: sales@kyros.com
- Enterprise: enterprise@kyros.com

---

## Quick Reference Commands

### Health Checks
```bash
# System health
curl http://localhost:8000/healthz
curl http://localhost:3000/api/health

# Service status
docker-compose ps

# Model status
curl http://localhost:8000/v1/models/status
```

### Common Fixes
```bash
# Restart services
docker-compose restart

# Clear cache
docker-compose exec orchestrator python scripts/clear_cache.py

# Reset database
docker-compose exec postgres psql -U kyros -d kyros -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Update configuration
docker-compose exec orchestrator python scripts/update_config.py
```

### Monitoring
```bash
# View logs
docker-compose logs -f [service]

# Monitor resources
docker stats

# Check costs
python scripts/cost_report.py

# Test performance
python scripts/performance_test.py
```