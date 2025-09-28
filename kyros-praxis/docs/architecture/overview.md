# Architecture Overview

This document provides a comprehensive overview of the Kyros Praxis architecture, including service composition, data flow, and design decisions.

## 🏗️ System Architecture

### High-Level Architecture

Kyros Praxis is designed as a microservices-based AI orchestration platform with the following core components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Console UI    │    │   Orchestrator  │    │ Service Registry│
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (FastAPI)     │
│   Port: 3001    │    │   Port: 8000    │    │   Port: 9000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Terminal Daemon │    │   PostgreSQL    │    │      Redis       │
│ (Node.js)       │    │   Port: 5432    │    │   Port: 6379    │
│ Port: 8787      │    └─────────────────┘    └─────────────────┘
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Zen MCP       │
│   Server        │
└─────────────────┘
```

### Service Dependencies

```
Console
├── Orchestrator (API)
├── Service Registry (Discovery)
└── PostgreSQL (User Data)

Orchestrator
├── PostgreSQL (Application Data)
├── Redis (Caching/Sessions)
├── Service Registry (Registration)
├── Zen MCP Server (AI Orchestration)
└── Terminal Daemon (Terminal Operations)

Terminal Daemon
└── Console (WebSocket Connection)

Service Registry
└── PostgreSQL (Service Data)

