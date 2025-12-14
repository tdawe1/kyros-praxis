# Unified Audit & Surgical Reboot Plan

**Date**: October 13, 2025  
**Sources**: 
- Surgical Reboot Analysis (Droid)
- Detailed Investigation (Previous Analysis)
- PRD Requirements

---

## Executive Summary

**Current Status**: **75-80% Complete** - Solid foundation, needs PRD alignment

**Key Finding**: You have excellent infrastructure BUT:
- ✅ Multi-agent architecture exists
- ✅ CrewAI integrated and working
- ⚠️ **Gap**: Current implementation ≠ PRD vision
- ⚠️ **Issue**: Prototype features, not production-ready
- ⚠️ **Problem**: Missing dependencies cause runtime failures

**Recommendation**: **Targeted Surgery** - Fix critical issues, align with PRD

---

## Synthesis: Two Analyses Combined

### Agreement Points (Both Found)

| Finding | Surgical Reboot | Investigation | Status |
|---------|----------------|---------------|--------|
| **Auth System** | ✅ Enterprise-grade, just completed | ✅ Cookie-based, working | 🟢 KEEP |
| **CrewAI Integration** | ✅ Found crew_runner.py | ✅ Exists but single-agent only | 🟡 FIX |
| **Database Models** | ✅ Good structure | ✅ Multi-agent tables exist | 🟢 KEEP |
| **Workflow Pipeline** | 🔍 Needs investigation | ⚠️ Prototype, auto-approves | 🔴 CRITICAL |
| **Frontend** | ✅ Next.js solid | ✅ Structure good, tests outdated | 🟡 FIX |
| **Missing Dependencies** | 🔍 Not checked | ❌ apscheduler, redis, prometheus | 🔴 CRITICAL |

---

## Critical Issues (Must Fix Before PRD Work)

### 🔴 CRITICAL #1: Missing Dependencies Cause Runtime Crashes

**Issue**:
```python
# api/app/jobs/cleanup.py imports these:
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # ❌ NOT IN requirements.txt

# api/app/cache/redis_cache.py imports:
from redis import asyncio as aioredis  # ❌ NOT IN requirements.txt

# api/app/middleware/metrics.py imports:
from prometheus_client import Counter, Histogram  # ❌ NOT IN requirements.txt
```

**Impact**: Server startup advertises features that crash on use

**Fix**: Add to `requirements.txt`:
```txt
# Background jobs
apscheduler==3.10.4

# Caching (optional but referenced)
redis==5.0.1

# Metrics (optional but referenced)
prometheus-client==0.19.0
```

**Alternative**: Guard these imports more carefully (already partially done)

**Priority**: 🔴 **IMMEDIATE** (blocks production deployment)

---

### 🔴 CRITICAL #2: Database Schema Mismatch

**Issue**:
```python
# api/app/jobs/cleanup.py:87
task.archived = True  # ❌ Column doesn't exist

# api/app/db/models.py - Task model has no `archived` field
```

**Impact**: Background cleanup job crashes

**Fix**: Either:
1. Add migration:
```python
# alembic/versions/000X_add_archived_field.py
def upgrade():
    op.add_column('tasks', sa.Column('archived', sa.Boolean(), default=False))
```

2. Or change cleanup logic to use existing fields

**Priority**: 🔴 **IMMEDIATE** (blocks background jobs)

---

### 🔴 CRITICAL #3: Outdated Tests (False Confidence)

**Issue**:
```typescript
// console/app/state/auth-context.test.tsx:61-148
// Tests still use localStorage, but code uses cookies!

const token = localStorage.getItem('token');  // ❌ Code doesn't do this anymore
```

**Impact**: Tests pass but don't validate actual auth flow

**Fix**: Rewrite tests for cookie-based auth:
```typescript
// Mock cookie behavior
global.document.cookie = 'access_token=fake-token';

// Test actual cookie auth
expect(fetch).toHaveBeenCalledWith(url, {
  credentials: 'include'  // ✅ What code actually does
});
```

**Priority**: 🔴 **IMMEDIATE** (false security confidence)

---

## Major Gap: Current vs PRD

### What PRD Expects

