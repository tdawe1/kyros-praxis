# 🚀 START HERE - Kyros Praxis CrewAI Stack

Welcome! This is your **quickstart roadmap** for the Kyros Praxis CrewAI platform.

---

## ⚡ I want to...

### ...Get Up and Running (5 minutes)
→ **[QUICKSTART.md](QUICKSTART.md)** - Copy-paste commands to start the stack

### ...Understand What This Is
→ **[README.md](README.md)** - Project overview, features, tech stack

### ...Integrate Authentication (Frontend Dev)
→ **[api/AUTH_API.md](api/AUTH_API.md)** - Complete auth integration guide with React examples

### ...Understand the Architecture
→ **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system design and components

### ...Follow Development Standards
→ **[DEVELOPMENT.md](DEVELOPMENT.md)** - Coding conventions and best practices

### ...See Project Status
→ **[MIGRATION-STATUS.md](MIGRATION-STATUS.md)** - Roadmap and migration progress

### ...Deploy to GitHub
→ **[STANDALONE-REPO-READY.md](STANDALONE-REPO-READY.md)** - Instructions for standalone repo

---

## 📊 Current Status

✅ **Phase 1: Foundation** - Complete  
✅ **Phase 2: Authentication** - Complete  
🔄 **Phase 3: Frontend Dashboard** - In Progress  

---

## 🎯 Quick Links

- **API Docs**: http://localhost:8001/docs (after starting)
- **Console**: http://localhost:3000 (after starting)
- **Database**: PostgreSQL on port 5432

---

## 🆘 Common Issues

**Can't start API?** → Check you have `.env` with JWT_SECRET_KEY and OPENROUTER_API_KEY  
**Can't connect to DB?** → Run `cd api && docker compose up -d db`  
**Console shows errors?** → Verify API is running on port 8001

---

## 📁 Repository Structure

```
├── api/          → FastAPI backend (port 8001)
├── console/      → Next.js frontend (port 3000)
├── docs/         → Additional documentation
└── *.md          → Guides and documentation
```

---

**New here?** Start with [QUICKSTART.md](QUICKSTART.md)!  
**Frontend team?** Go to [api/AUTH_API.md](api/AUTH_API.md)!  
**Questions?** Check [README.md](README.md)!
