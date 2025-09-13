# Kyros Praxis - AI Orchestration Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)](https://www.typescriptlang.org/)

Kyros Praxis is a sophisticated multi-service AI orchestration platform that provides intelligent agent management, real-time terminal operations, and collaborative development workflows with enterprise-grade security and observability.

## 🏗️ Architecture

**Core Services:**
- **Console** - Next.js frontend with Carbon Design System
- **Orchestrator** - FastAPI backend with SQLAlchemy & PostgreSQL
- **Terminal Daemon** - WebSocket terminal service (Node.js + node-pty)
- **Service Registry** - Service discovery and health monitoring
- **Zen MCP Server** - AI model coordination and workflow execution

**Data Flow:**
```
User → Console → Orchestrator → [PostgreSQL/Redis]
                     ↓
              Zen MCP Server → AI Models
                     ↓
              Terminal Daemon → CLI
```

## 🚀 Quick Start

### Prerequisites
- [Docker](https://docker.com) & [Docker Compose](https://docs.docker.com/compose/)
- [Node.js 18+](https://nodejs.org) & [Python 3.11+](https://python.org)
- [Git](https://git-scm.com)

### Development Environment

```bash
# Clone the repository
git clone https://github.com/tdawe1/kyros-praxis.git
cd kyros-praxis

# Start infrastructure services
docker-compose up -d postgres redis

# Start the orchestrator
cd services/orchestrator
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start the console
cd ../console
npm install
npm run dev

# Start the terminal daemon
cd ../terminal-daemon
npm install
npm start
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## 📊 Service Endpoints

| Service | Local URL | Description |
|---------|-----------|-------------|
| Console | http://localhost:3001 | Next.js frontend dashboard |
| Orchestrator | http://localhost:8000 | FastAPI backend API |
| Terminal Daemon | ws://localhost:8787 | WebSocket terminal service |
| PostgreSQL | localhost:5432 | Primary database |
| Redis | localhost:6379 | Caching layer |

## 🔧 Development Commands

### Console Service (Next.js)
```bash
cd services/console
npm run dev          # Development server
npm run build        # Production build
npm run start        # Production server
npm run lint         # ESLint validation
npm test             # Test suite
```

### Orchestrator Service (FastAPI)
```bash
cd services/orchestrator
python -m uvicorn main:app --reload --port 8000
python -m pytest                                    # Test suite
alembic upgrade head                                # Database migrations
```

### Terminal Daemon Service (Node.js)
```bash
cd services/terminal-daemon
npm run dev          # Development server
npm run build        # TypeScript compilation
npm start           # Production server
```

## 🛡️ Security Features

- **Authentication**: NextAuth v5 with JWT tokens
- **Authorization**: Role-based access control
- **CSRF Protection**: HMAC-based token validation
- **Rate Limiting**: Configurable request throttling
- **Content Security Policy**: Strict CSP headers
- **Database Security**: Parameterized queries with SQL injection prevention
- **Secret Management**: Environment-based configuration

## 📖 Documentation

- [Architecture Overview](docs/architecture/overview.md) - System design and components
- [API Documentation](docs/api/README.md) - REST API endpoints and schemas
- [Security Guidelines](docs/security/README.md) - Security best practices
- [Operations Manual](docs/operations/README.md) - Deployment and operations
- [Architecture Decision Records](docs/adr/) - Design decisions and rationale
- [Zen MCP Server](zen-mcp-server/docs/) - AI coordination server documentation

## 🔗 Related Resources

### Project Plans
- [Frontend Development Plan](frontend-current-plan.md)
- [Backend Development Plan](backend-current-plan.md)
- [Implementation Roadmap](docs/implementation-roadmap.md)

### Integration Guides
- [MCP Server Setup](docs/zen-mcp-setup.md)
- [Service Integration](docs/integration/hybrid-model-integration-guide.md)
- [Deployment Guide](docs/deployment/hybrid-model-deployment-guide.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Development Guidelines
- Follow the existing code style and conventions
- Update relevant documentation
- Include tests for all changes
- Ensure all security checks pass
- Update project plans if scope changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For technical support or questions:
- Check the [FAQ](docs/faq/hybrid-model-faq.md)
- Review [troubleshooting guides](docs/troubleshooting/)
- Submit issues on GitHub with appropriate labels
