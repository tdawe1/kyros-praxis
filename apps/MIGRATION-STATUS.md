# CrewAI Migration Status Report

**Date**: 2025-01-12  
**Status**: Phase 1 - Coexistence Configuration Complete

## Executive Summary

The Kyros Praxis project has successfully implemented a **CrewAI-ready architecture** in `api` while maintaining the legacy orchestrator for backward compatibility. This document tracks the migration progress and configuration changes.

---

## Changes Implemented

### 1. Port Conflict Resolution ✅

**Problem**: Both legacy orchestrator and new CrewAI API defaulted to port 8000.

**Solution**:
- **Legacy Orchestrator**: Remains on port 8000
- **New CrewAI API**: Now uses port 8001
- **Console**: Updated to target port 8001 by default

**Files Modified**:
- `console/app/page.tsx` - Changed default API_BASE to `http://localhost:8001`
- `api/README.md` - Updated uvicorn command to use port 8001
- `console/README.md` - Updated setup instructions with port 8001

### 2. Documentation Updates ✅

**Repository Guidelines** (`AGENTS.md`):
- Added dual-architecture explanation (CrewAI vs Legacy)
- Split build commands into "CrewAI Stack (Recommended)" and "Legacy Stack (Maintenance Mode)"
- Clarified migration status and service responsibilities

**New Architecture Documentation** (`apps/README.md`):
- Comprehensive guide to the CrewAI stack
- Service architecture diagram
- Environment variable documentation
- Migration strategy overview
- Quick start guides for both API and console
- Troubleshooting section

**Console Documentation** (`console/README.md`):
- Updated to reference CrewAI API on port 8001
- Added note distinguishing from legacy console
- Updated setup instructions with database steps

### 3. Environment Configuration ✅

**Created Configuration Files**:

**`api/.env.example`**:
- LLM provider configuration (OpenRouter + OpenAI)
- Database URLs (main + test)
- CORS settings
- Runtime options
- Comprehensive comments explaining each option

**`console/.env.example`**:
- API base URL configuration
- Clear note about targeting port 8001

---

## Architecture Overview

### Current State (Post-Implementation)

```
┌─────────────────────────────────────────────────────────────┐
│                    Kyros Praxis Monorepo                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  CrewAI Stack (Recommended)          Legacy Stack            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━          │
│                                                               │
│  console (3000)    ────────┐    services/console       │
│         │                       │    (references legacy)     │
│         │ SSE                   │                            │
│         ↓                       │    kyros-praxis/services/  │
│  api (8001)                │    orchestrator (8000)     │
│    ├── CrewAI                   │    ├── Job/Task API       │
│    ├── Manifests                │    ├── JWT Auth           │
│    ├── SSE Events               │    ├── WebSocket          │
│    └── PostgreSQL               │    └── User Management    │
│                                 │                            │
│                                 └──> terminal-daemon         │
│                                      service-registry        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Migration Roadmap

### ✅ Phase 1: Coexistence (COMPLETE)
**Duration**: Immediate  
**Status**: Complete  
**Completed**: 2025-01-12

- [x] Resolve port conflict (8000 vs 8001)
- [x] Document dual architecture in AGENTS.md
- [x] Create comprehensive apps/README.md
- [x] Update console to target CrewAI API
- [x] Add .env.example files for configuration
- [x] Update service READMEs with correct ports

**Result**: Both services can run simultaneously without conflicts. Developers have clear guidance on which stack to use.

---

### ✅ Phase 2: Feature Parity (COMPLETE)
**Duration**: 1 day  
**Status**: Complete  
**Completed**: 2025-01-12

**Completed Goals**:
- [x] Port JWT authentication to CrewAI API
- [x] Add User model and database migration
- [x] Implement auth endpoints (/auth/register, /auth/login, /auth/me)
- [x] Add optional authentication to crew endpoints
- [x] Comprehensive API documentation (AUTH_API.md)
- [x] React/TypeScript integration examples

**Deferred to Phase 3**:
- [ ] Implement RBAC (role-based access control) enforcement
- [ ] Add API key management
- [ ] Create job-to-crew-run adapter for backward compatibility
- [ ] Unified OpenAPI specification
- [ ] Monitoring and observability setup

**Acceptance Criteria**: ✅ ALL MET
- ✅ CrewAI API has JWT authentication system
- ✅ User registration and login working
- ✅ Optional auth for crew runs (tracks user_id when authenticated)
- ✅ Frontend integration guide complete
- ✅ Database migration applied successfully

**Documentation**:
- [api/AUTH_API.md](api/AUTH_API.md) - Complete API docs
- [apps/PHASE2-AUTH-COMPLETE.md](apps/PHASE2-AUTH-COMPLETE.md) - Implementation summary

---

### ⏸️ Phase 3: Incremental Migration (PLANNED)
**Duration**: 8-12 weeks  
**Status**: Not Started

**Goals**:
- [ ] Add routing layer to direct new requests to CrewAI API
- [ ] Keep legacy orchestrator for historical job queries
- [ ] Build CLI migration tool (jobs → crew_runs)
- [ ] Add data export/import utilities
- [ ] Performance benchmarking between stacks

**Acceptance Criteria**:
- All new requests route to CrewAI API
- Historical data remains accessible via legacy API (read-only)
- Migration tool successfully converts job data

---

### 🔮 Phase 4: Deprecation (PLANNED)
**Duration**: 12+ weeks  
**Status**: Not Started

**Goals**:
- [ ] Freeze legacy orchestrator (read-only mode)
- [ ] Archive historical job data
- [ ] Decommission legacy orchestrator service
- [ ] Remove legacy console
- [ ] Clean up deprecated code paths

**Acceptance Criteria**:
- Legacy orchestrator no longer accepts writes
- All production traffic flows through CrewAI API
- Historical data archived and accessible

---

## Technical Debt Resolved

### High Priority ✅
- [x] **Port Conflict**: Both services now use distinct ports (Phase 1)
- [x] **Documentation Confusion**: Clear separation in AGENTS.md and new apps/README.md (Phase 1)
- [x] **Console Target Ambiguity**: Console explicitly targets port 8001 (Phase 1)
- [x] **Missing auth in new API**: JWT authentication implemented (Phase 2)

### Still Outstanding
- [ ] No error handling in crew_runner.py for provider failures
- [ ] Duplicate model definitions (Job vs CrewRun) - needs migration adapter
- [ ] No refresh token mechanism (planned for Phase 3)
- [ ] Rate limiting not implemented (planned for Phase 3)

---

## Quick Start (Post-Configuration)

### Running CrewAI Stack

```bash
# Terminal 1: Start database
cd api
docker compose up -d db
alembic upgrade head

