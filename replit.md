# Overview

Kyros Praxis is an AI-powered orchestration platform designed as a monorepo with multiple microservices. The platform provides intelligent agent management, real-time terminal operations, and collaborative development workflows with enterprise-grade quality gates. It features a sophisticated multi-service architecture with a Next.js frontend (Console), FastAPI backend (Orchestrator), Node.js terminal service (Terminal Daemon), and centralized service discovery with AI coordination through Zen MCP Server.

The system is built to handle complex AI workflows, content repurposing, and collaborative agent coordination with features like ETag-based atomic updates, lease-based execution models, and append-only event logging for full audit trails.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Services Architecture

The platform follows a microservices architecture with clear separation of concerns:

**Frontend (Console Service)**: Built with Next.js 14.2.5 using App Router for modern React development. Uses Carbon Design System for UI components, Next-Auth for OIDC authentication, and TypeScript for type safety. Supports real-time updates via WebSocket connections and implements CSP headers for security.

**Backend (Orchestrator Service)**: FastAPI-based Python service with SQLAlchemy ORM and PostgreSQL database. Implements JWT authentication, rate limiting via SlowAPI, and database migrations through Alembic. Features ETag-based conditional updates for collaborative workflows and structured error handling.

**Terminal Daemon**: Node.js service using node-pty for terminal operations with WebSocket communication. Provides real-time terminal access and command execution capabilities.

**Service Registry**: Centralized service discovery and health monitoring system that tracks all running services and their status.

## Data Storage and State Management

**Database**: PostgreSQL primary database with SQLAlchemy models. Uses Alembic for schema migrations and supports both SQLite (development) and PostgreSQL (production) through configurable connection strings.

**Caching**: Redis for session storage, rate limiting, and caching common reads. Also used for background job queuing with Celery integration.

**Collaborative State**: File-based JSON state management in `collaboration/state/` with ETag-based atomic updates using If-Match headers. Events stored as append-only JSONL for audit trails.

## Authentication and Authorization

**Primary Auth**: Next-Auth v4 with OIDC provider integration. JWT tokens for API authentication with configurable secret keys.

**API Security**: Dual authentication model - JWT tokens for user-facing APIs and API key validation (X-API-Key header) for service-to-service communication. Rate limiting implemented per API key with Redis backing.

**Security Headers**: Comprehensive CSP, X-Frame-Options, and other security headers configured in Next.js and Vercel deployment.

## AI Coordination and Workflow Management

**Zen MCP Server**: Multi-model AI coordination system that manages different AI models (GPT, Claude, Gemini) with intelligent routing based on task complexity and rate limits. Supports agent registration, session management, and tool orchestration.

**Escalation System**: Sophisticated trigger detection for escalating complex tasks to Claude 4.1 Opus based on security sensitivity, architectural decisions, and business impact analysis.

**Lease-Based Execution**: Distributed lock mechanism using TTL and heartbeat patterns for coordinating work across agents without traditional locking.

## Testing and Quality Assurance

**Multi-Layer Testing**: Jest for frontend unit tests, pytest for backend testing, Playwright for end-to-end testing. Comprehensive test infrastructure with fixtures and mocks.

**Quality Gates**: PR gate system that enforces test coverage, lint checks, security scans, and plan synchronization. Conventional commit format required with automated changelog generation.

**Monitoring**: Structured logging, health check endpoints (`/readyz`, `/healthz`), and performance metrics tracking with Sentry integration for error monitoring.

# External Dependencies

## Core Infrastructure
- **PostgreSQL**: Primary database for persistent data storage
- **Redis**: Caching, session storage, rate limiting, and background job queuing
- **Docker Compose**: Container orchestration for local development environment

## AI and ML Services
- **OpenAI API**: GPT models for various AI tasks
- **Anthropic API**: Claude models for complex reasoning tasks
- **Google Gemini**: Additional AI model for specialized tasks
- **OpenRouter**: AI model routing and access management

## Development and Deployment
- **Vercel**: Frontend deployment and hosting platform
- **GitHub**: Version control and CI/CD integration
- **Sentry**: Error monitoring and performance tracking
- **Playwright**: Automated browser testing for E2E scenarios

## Third-Party Integrations
- **Carbon Design System**: IBM's design system for consistent UI components
- **Next-Auth**: Authentication library for OAuth/OIDC providers
- **Alembic**: Database migration management for Python
- **Celery**: Distributed task queue for background job processing

## Development Tools
- **MCP (Model Context Protocol)**: Server communication protocol for AI agents
- **Ruff**: Python linting and formatting
- **ESLint**: JavaScript/TypeScript linting
- **TypeScript**: Type checking for frontend development
- **Jest**: JavaScript testing framework
- **pytest**: Python testing framework