```
┌─────────────────────────────────────────────────────┐
│ User Input (Detailed Prompt)                        │
│ "I want a Flask web app with..."                    │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│ PLANNER AGENT                                       │
│ • Analyzes prompt                                   │
│ • Creates structured spec                           │
│ • Breaks into components                            │
│ • User reviews/approves spec                        │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│ CODER AGENT                                         │
│ • Generates code for each component                 │
│ • Creates file structure                            │
│ • Adds comments/docs                                │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│ TESTER AGENT                                        │
│ • Reviews generated code                            │
│ • Creates unit tests                                │
│ • Validates functionality                           │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│ DOCUMENTER AGENT (Optional)                         │
│ • Generates README                                  │
│ • Creates API docs                                  │
│ • Writes usage instructions                         │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│ ITERATION LOOP                                      │
│ User: "Make it mobile-friendly"                     │
│ → Re-runs with refinements                          │
└─────────────────────────────────────────────────────┘
```

---

### What Currently Exists

```
┌─────────────────────────────────────────────────────┐
│ Manifest-Driven Execution                           │
│ • Hardcoded YAML manifests                          │
│ • Single role/task (spec_to_tasks)                  │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│ SINGLE CREW RUN                                     │
│ • Same crew for all stages                          │
│ • Orchestrator → Implementer → Critic               │
│ • Auto-approves if critic errors                    │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│ SIMULATION MODE (when CrewAI missing)               │
│ • Returns fake output                               │
│ • No actual agent execution                         │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│ NO ITERATION                                        │
│ • One-shot execution                                │
│ • No refinement loop                                │
│ • No user approval gates                            │
└─────────────────────────────────────────────────────┘
```

**Gap**: Current = prototype scaffolding, PRD = production feature

---

## Detailed Findings by Component

### ✅ API Backend - GOOD Foundation, Needs Alignment

**Strengths**:
- ✅ FastAPI well-structured (`main.py:19-194`)
- ✅ Auth system enterprise-grade (just completed)
- ✅ SSE streaming working
- ✅ Database models comprehensive
- ✅ Middleware architecture solid

**Issues**:
| Issue | Location | Severity | Fix |
|-------|----------|----------|-----|
| Missing deps | `requirements.txt:1-21` | 🔴 Critical | Add packages |
| Schema mismatch | `models.py:85-105`, `cleanup.py:87` | 🔴 Critical | Add migration |
| Single-agent only | `crew_runner.py:41-193` | 🟡 Major | Multi-agent support |
| Auto-approve critic | `pipeline.py:66-435` | 🟡 Major | Add review gate |
| Simulation fallback | `crew_runner.py:41-193` | 🟢 Minor | Document behavior |
| Limited tests | `tests/` | 🟡 Major | Expand coverage |

**PRD Alignment**: **60%** - Structure exists, needs multi-agent workflow

---

### ✅ Console Frontend - GOOD UI, Needs Testing

**Strengths**:
- ✅ Next.js 15 (modern)
- ✅ Cookie auth working
- ✅ Terminal component solid
- ✅ Planner page exists
- ✅ Shared UI components

**Issues**:
| Issue | Location | Severity | Fix |
|-------|----------|----------|-----|
| Outdated tests | `auth-context.test.tsx:61-148` | 🔴 Critical | Rewrite for cookies |
| No APIError.correlationId | `api-client.ts:7-119` | 🟡 Major | Add field |
| Placeholder pages | `kyros-lexis/`, `templates/` | 🟢 Minor | Hide or implement |
| No test coverage | Multiple components | 🟡 Major | Add tests |

**PRD Alignment**: **50%** - UI exists, missing prompt builder & code viewer

---

### ✅ Database - EXCELLENT, Minor Additions Needed

**Current Models**:
```python
✅ User           # Auth
✅ OAuthAccount   # OAuth ready
✅ Project        # Multi-agent support
✅ Task           # Workflow tasks
✅ CrewRun        # Agent execution
✅ CrewEvent      # Event tracking
✅ SharedMemory   # Agent memory
✅ WorkflowStage  # Pipeline stages
✅ CriticFeedback # Review feedback
✅ Artifact       # Generated files
```

