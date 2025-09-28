# Kyros Praxis Documentation

Welcome to the comprehensive documentation for Kyros Praxis, a sophisticated multi-service AI orchestration platform. This documentation provides everything you need to get started, develop features, deploy, and operate the platform.

## 🚀 Quick Start

**New to Kyros Praxis?** Start here:
1. [User Guide](user-guide/README.md) - Complete setup and usage guide
2. [FAQ](faq/README.md) - Common questions and answers
3. [API Documentation](api/README.md) - REST API reference with OpenAPI spec

**Having issues?** Check the [Troubleshooting Guide](troubleshooting/README.md)

## 📚 Documentation Index

### 🏁 Getting Started
- **[User Guide](user-guide/README.md)** - Comprehensive guide covering setup, API usage, and advanced features
- **[Quick Start Guide](QUICK_START.md)** - Minimal setup instructions
- **[Development Setup](DEVELOPMENT-SETUP.md)** - Development environment configuration
- **[FAQ](faq/README.md)** - Frequently asked questions with detailed answers

### 🏗️ Architecture & Design
- **[Architecture Overview](architecture/overview.md)** - System design and component architecture
- **[Architecture Decision Records](adr/)** - Design decisions and their rationale
- **[Integration Guide](integration/)** - Service integration patterns and examples

### 🔗 API & Integration
- **[API Documentation](api/README.md)** - Complete REST API reference
  - OpenAPI Specification: `http://localhost:8000/api/v1/openapi.json`
  - Interactive Docs: `http://localhost:8000/docs`
  - ReDoc Format: `http://localhost:8000/redoc`
- **[Backend API Documentation](api/backend_steel_thread.md)** - Backend-specific API details

### 🛡️ Security & Operations
- **[Security Guidelines](security/README.md)** - Security best practices and configuration
- **[Operations Manual](ops/runbooks/README.md)** - Deployment, monitoring, and operations
- **[Security Implementation](security-implementation-summary.md)** - Security feature implementation details

### 🔧 Development & Testing
- **[Testing Guide](TESTING.md)** - Testing strategies and procedures
- **[Development Plans](frontend-current-plan.md)** - Current development roadmap
  - [Frontend Plan](frontend-current-plan.md)
  - [Backend Plan](backend-current-plan.md)
- **[Implementation Roadmap](implementation-roadmap.md)** - Long-term development strategy

### 🆘 Support & Troubleshooting
- **[Troubleshooting Guide](troubleshooting/README.md)** - Step-by-step problem resolution
- **[FAQ](faq/README.md)** - Common questions with detailed answers
- **[Support Resources](#getting-help)** - How to get additional help

### 📦 Deployment & Operations
- **[Deployment Guide](deployment/)** - Production deployment procedures
- **[Operations Runbooks](ops/runbooks/)** - Operational procedures and troubleshooting
- **[Observability](observability.md)** - Monitoring and logging setup

### 🧪 Advanced Topics
- **[MCP Management](mcp-management.md)** - Model Control Protocol management
- **[Escalation System](escalation-system-guide.md)** - Automated escalation procedures
- **[Training Materials](training/)** - Educational resources and training guides

## 📊 Quick Reference

### Service Endpoints
| Service | Local URL | Documentation |
|---------|-----------|---------------|
| Console | http://localhost:3001 | Frontend dashboard |
| Orchestrator API | http://localhost:8000 | [API Docs](api/README.md) |
| Interactive API Docs | http://localhost:8000/docs | Swagger UI |
| OpenAPI Schema | http://localhost:8000/api/v1/openapi.json | OpenAPI 3.0 Spec |
| Terminal Daemon | ws://localhost:8787 | WebSocket terminal service |

### Essential Commands
```bash
# Start all services
docker compose up -d

# Run tests
python3 scripts/pr_gate.py --run-tests

# Check service health
curl http://localhost:8000/health

# View service logs
docker compose logs -f [service-name]
```

### Development Workflow
1. **Setup** - Follow [User Guide](user-guide/README.md) setup instructions
2. **Development** - See [Development Setup](DEVELOPMENT-SETUP.md)
3. **Testing** - Run tests with `python3 scripts/pr_gate.py --run-tests`
4. **Deployment** - Follow [Deployment Guide](deployment/)

## 🎯 Documentation Goals

This documentation aims to:
- **Reduce onboarding time** for new developers from days to hours
- **Provide comprehensive API reference** with interactive examples
- **Enable self-service troubleshooting** through detailed guides
- **Maintain up-to-date architectural decisions** through ADRs
- **Support production operations** with runbooks and procedures

## 📈 Documentation Quality

- **✅ Comprehensive Coverage** - All major features and APIs documented
- **✅ Interactive Examples** - API documentation with live examples
- **✅ Troubleshooting Support** - Step-by-step problem resolution
- **✅ Version Controlled** - All documentation tracked in Git
- **✅ Cross-Referenced** - Extensive linking between related topics
- **✅ Regular Updates** - Documentation maintained alongside code changes

## 🔗 External Resources

### Development Tools
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Standards & Specifications
- [OpenAPI Specification](https://swagger.io/specification/)
- [JSON API Specification](https://jsonapi.org/)
- [JWT (JSON Web Tokens)](https://jwt.io/)
- [WebSocket Protocol](https://tools.ietf.org/html/rfc6455)

## 💬 Getting Help

### Self-Service Resources
1. **[FAQ](faq/README.md)** - Check for common questions first
2. **[Troubleshooting Guide](troubleshooting/README.md)** - Step-by-step problem solving
3. **[API Documentation](api/README.md)** - Complete API reference
4. **[User Guide](user-guide/README.md)** - Comprehensive usage instructions

### Community Support
- **GitHub Issues** - [Report bugs or request features](https://github.com/tdawe1/kyros-praxis/issues)
- **GitHub Discussions** - Community Q&A and discussions
- **Documentation Issues** - Report documentation problems or suggestions

### Creating Issues
When creating issues, please include:
- **Clear problem description** with steps to reproduce
- **System information** (OS, Docker version, service versions)
- **Error messages and logs** (sanitized, no secrets)
- **Expected vs actual behavior**
- **Relevant configuration details** (without sensitive information)

## 📝 Contributing to Documentation

Documentation contributions are welcome! Please:
1. Follow the existing structure and style
2. Update relevant cross-references when adding new content
3. Test all code examples and commands
4. Include screenshots for UI changes
5. Update this index when adding new major sections

### Documentation Standards
- **Markdown format** with consistent formatting
- **Code examples** that are tested and working
- **Clear headings** and table of contents for long documents
- **Cross-references** to related documentation
- **Regular updates** to keep information current

---

**Last Updated:** Current as of the latest commit. This documentation is maintained alongside the codebase and updated with each release.