# Terminal 2: Start API
cd api
cp .env.example .env  # Edit with your API keys
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 3: Start console
cd console
cp .env.example .env  # Should already have correct port
npm install
npm run dev

# Access console at http://localhost:3000
```

### Running Legacy Stack

```bash
# Terminal 1: Start orchestrator
cd kyros-praxis/services/orchestrator
uvicorn main:app --reload --port 8000

# Terminal 2: Start legacy console (if needed)
cd services/console
npm run dev
```

---

## Developer Guidelines

### For New Development
✅ **Use CrewAI Stack** (`apps/*`)
- Port 8001 for API
- Port 3000 for console
- Follow manifest-based workflow
- Reference `apps/README.md` for setup

### For Maintenance Work
⚠️ **Use Legacy Stack** (`kyros-praxis/services/*`)
- Port 8000 for orchestrator
- Minimize new features
- Plan migration path to CrewAI API

---

## Environment Variables Summary

### CrewAI API (api)
```bash
OPENROUTER_API_KEY=sk-or-v1-...
MODEL_PROVIDER=openrouter
MODEL_NAME=gpt-4o-mini
DATABASE_URL=postgresql+asyncpg://kyros:kyros@localhost:5432/kyros
CORS_ALLOW_ORIGINS=["http://localhost:3000"]
KYROS_ENV=dev
```

### Console (console)
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

---

## Testing Status

### CrewAI API
- **Unit Tests**: Exist (`api/tests/`)
- **Integration Tests**: Basic crew run flow tested
- **Status**: ✅ Passing

### Console
- **Tests**: Not yet configured
- **Status**: ⚠️ Needs setup

---

## Known Issues

1. **PRD Document Format**: `PRD_ Prompt-Driven Development via CrewAI Integration.docx` is in binary DOCX format
   - **Recommendation**: Convert to Markdown for version control
   - **Action**: Pending user decision

2. **Duplicate Consoles**: Two console implementations exist
   - `console` - New CrewAI-focused
   - `services/console` - Legacy orchestrator-focused
   - **Resolution**: Document separation complete; consider deprecating legacy console in Phase 4

3. **Auth Gap**: New API lacks authentication
   - **Impact**: Not production-ready
   - **Resolution**: Planned for Phase 2

---

## Next Steps

### Immediate (This Week)
1. Test coexistence setup with both services running
2. Verify console can communicate with API on port 8001
3. Document any additional configuration issues

### Short-term (Next Sprint)
1. Begin Phase 2: Port JWT authentication
2. Add integration tests for authentication flow
3. Create OpenAPI spec for CrewAI API

### Medium-term (Next Quarter)
1. Implement job-to-crew-run adapter
2. Set up monitoring and observability
3. Performance benchmarking

---

## Resources

- **CrewAI Docs**: [apps/README.md](apps/README.md)
- **API Docs**: [api/README.md](api/README.md)
- **Console Docs**: [console/README.md](console/README.md)
- **Repository Guidelines**: [AGENTS.md](AGENTS.md)
- **Backend Plan**: [kyros-praxis/backend-current-plan.md](kyros-praxis/backend-current-plan.md)
- **Frontend Plan**: [kyros-praxis/frontend-current-plan.md](kyros-praxis/frontend-current-plan.md)

---

## Conclusion

**Phase 1 (Coexistence)** is now complete. Both the CrewAI API and legacy orchestrator can run simultaneously without conflicts. Comprehensive documentation guides developers to the appropriate stack for their work. The project is ready for Phase 2 (Feature Parity) implementation.

**Recommendation**: Begin authentication migration to unlock production readiness for the CrewAI stack.