**Needed Additions** (from PRD):
```python
# Add to Project model:
prompt: Text              # ❌ Missing - User's detailed prompt
specification: Text       # ❌ Missing - AI-generated spec
generated_code: JSON      # ❌ Missing - File structure + code
iteration_count: Int      # ❌ Missing - Refinement tracking

# Add to Task model:
archived: Boolean         # ❌ Missing - Causes cleanup.py to crash

# New model needed:
class PromptTemplate:     # ❌ Missing - PRD requirement
  name: String
  category: String
  template_text: Text
```

**PRD Alignment**: **80%** - Most models exist, need prompt-specific fields

---

### ⚠️ Workflows - PROTOTYPE, Not Production

**Current State** (`pipeline.py:66-435`):
```python
# ❌ Issues:
- Same crew for all stages (not separate agents)
- Auto-approves on critic errors
- No refinement loop (_refine_implementation is TODO)
- No user approval gates
- Hardcoded logic
```

**PRD Requires**:
```python
# ✅ Needed:
- Distinct Planner, Coder, Tester, Documenter agents
- User reviews spec before coding starts
- Iteration loop with refinements
- Proper error handling (not auto-approve)
- Dynamic prompt processing
```

**Gap**: **Largest disconnect from PRD**

**Priority**: 🔴 **HIGH** (core feature)

---

### ⚠️ Testing - INADEQUATE Coverage

**Backend Tests**:
- ✅ Auth tested
- ✅ Manifest loading tested
- ✅ Run lifecycle tested
- ❌ Projects router untested
- ❌ Batch runs untested
- ❌ Workflow pipeline untested
- ❌ WebSocket terminal untested

**Frontend Tests**:
- ⚠️ Auth context (outdated - uses localStorage)
- ❌ API client untested
- ❌ Run manager untested
- ❌ Terminal untested
- ❌ Planner untested

**Coverage Estimate**: **~30%**

**PRD Alignment**: **Poor** (testing is critical for PRD quality goals)

---

## Surgical Reboot Strategy

### Phase 0: Critical Fixes (Week 1 - Days 1-2)

**Goal**: Make current code production-stable

**Tasks**:
1. ✅ Keep auth system (perfect as-is)
2. 🔧 Add missing dependencies to requirements.txt
3. 🔧 Add Task.archived migration OR remove usage
4. 🔧 Update frontend tests for cookie auth
5. 🔧 Add APIError.correlationId field
6. 🧪 Verify all servers start without errors

**Success Criteria**: No runtime crashes, tests pass

**Effort**: 2 days

---

### Phase 1: PRD Core Gap - Multi-Agent Workflow (Week 1-2)

**Goal**: Transform prototype into PRD-compliant multi-agent system

**Tasks**:

#### 1.1: Create Separate Agent Definitions (2 days)
```
apps/api/app/agents/
├── __init__.py
├── planner.py       # NEW - "refines prompt into structured plan"
├── coder.py         # NEW - "generates actual code"
├── tester.py        # NEW - "reviews or generates tests"
└── documenter.py    # Phase 2
```

#### 1.2: Implement Prompt Processing (1 day)
```python
# apps/api/app/prompt_processor.py (NEW)
class PromptProcessor:
    def validate(prompt: str) -> ValidationResult:
        """PRD: 'if prompt is too short or ambiguous, warn user'"""
    
    def enhance(prompt: str) -> str:
        """PRD: 'inject system prompts or context to guide agents'"""
```

#### 1.3: Refactor Workflow Pipeline (2 days)
```python
# apps/api/app/workflows/pipeline.py
# ❌ Remove: Same crew for all stages
# ✅ Add: Distinct crews per stage
# ✅ Add: User approval gate after Planner
# ✅ Add: Implement _refine_implementation
# ✅ Add: Proper error handling (no auto-approve)
```

#### 1.4: Update Projects Router (1 day)
```python
# Add endpoints:
POST /projects/{id}/generate      # Trigger AI generation
POST /projects/{id}/regenerate    # Refine with new prompt
GET /projects/{id}/specification  # Get Planner output
GET /projects/{id}/code           # Get Coder output
```

**Success Criteria**: Can run Planner → Coder → Tester as separate agents

**Effort**: 6 days

---

### Phase 2: Frontend PRD Features (Week 2-3)

