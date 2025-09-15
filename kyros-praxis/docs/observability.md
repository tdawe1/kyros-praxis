# Observability and Monitoring Configuration for kyros-praxis

## Overview

This document outlines the observability strategy for monitoring application performance, errors, and user behavior across all environments.

## Architecture

```
Application → OpenTelemetry → Collector → Backend (Sentry/Grafana)
           → Metrics → Prometheus → Grafana
           → Logs → Loki → Grafana
           → Traces → Jaeger → Grafana
```

## Components

### 1. Application Monitoring

#### Frontend (Next.js)
```javascript
// services/console/app/lib/monitoring.ts
import * as Sentry from '@sentry/nextjs'
import { BrowserTracing } from '@sentry/tracing'

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_APP_ENV,
  release: `kyros-praxis@${process.env.NEXT_PUBLIC_COMMIT_SHA}`,
  integrations: [new BrowserTracing()],
  tracesSampleRate: 0.1,
  beforeSend(event) {
    // Filter out sensitive data
    if (event.request && event.request.headers) {
      delete event.request.headers.authorization
      delete event.request.headers.cookie
    }
    return event
  }
})
```

#### Backend (FastAPI)
```python
# services/orchestrator/app/monitoring.py
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

# Configure OpenTelemetry
resource = Resource.create({
    "service.name": "kyros-praxis-api",
    "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    "service.version": os.getenv("COMMIT_SHA", "unknown")
})

tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)
tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")))
)

meter_provider = MeterProvider(resource=resource)
metrics.set_meter_provider(meter_provider)
```

### 2. Metrics Collection

#### Custom Metrics
```python
# API Response Time
request_duration = meter.create_histogram(
    "http.request.duration",
    description="HTTP request duration in seconds",
    unit="s"
)

# Active Users
active_users = meter.create_up_down_counter(
    "users.active",
    description="Number of active users"
)

# Agent Operations
agent_operations = meter.create_counter(
    "agent.operations.total",
    description="Total number of agent operations"
)
```

#### System Metrics
- CPU usage
- Memory consumption
- Disk I/O
- Network traffic
- Database connections

### 3. Logging Strategy

#### Structured Logging
```python
# services/orchestrator/app/logging.py
import structlog
import logging

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

#### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational information
- **WARNING**: Potentially harmful situations
- **ERROR**: Error events that might still allow continued operation
- **CRITICAL**: Very severe errors that might cause termination

### 4. Tracing

#### Distributed Tracing
```python
# services/orchestrator/app/tracing.py
from opentelemetry import trace
from opentelemetry.trace.span import Span

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("process_agent_request")
async def process_agent_request(request_data: dict) -> dict:
    # Processing logic here
    pass
```

### 5. Health Checks

#### API Health Endpoints
```python
# services/orchestrator/app/api/v1/utils/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..deps import get_db
from ...database import engine

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    try:
        # Check database connection
        db.execute("SELECT 1")
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
```

## Monitoring Dashboard Setup

### Grafana Dashboards

#### 1. System Health Dashboard
- CPU usage by service
- Memory usage by service
- Disk I/O operations
- Network traffic

#### 2. API Performance Dashboard
- Request rate and latency
- Error rates by endpoint
- Database query performance
- Cache hit ratios

#### 3. Business Metrics Dashboard
- Active users over time
- Agent operations completed
- Task execution times
- Success/failure rates

#### 4. Error Tracking Dashboard
- Error rates by environment
- Top error types
- Error distribution by user
- Error trends over time

## Alerting Configuration

### Critical Alerts
- **Service Down**: Any service unavailable for > 5 minutes
- **High Error Rate**: > 5% error rate for > 10 minutes
- **Database Connection**: Database unavailable for > 2 minutes
- **Memory Usage**: > 90% memory usage for > 5 minutes

### Warning Alerts
- **High Latency**: P95 latency > 2 seconds
- **Low Success Rate**: < 95% success rate for API calls
- **Queue Backlog**: Message queue growing for > 15 minutes
- **Disk Space**: < 20% free disk space

### Info Alerts
- **New Deployment**: Successful deployment detected
- **High Traffic**: Traffic spike detected
- **Performance Degradation**: Gradual performance decline

## Uptime Monitoring

### External Health Checks
```yaml
# uptime-kuma configuration
services:
  - name: Kyros Praxis Frontend
    url: https://app.kyros-praxis.com
    interval: 60
    notification: webhook
    
  - name: Kyros Praxis API
    url: https://api.kyros-praxis.com/health
    interval: 30
    notification: webhook
    
  - name: Terminal Daemon
    url: https://daemon.kyros-praxis.com/health
    interval: 60
    notification: webhook
```

## Deployment Integration

### Pre-deploy Checks
```bash
# scripts/ci/pre-deploy-checks.sh
#!/bin/bash

echo "🔍 Running pre-deploy health checks..."

# Check all services are healthy
curl -f https://api.kyros-praxis.com/health || exit 1
curl -f https://app.kyros-praxis.com/api/health || exit 1

# Check error rates are acceptable
ERROR_RATE=$(curl -s "https://api.kyros-praxis.com/metrics/error-rate" | jq '.rate')
if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
    echo "❌ Error rate too high: $ERROR_RATE"
    exit 1
fi

echo "✅ Pre-deploy checks passed"
```

### Post-deploy Validation
```bash
# scripts/ci/post-deploy-validation.sh
#!/bin/bash

echo "✅ Validating deployment..."

# Wait for services to be ready
sleep 30

# Check health endpoints
curl -f https://api.kyros-praxis.com/health || exit 1
curl -f https://app.kyros-praxis.com/api/health || exit 1

# Run smoke tests
npm run test:smoke

echo "✅ Deployment validation complete"
```

## Security Considerations

### Data Privacy
- **PII Filtering**: Automatically filter personally identifiable information from logs
- **Access Control**: Role-based access to monitoring data
- **Data Retention**: Configure appropriate retention periods

### Compliance
- **GDPR Compliance**: Ensure user data is properly handled
- **Audit Trails**: Maintain audit logs for all monitoring activities
- **Data Encryption**: Encrypt sensitive monitoring data at rest and in transit

## Implementation Checklist

### Phase 1: Basic Monitoring
- [ ] Set up Sentry for error tracking
- [ ] Configure basic health checks
- [ ] Implement structured logging
- [ ] Set up basic Grafana dashboards

### Phase 2: Advanced Observability
- [ ] Implement OpenTelemetry tracing
- [ ] Set up metrics collection
- [ ] Configure alerting rules
- [ ] Set up external monitoring

### Phase 3: Business Intelligence
- [ ] Implement business metrics
- [ ] Set up user behavior tracking
- [ ] Configure performance analytics
- [ ] Set up capacity planning

### Phase 4: Optimization
- [ ] Implement automated alerting
- [ ] Set up anomaly detection
- [ ] Configure predictive scaling
- [ ] Implement cost optimization