# Kyros Praxis - CrewAI Stack

> **Prompt-Driven Development Platform** using CrewAI for intelligent agent orchestration

A production-ready FastAPI + Next.js stack for building AI-powered applications with CrewAI agents, JWT authentication, and real-time event streaming.

---

## 🚀 Quick Start

**Get running in 5 minutes**: See [QUICKSTART.md](QUICKSTART.md)

```bash
# 1. Start database
cd api && docker compose up -d db

# 2. Setup API
pip install -r requirements.txt
cp .env.example .env  # Add your OPENROUTER_API_KEY and JWT_SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8001

# 3. Setup Console
cd ../console && npm install && npm run dev

# 4. Visit http://localhost:3000
```

---

## 📖 Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide | New developers |
| [README.md](README.md) | Architecture & overview | All developers |
| [api/AUTH_API.md](api/AUTH_API.md) | Authentication API guide | Frontend team |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Coding standards | Contributors |
| [PHASE2-AUTH-COMPLETE.md](PHASE2-AUTH-COMPLETE.md) | Auth implementation details | Technical leads |
| [MIGRATION-STATUS.md](MIGRATION-STATUS.md) | Project roadmap | Project managers |

---

## 🏗️ Architecture

```
┌─────────────────┐
│ Console         │  Next.js 14 dashboard (port 3000)
│ (Frontend)      │  - User authentication
└────────┬────────┘  - Crew run management
         │ HTTP + SSE - Real-time monitoring
         ↓
┌─────────────────┐
│ API             │  FastAPI backend (port 8001)
│ (Backend)       │  - JWT authentication
│                 │  - CrewAI orchestration
│                 │  - Event streaming
└────────┬────────┘
         │ asyncpg
         ↓
┌─────────────────┐
│ PostgreSQL      │  Database (port 5432)
│                 │  - users, crew_runs, crew_events
└─────────────────┘
         │
         ↓
┌─────────────────┐
│ OpenRouter      │  LLM provider
│                 │  - gpt-4o-mini, claude, etc.
└─────────────────┘
```

---

## ✨ Features

### Authentication
- ✅ JWT-based user authentication
- ✅ User registration and login
- ✅ Optional run tracking by user
- ✅ Secure password hashing (bcrypt)

### CrewAI Integration
- ✅ Manifest-based agent workflows (YAML)
- ✅ Prompt template system (Markdown)
- ✅ OpenRouter/OpenAI provider support
- ✅ Real-time event streaming (SSE)

### Database
- ✅ PostgreSQL with async support
- ✅ Alembic migrations
- ✅ User and run tracking
- ✅ Event logging

### Frontend
- ✅ Next.js 14 with App Router
- ✅ Real-time run monitoring
- ✅ Authentication UI (ready for implementation)
- ✅ Server-Sent Events (SSE) integration

---

## 📁 Project Structure

```
kyros-praxis/
├── api/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py              # API entry point
│   │   ├── auth.py              # JWT authentication
│   │   ├── models.py            # Pydantic models
│   │   ├── crew_runner.py       # CrewAI orchestration
│   │   ├── db/
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   └── session.py       # Database session
│   │   ├── routers/
│   │   │   └── auth.py          # Auth endpoints
│   │   └── core/
│   │       └── config.py        # Settings
│   ├── alembic/                 # Database migrations
│   ├── ai/
│   │   ├── crews/               # Crew manifests (YAML)
│   │   └── prompts/             # Prompt templates (Markdown)
│   ├── tests/                   # API tests
│   ├── requirements.txt
│   └── .env.example
│
├── console/                      # Next.js frontend
│   ├── app/
│   │   ├── page.tsx             # Main dashboard
│   │   └── layout.tsx           # App layout
│   ├── package.json
│   └── .env.example
│
├── docs/                         # Additional documentation
├── QUICKSTART.md                # Quick setup guide
├── README.md                    # This file
├── DEVELOPMENT.md               # Development guidelines
└── .gitignore
```

---

## 🔧 Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **CrewAI** - Multi-agent orchestration framework
- **SQLAlchemy** - Async ORM for PostgreSQL
- **Alembic** - Database migrations
- **python-jose** - JWT tokens
- **passlib** - Password hashing
- **asyncpg** - Async PostgreSQL driver

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **React** - UI library
- **Server-Sent Events** - Real-time updates

### Database
- **PostgreSQL 16** - Primary database

### AI/LLM
- **OpenRouter** - Multi-model LLM access (recommended)
- **OpenAI** - Direct API access (optional)