**Goal**: Build prompt builder & code viewer from PRD

#### 2.1: Prompt Builder UI (3 days)
```typescript
// apps/console/app/prompt-builder/page.tsx (NEW)
// PRD: "Guided Prompt Input with tips or sections"

<PromptBuilder>
  <PromptSection title="Purpose">
    <TextArea placeholder="What are you trying to build?" />
  </PromptSection>
  
  <PromptSection title="Features">
    <BulletList />
  </PromptSection>
  
  <PromptSection title="Tech Stack">
    <TechStackSelector />
  </PromptSection>
  
  <PromptValidation />
  <PromptTemplates />
</PromptBuilder>
```

#### 2.2: Code Viewer Component (3 days)
```typescript
// apps/console/app/components/CodeViewer.tsx (NEW)
// PRD: "user can review each file in our IDE"

<CodeViewer project={generatedProject}>
  <FileTree files={project.files} />
  <CodeEditor file={selectedFile} readOnly />
  <DiffViewer iterations={project.history} />
</CodeViewer>
```

#### 2.3: Iteration UI (2 days)
```typescript
// PRD: "iterative refinement loop"
<IterationPanel>
  <SpecReview spec={planner.output} />
  <ApproveButton onApprove={startCoding} />
  <RefineButton onRefine={showPromptEditor} />
</IterationPanel>
```

**Success Criteria**: Complete prompt → generate → refine flow in UI

**Effort**: 8 days

---

### Phase 3: Testing & Quality (Week 3-4)

**Goal**: Achieve PRD quality standards

#### 3.1: Backend Tests (3 days)
- [ ] Test new multi-agent workflow
- [ ] Test prompt validation
- [ ] Test iteration/refinement
- [ ] Test projects endpoints
- [ ] Test WebSocket terminal

#### 3.2: Frontend Tests (3 days)
- [ ] Fix auth context tests (cookies)
- [ ] Test API client + retries
- [ ] Test run manager
- [ ] Test prompt builder
- [ ] Test code viewer

#### 3.3: Integration Tests (2 days)
- [ ] End-to-end: prompt → code generation
- [ ] End-to-end: refinement loop
- [ ] End-to-end: multi-agent coordination

**Success Criteria**: >70% coverage, all critical paths tested

**Effort**: 8 days

---

### Phase 4: Polish & Launch (Week 4+)

**Goal**: PRD Beta-ready

- [ ] Add prompt templates library
- [ ] Improve error messages
- [ ] Add loading states
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Beta user testing

---

## Migration Checklist

### ✅ Keep (Don't Touch - Already Perfect)

```
✅ apps/api/app/auth.py (320 lines)
✅ apps/api/app/auth_providers/ (entire directory)
✅ apps/api/app/routers/auth*.py (all auth routers)
✅ apps/console/app/state/auth-context.tsx
✅ apps/console/app/lib/api-client.ts
✅ apps/api/app/db/session.py
✅ apps/api/app/core/config.py
✅ All new authentication documentation
```

**Reason**: Just completed, production-ready, don't risk breaking

---

### 🔧 Fix (Critical Issues)

```
🔧 apps/api/requirements.txt
   → Add: apscheduler, redis, prometheus-client
   → Or remove code that uses them

🔧 apps/api/app/db/models.py
   → Add Task.archived field
   → Or fix cleanup.py to not use it

🔧 apps/console/app/state/auth-context.test.tsx
   → Rewrite for cookie-based auth
   → Remove localStorage assumptions

🔧 apps/console/app/lib/api-client.ts
   → Add correlationId to APIError type
```

---

### 🔄 Refactor (Align with PRD)

```
🔄 apps/api/app/workflows/pipeline.py
   → Separate agents per stage
   → Add user approval gates
   → Implement refinement loop
   → Remove auto-approve on errors

🔄 apps/api/app/crew_runner.py
   → Support multiple agent types
   → Dynamic prompt processing
   → Better error handling
```

---

### 🆕 Create (PRD Requirements)

```
🆕 apps/api/app/agents/
   → planner.py
   → coder.py
   → tester.py
   → documenter.py

🆕 apps/api/app/prompt_processor.py
   → Validation
   → Enhancement
   → Template processing

🆕 apps/console/app/prompt-builder/
   → Guided prompt interface
   → Templates library
   → Validation feedback

🆕 apps/console/app/components/CodeViewer.tsx
   → File tree
   → Code display
   → Diff viewer
```