Zen MCP Server
├── Multiple AI Providers (OpenAI, Gemini, XAI, etc.)
└── Orchestrator (Workflow Integration)
```

## 📊 Core Services

### Console Service (`services/console/`)

**Technology Stack:**
- Next.js 14 with App Router
- React 18 with TypeScript
- Carbon Design System (IBM)
- TanStack Query for state management
- NextAuth v5 for authentication

**Responsibilities:**
- User interface and dashboard
- Authentication and authorization
- Real-time terminal display
- Agent management interface
- Job monitoring and execution

**Key Endpoints:**
- `/` - Main dashboard
- `/agents` - Agent management
- `/jobs` - Job monitoring
- `/terminal` - Terminal interface
- `/api/*` - API routes

### Orchestrator Service (`services/orchestrator/`)

**Technology Stack:**
- FastAPI with Python 3.11+
- SQLAlchemy with async PostgreSQL
- Redis for caching
- Alembic for migrations
- JWT authentication

**Responsibilities:**
- Core business logic orchestration
- Job scheduling and execution
- Agent lifecycle management
- API gateway and service coordination
- Security middleware implementation

**Key Endpoints:**
- `/healthz` - Health check
- `/readyz` - Readiness check
- `/v1/config` - Configuration retrieval
- `/v1/runs/plan` - Start planning run
- `/v1/runs/implement` - Start implementation run
- `/v1/runs/critic` - Start review/critique run
- `/v1/agents/status` - Agent status information
- `/auth/*` - Authentication endpoints

### Terminal Daemon Service (`services/terminal-daemon/`)

**Technology Stack:**
- Node.js 18+
- TypeScript
- WebSocket with node-pty
- Express.js for HTTP endpoints

**Responsibilities:**
- Real-time terminal operations
- WebSocket connection management
- Command execution and output streaming
- Session management

**Key Endpoints:**
- `ws://localhost:8787` - WebSocket terminal
- `/health` - Health check endpoint

### Service Registry (`packages/service-registry/`)

**Technology Stack:**
- FastAPI with Python
- PostgreSQL for service storage
- Health monitoring capabilities

**Responsibilities:**
- Service discovery and registration
- Health status monitoring
- Service metadata management
- Load balancing coordination

### Zen MCP Server (`zen-mcp-server/`)

**Technology Stack:**
- Python 3.11+
- MCP (Model Context Protocol) implementation
- Multiple AI provider integrations
- WebSocket for real-time communication

**Responsibilities:**
- AI model coordination and routing
- Workflow execution management
- Multi-provider AI integration
- Conversation memory management

## 🔄 Data Flow

### Request Flow

1. **User Request** → Console UI
2. **Console** → Orchestrator API (authenticated)
3. **Orchestrator** → Business logic execution
4. **Orchestrator** → Zen MCP Server (AI operations)
5. **Zen MCP** → External AI providers
6. **Terminal Operations** → Terminal Daemon
7. **Data Storage** → PostgreSQL/Redis
8. **Response** → Console UI

### Event Flow

```
User Action → Console → Orchestrator → Zen MCP → AI Provider
                                                    ↓
Terminal Command → Terminal Daemon ← Orchestrator
                                                    ↓
Data Storage → PostgreSQL ← Redis ← All Services
```

## 🗄️ Data Architecture

### Database Schema

**Core Tables:**
- `users` - User authentication and profile data
- `agents` - Agent configurations and capabilities
- `runs` - Execution runs and workflows
- `jobs` - Job definitions and execution history
- `service_registry` - Service registration data
- `quality_assessments` - Quality validation results
- `escalation_workflows` - Escalation process data

### Data Access Patterns

**Repository Pattern:**
- Each service has dedicated repository classes
- Abstract database access through interfaces
- Support for multiple database backends
- Connection pooling and optimization

**Caching Strategy:**
- Redis for session management
- Application-level caching for frequently accessed data
- Cache invalidation policies
- Fallback mechanisms for cache failures

## 🔐 Security Architecture

### Authentication Flow

```
1. User Login → Console
2. Console → NextAuth (OAuth/JWT)
3. NextAuth → Database (User verification)
4. JWT Token Generation
5. Token Storage (HttpOnly cookies)
6. API Requests → Token Validation
7. Authorization Checks → Resource Access
```

### Security Layers

1. **Network Layer**: TLS encryption, firewall rules
2. **Application Layer**: JWT validation, CSRF protection
3. **Data Layer**: Encryption at rest, parameterized queries
4. **Infrastructure Layer**: Container security, least privilege

## 📈 Monitoring & Observability

### Health Checks

**Service Health:**
- `/healthz` - Liveness probe
- `/readyz` - Readiness probe
- Dependency health verification
- Database connectivity checks

### Metrics Collection

**Application Metrics:**
- Request latency and throughput
- Error rates and status codes
- Database query performance
- Memory and CPU usage

**Business Metrics:**
- Job execution success rates
- Agent utilization metrics
- AI provider response times
- User activity metrics

### Logging Strategy

**Structured Logging:**
- JSON format with consistent fields
- Correlation IDs for request tracing
- Log levels (DEBUG, INFO, WARN, ERROR)
- Sensitive data redaction

**Log Aggregation:**
- Centralized log collection
- Real-time log analysis
- Alert threshold configuration
- Log retention policies

## 🚀 Deployment Architecture

### Container Strategy

**Multi-stage Builds:**
- Development builds with hot reload
- Production builds with optimization
- Security scanning in CI/CD
- Image vulnerability scanning

**Orchestration:**
- Docker Compose for local development
- Kubernetes for production deployment
- Service mesh for inter-service communication
- Ingress controllers for external access

### Environment Management

**Environment Configuration:**
- Development: Local Docker setup
- Staging: Cloud-based deployment
- Production: Multi-region deployment
- Configuration management through environment variables

**CI/CD Pipeline:**
- Automated testing (unit, integration, security)
- Container image building and scanning
- Progressive deployment strategies
- Rollback capabilities

## 🔧 Configuration Management

### Environment Variables

**Required Variables:**
- Database connection strings
- Authentication secrets
- AI provider API keys
- Service discovery endpoints
- Monitoring and logging configuration

**Configuration Files:**
- YAML-based service configuration
- Feature flags and toggles
- Rate limiting and throttling settings
- Security policy configurations

## 📋 Architecture Decision Records

Key architectural decisions are documented in the `docs/adr/` directory:

- [ADR 0001](../adr/0001-record-architecture-decisions.md) - Architecture Decision Records
- [ADR 0002](../adr/0002-hybrid-model-strategy-implementation.md) - Hybrid Model Strategy
- [ADR 2025-09](../adr/2025-09-ci-cd-and-previews.md) - CI/CD and Previews

## 🔄 Scalability Considerations

### Horizontal Scaling

**Service Scalability:**
- Stateless service design
- Load balancing capabilities
- Auto-scaling policies
- Circuit breakers for resilience

### Database Scalability

**Read Replicas:**
- Read scalability through replication
- Connection pooling optimization
- Query optimization strategies
- Database sharding considerations

### Cache Strategy

**Multi-level Caching:**
- Application-level caching
- Database query caching
- CDN for static assets
- Cache invalidation strategies

## 🔮 Future Considerations

### Planned Enhancements

1. **Multi-region Deployment**: Geographic distribution for resilience
2. **Event Sourcing**: Enhanced audit capabilities and temporal queries
3. **GraphQL API**: More flexible API querying
4. **Service Mesh**: Advanced traffic management and security
5. **Machine Learning Operations**: ML model deployment and monitoring

### Technical Debt

**Known Issues:**
- Authentication inconsistencies between services
- Single points of failure in database layer
- Limited monitoring granularity
- Performance optimization opportunities

**Refactoring Priorities:**
- Standardize authentication patterns
- Implement database clustering
- Enhanced observability platform
- Performance optimization across services

## 📞 Architecture Governance

### Review Process

- **Architecture Review Board**: Monthly architecture reviews
- **Design Patterns**: Enforce consistent patterns across services
- **Performance Budgets**: Define and monitor performance targets
- **Security Reviews**: Regular security assessments

### Documentation Standards

- **ADR Process**: Document all significant architectural decisions
- **API Documentation**: Auto-generated OpenAPI specifications
- **Service Documentation**: Comprehensive service documentation
- **Runbooks**: Operational procedures and troubleshooting guides