---

## 🔐 Authentication

Complete JWT authentication system with:
- User registration (`POST /auth/register`)
- User login (`POST /auth/login`)
- Current user info (`GET /auth/me`)
- Optional auth for crew runs

**See**: [api/AUTH_API.md](api/AUTH_API.md) for integration guide.

---

## 🤖 CrewAI Workflows

Define agent workflows with YAML manifests:

```yaml
# api/ai/crews/spec_to_tasks.yaml
name: spec_to_tasks
description: Convert a plan/spec document into structured tasks
model:
  provider: openrouter
  name: gpt-4o-mini
roles:
  - name: planner
    goal: extract actionable tasks from the plan
    prompt: spec_to_tasks.md
```

Prompt templates use Markdown with variable substitution:

```markdown
# api/ai/prompts/spec_to_tasks.md
You are a senior technical planner. Given the following plan text,
extract a concise set of tasks...

User input:
{prompt}
```

---

## 🧪 Testing

### API Tests
```bash
cd api
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_auth.py # Specific test
```

### Manual Testing
```bash
# Health check
curl http://localhost:8001/health

# Register user
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"password123"}'

# Create crew run
curl -X POST http://localhost:8001/crews/runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"crew_id":"spec_to_tasks","input":{"prompt":"Build a todo app"}}'
```

---

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - Create user account
- `POST /auth/login` - Get JWT token
- `GET /auth/me` - Get current user

### Crew Runs
- `POST /crews/runs` - Create new run
- `GET /crews/runs/{id}` - Get run status
- `POST /crews/runs/{id}/cancel` - Cancel run
- `GET /crews/runs/{id}/events` - Stream events (SSE)

### Health
- `GET /health` - Health check

**Interactive docs**: http://localhost:8001/docs

---

## 🔒 Security

### Implemented
- ✅ JWT token authentication
- ✅ Bcrypt password hashing
- ✅ CORS configuration
- ✅ Environment-based secrets
- ✅ Input validation

### Recommended for Production
- [ ] Enable HTTPS/TLS
- [ ] Add rate limiting
- [ ] Implement refresh tokens
- [ ] Add account lockout
- [ ] Enable audit logging
- [ ] Set up monitoring

---

## 🌍 Environment Variables

### API (api/.env)
```bash
# LLM Provider
OPENROUTER_API_KEY=sk-or-v1-...
MODEL_PROVIDER=openrouter
MODEL_NAME=gpt-4o-mini

# Database
DATABASE_URL=postgresql+asyncpg://kyros:kyros@localhost:5432/kyros

# JWT Authentication
JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# CORS
CORS_ALLOW_ORIGINS=["http://localhost:3000"]
```

### Console (console/.env.local)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

---

## 🚢 Deployment

### Docker Compose (Development)
```bash
cd api
docker compose up -d  # Starts PostgreSQL
```

### Production Checklist
- [ ] Generate strong JWT_SECRET_KEY
- [ ] Configure production DATABASE_URL
- [ ] Set CORS_ALLOW_ORIGINS to production domain
- [ ] Enable HTTPS
- [ ] Set up monitoring/logging
- [ ] Configure backup strategy
- [ ] Review security settings

---

## 🤝 Contributing

1. Follow [DEVELOPMENT.md](DEVELOPMENT.md) guidelines
2. Use Conventional Commits
3. Write tests for new features
4. Update documentation
5. Submit pull requests with clear descriptions

---

## 📝 License

[Add your license here]

---

## 🆘 Support

- **Quick setup**: [QUICKSTART.md](QUICKSTART.md)
- **Architecture**: [README.md](README.md)
- **Auth integration**: [api/AUTH_API.md](api/AUTH_API.md)
- **Development**: [DEVELOPMENT.md](DEVELOPMENT.md)
- **API docs**: http://localhost:8001/docs

---

## 🗺️ Roadmap

### ✅ Phase 1: Foundation (Complete)
- Authentication system
- CrewAI integration
- Database setup
- Real-time streaming

### 🔄 Phase 2: Enhancement (In Progress)
- Frontend dashboard UI
- User profile management
- Advanced crew workflows
- Performance optimization

### 📋 Phase 3: Production (Planned)
- Refresh token mechanism
- Rate limiting
- Admin dashboard
- OAuth2 integration
- Monitoring/alerting

---

**Status**: 🚀 Ready for Development

Built with ❤️ using CrewAI, FastAPI, and Next.js