---

### ❌ Remove (Optional Cleanup)

```
❌ apps/console/app/landing/page.tsx
   → Remove non-Praxis tool ads (kyros-lexis, etc.)
   → Or hide behind feature flags

❌ apps/api/app/crews/code_reviewer.py
   → Old single-agent approach
   → Replace with new multi-agent workflow

❌ Placeholder pages
   → Either implement or hide from nav
```

---

## Risk Assessment

### 🔴 High Risk (Address First)

1. **Missing Dependencies** → Server crashes
2. **Schema Mismatch** → Background jobs crash
3. **Outdated Tests** → False security confidence
4. **Single-Agent Workflow** → PRD gap (core feature)

### 🟡 Medium Risk (Address Soon)

1. **Limited Test Coverage** → Bugs in production
2. **No Iteration Loop** → PRD requirement missing
3. **Missing Prompt Builder** → User can't use feature
4. **No Code Viewer** → Can't see generated code

### 🟢 Low Risk (Can Wait)

1. **Placeholder Pages** → Not blocking
2. **Documentation Gaps** → Most docs exist
3. **Performance** → Not mentioned as issue yet

---

## Effort Estimates

| Phase | Tasks | Days | Calendar |
|-------|-------|------|----------|
| Phase 0 | Critical fixes | 2 | Week 1 (Mon-Tue) |
| Phase 1 | Multi-agent workflow | 6 | Week 1-2 (Wed-Wed) |
| Phase 2 | Frontend features | 8 | Week 2-3 (Thu-Thu) |
| Phase 3 | Testing & quality | 8 | Week 3-4 (Fri-Fri) |
| Phase 4 | Polish & launch | 5+ | Week 4+ |
| **Total** | **Core work** | **24 days** | **~5 weeks** |

**Assumptions**: 1 developer, full-time, focused work

**Adjustments**:
- Team of 2: ~3 weeks
- Part-time: ~10 weeks
- With distractions: Add 50% buffer

---

## Success Metrics

### Phase 0 Success
- [ ] No crashes on server startup
- [ ] All tests pass
- [ ] Auth flow validated

### Phase 1 Success (PRD Core)
- [ ] Separate Planner, Coder, Tester agents
- [ ] User can trigger generation via API
- [ ] Workflow produces structured output

### Phase 2 Success (PRD UX)
- [ ] Guided prompt builder UI works
- [ ] Generated code displayed in viewer
- [ ] User can refine and regenerate

### Phase 3 Success (PRD Quality)
- [ ] >70% test coverage
- [ ] All critical paths tested
- [ ] No known critical bugs

### Phase 4 Success (PRD Beta)
- [ ] 5-10 beta users testing
- [ ] Successfully generate 3+ project types
- [ ] Positive user feedback

---

## Recommendations

### Immediate (This Week)

1. **Fix Critical Issues** (Phase 0)
   - Add missing dependencies
   - Fix schema mismatch
   - Update tests
   - **Effort**: 2 days
   - **Impact**: Prevents production crashes

2. **Start Multi-Agent Work** (Phase 1)
   - Create agent definitions
   - Refactor workflow pipeline
   - **Effort**: 6 days
   - **Impact**: Closes largest PRD gap

### Short-term (Next 2 Weeks)

3. **Build Frontend Features** (Phase 2)
   - Prompt builder
   - Code viewer
   - Iteration UI
   - **Effort**: 8 days
   - **Impact**: Enables user testing

### Medium-term (Weeks 3-4)

4. **Testing & Polish** (Phase 3-4)
   - Expand test coverage
   - Beta testing
   - Documentation
   - **Effort**: 10+ days
   - **Impact**: Production readiness

---

## Decision Points

### A. Dependency Strategy

**Option 1**: Add all dependencies
- **Pro**: Full functionality
- **Con**: Larger deployment
- **Effort**: 1 hour (add to requirements.txt)

**Option 2**: Remove unused code
- **Pro**: Simpler, less to maintain
- **Con**: Lose functionality
- **Effort**: 4 hours (remove imports, features)

