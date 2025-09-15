# ADR: CI/CD and Preview Environments for kyros-praxis

## Status
**Accepted**

## Date
2025-09-13

## Context
kyros-praxis needs a comprehensive CI/CD pipeline to automate testing, preview environments, and production deployments. The project consists of multiple services (Next.js frontend, FastAPI backend, terminal daemon) that need coordinated deployment.

## Decision

We implement a CI/CD pipeline using:

- **CircleCI** as the primary CI/CD platform
- **Vercel** for Next.js frontend deployment with preview environments
- **Railway** for backend services (FastAPI, PostgreSQL, Qdrant)
- **Existing GitHub Actions** maintained for parity

### Architecture

```
GitHub PR → CircleCI → Vercel Preview + Railway Preview → E2E Tests
                          ↓
Main Branch → CircleCI → Vercel Prod + Railway Prod → Smoke Tests
```

## Rationale

### CircleCI Choice
- **Fast parallel execution** with configurable resource classes
- **First-class Docker support** for containerized services
- **Orb ecosystem** for standardized workflows
- **Cost-effective** at scale compared to GitHub Actions
- **Enterprise features** like concurrency control and artifacts

### Vercel for Frontend
- **Zero-config Next.js deployment** with automatic optimizations
- **Instant preview environments** per PR
- **Built-in analytics and performance monitoring**
- **Edge CDN** for global distribution
- **Automatic SSL** and security headers

### Railway for Backend
- **Simplified container deployment** without complex Kubernetes
- **Managed databases** (PostgreSQL, Qdrant) with automatic scaling
- **Environment isolation** with preview environments per PR
- **Built-in health checks** and monitoring
- **Cost-effective** for small-to-medium workloads

## Implementation Details

### Pipeline Stages

1. **Checks**: ESLint, TypeScript, Ruff, MyPy, unit tests
2. **Build**: Next.js build, Docker images
3. **Test**: E2E with Playwright, contract testing
4. **Security**: npm audit, pip-audit, Trivy scans
5. **Deploy Preview**: Vercel + Railway per PR
6. **Deploy Production**: Vercel + Railway on main/tag
7. **Post-deploy**: Smoke tests and health checks

### Preview Environments

**Frontend (Vercel)**
- Automatic deployment on PR creation
- Unique URL per PR: `https://kyros-praxis-{pr-hash}.vercel.app`
- Environment variables scoped to preview

**Backend (Railway)**
- Isolated database per PR: `kyros_pr_${PR_NUMBER}`
- Managed Qdrant with API key isolation
- Automatic service discovery
- Auto-teardown on PR close

### Testing Strategy

**Unit Tests**
- Frontend: Jest + React Testing Library
- Backend: pytest with in-memory SQLite

**Integration Tests**
- Contract testing between frontend and backend
- API tests with real database
- WebSocket terminal functionality

**E2E Tests**
- Playwright against local Docker stack
- Additional smoke test against preview environments
- Screenshots and traces on failure

### Security & Quality

**Static Analysis**
- ESLint for frontend code
- Ruff for Python code
- MyPy for type safety

**Security Scanning**
- npm audit and pip-audit for dependencies
- Trivy for container vulnerabilities
- SAST rules with Semgrep (optional)

**Quality Gates**
- Test coverage reporting
- Build artifacts retention
- Conventional commit enforcement

## Alternatives Considered

### GitHub Actions + Self-hosted
**Pros**
- Native GitHub integration
- No additional platform costs
- Full control over runners

**Cons**
- Slower for complex pipelines
- Limited parallel execution
- Higher maintenance overhead

### AWS/GCP Native
**Pros**
- Maximum control and scalability
- Enterprise features
- Cost optimization at scale

**Cons**
- High complexity
- Steep learning curve
- Expensive for small teams

### Railway for Everything
**Pros**
- Single platform simplicity
- Unified billing
- Easy setup

**Cons**
- Limited CI features
- Less flexible for complex workflows
- Vendor lock-in concerns

## Costs and Limits

### CircleCI
- **Free tier**: 6,000 credits/month (~1,500 build minutes)
- **Estimated usage**: 200-300 build minutes/month
- **Monthly cost**: ~$50-100 for medium team

### Vercel
- **Hobby tier**: Free for personal projects
- **Pro tier**: $20/month for teams
- **Bandwidth**: 100GB/month included

### Railway
- **Starter tier**: $5/month per service
- **Pro tier**: $20/month per service
- **Database**: Free tier for development, $10/month for production

### Total Estimated Cost
- **Development**: ~$70/month
- **Production**: ~$120/month
- **Total**: ~$190/month

## Rollback Strategy

1. **Immediate Rollback**: Railway and Vercel support instant rollbacks
2. **Database**: Forward-only migrations with feature flags for breaking changes
3. **Monitoring**: Automated health checks and alerting
4. **Blue/Green**: Database cloning for zero-downtime updates

## Migration Plan

1. **Phase 1**: Set up CircleCI pipeline (current)
2. **Phase 2**: Configure Vercel and Railway projects
3. **Phase 3**: Migrate existing GitHub Actions to CircleCI
4. **Phase 4**: Enable preview environments
5. **Phase 5**: Production deployment pipeline

## Future Considerations

- **Feature flagging**: Integrate LaunchDarkly or ConfigCat
- **Performance testing**: Add K6 or Locust integration
- **Chaos engineering**: Gremlin for resilience testing
- **Multi-region**: Expand to global deployment
- **GitOps**: Flux/ArgoCD for infrastructure management

## Consequences

- **Positive**: Faster feedback cycles, reduced deployment risk, better collaboration
- **Negative**: Learning curve for new tools, additional platform costs
- **Neutral**: Maintains existing GitHub Actions for parity