**Recommendation**: **Option 1** - Add dependencies
- Redis/Prometheus are standard in production
- Features are partially implemented already
- Easier to add than remove

### B. Testing Strategy

**Option 1**: Fix tests incrementally
- **Pro**: Continuous validation
- **Con**: Slower feature development

**Option 2**: Fix tests in Phase 3
- **Pro**: Faster feature delivery
- **Con**: More bugs during development

**Recommendation**: **Hybrid** - Fix critical auth tests now, expand in Phase 3

### C. Workflow Refactor Approach

**Option 1**: Complete rewrite
- **Pro**: Clean PRD alignment
- **Con**: High risk, longer timeline
- **Effort**: 10+ days

**Option 2**: Incremental improvement
- **Pro**: Lower risk, faster
- **Con**: Technical debt remains
- **Effort**: 6 days

**Recommendation**: **Option 2** - Incremental
- Current structure is reasonable
- Refactor piece by piece
- Test continuously

---

## Conclusion

### Current State Summary

**What You Have**:
- ✅ 75-80% of PRD infrastructure exists
- ✅ Enterprise-grade auth (just completed)
- ✅ Solid technical foundation
- ✅ CrewAI integrated
- ✅ Multi-agent database schema
- ✅ Frontend structure ready

**Critical Gaps**:
- 🔴 Missing dependencies (runtime crashes)
- 🔴 Schema mismatches (background jobs fail)
- 🔴 Single-agent workflow (PRD expects multi-agent)
- 🟡 Outdated tests (false confidence)
- 🟡 No prompt builder UI (PRD requirement)
- 🟡 No code viewer (PRD requirement)

### Recommendation

**Strategy**: **Surgical Reboot** (not full reboot)

**Keep**: 90% of existing code (it's good!)

**Fix**: Critical issues (2 days)

**Refactor**: Workflow pipeline (6 days)

**Add**: PRD-specific features (8 days)

**Test**: Comprehensive quality assurance (8 days)

**Timeline**: ~5 weeks to PRD Beta

**Confidence**: 🟢 **HIGH** - Foundation is solid, clear path forward

---

## Next Actions

### Immediate (Do Now)

1. **Review this analysis** with team
2. **Decide on dependencies** (add or remove?)
3. **Prioritize** Phase 0 vs Phase 1
4. **Assign** tasks if team available

### First Steps (Today)

```bash
# 1. Fix dependencies
cd /home/thomas/kyros-praxis/apps/api
echo "apscheduler==3.10.4" >> requirements.txt
echo "redis==5.0.1" >> requirements.txt
echo "prometheus-client==0.19.0" >> requirements.txt

# 2. Create Phase 0 branch
git checkout -b fix/critical-issues

# 3. Start with schema fix
# Create migration for Task.archived

# 4. Fix auth tests
cd /home/thomas/kyros-praxis/apps/console
# Update auth-context.test.tsx
```

### Track Progress

Use this checklist:

**Phase 0: Critical Fixes**
- [ ] Add dependencies OR remove unused code
- [ ] Fix Task.archived issue
- [ ] Update auth tests for cookies
- [ ] Add APIError.correlationId
- [ ] Verify no crashes

**Phase 1: Multi-Agent Core**
- [ ] Create agent definitions (planner, coder, tester)
- [ ] Implement prompt processor
- [ ] Refactor workflow pipeline
- [ ] Add multi-agent endpoints
- [ ] Test agent coordination

**Phase 2: Frontend Features**
- [ ] Build prompt builder UI
- [ ] Build code viewer component
- [ ] Add iteration/refinement UI
- [ ] Connect to backend endpoints

**Phase 3: Testing**
- [ ] Fix all existing tests
- [ ] Add workflow tests
- [ ] Add frontend tests
- [ ] Integration tests

**Phase 4: Launch**
- [ ] Beta testing
- [ ] Documentation
- [ ] Performance optimization
- [ ] Production deployment

---

**Status**: Ready for surgical reboot  
**Confidence**: High (solid foundation)  
**Timeline**: 5 weeks to PRD Beta  
**Risk**: Medium (manageable with plan)

**Let's proceed!** 🚀
