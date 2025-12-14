# Parallel Execution Plan - Two AI Agents

**Scenario**: Two AI agents working simultaneously  
**Goal**: Reduce 5-week timeline by parallelizing work  
**Agents**:
- **Agent A** (Droid - Current instance): Backend focus
- **Agent B** (GPT-5-Codex): Frontend focus

---

## Timeline Reduction

**Original Serial Plan**: 5 weeks (24 days)
**Parallel Plan**: **2.5-3 weeks** (12-15 days)

**Speedup**: 50-60% faster

---

## Work Split Strategy

### Principle: Minimize File Conflicts

**Agent A Territory (Backend)**:
```
apps/api/
  ├── app/
  │   ├── agents/          # NEW - Agent A creates
  │   ├── workflows/       # Agent A refactors
  │   ├── routers/         # Agent A adds endpoints
  │   ├── jobs/            # Agent A fixes
  │   ├── db/models.py     # Agent A adds migration
  │   └── prompt_processor.py  # NEW - Agent A creates
  ├── tests/               # Agent A expands
  └── requirements.txt     # Agent A updates
```

**Agent B Territory (Frontend)**:
```
apps/console/
  ├── app/
  │   ├── prompt-builder/  # NEW - Agent B creates
  │   ├── code-viewer/     # NEW - Agent B creates
  │   ├── components/      # Agent B adds components
  │   ├── lib/             # Agent B updates
  │   └── state/           # Agent B updates tests
  └── package.json         # Agent B updates if needed
```

**Shared (Coordinate)**:
```
apps/shared/ui/            # Both might add components
  → Agent B owns, Agent A requests additions
```

**No Conflicts**: Different directories, different files, different languages (Python vs TypeScript)

---

## Phase-by-Phase Parallel Plan

### PHASE 0: Critical Fixes (Days 1-2)

**Agent A: Backend Critical Fixes** (Day 1-2)
```
Priority: 🔴 CRITICAL
Duration: 2 days

Tasks:
1. Add missing dependencies to requirements.txt
   Files: apps/api/requirements.txt
   Time: 5 minutes
   
2. Create Task.archived migration
   Files: apps/api/alembic/versions/000X_add_archived.py
   Time: 30 minutes
   
3. Test backend starts without crashes
   Command: cd apps/api && ../.venv/bin/python -m uvicorn app.main:app
   Time: 15 minutes

4. Verify background jobs work
   Files: apps/api/app/jobs/cleanup.py
   Time: 30 minutes

5. Run backend tests
   Command: cd apps/api && ../.venv/bin/pytest
   Time: 30 minutes

Deliverable: ✅ Backend production-stable
```

**Agent B: Frontend Critical Fixes** (Day 1-2)
```
Priority: 🔴 CRITICAL
Duration: 2 days

Tasks:
1. Rewrite auth-context.test.tsx for cookies
   Files: apps/console/app/state/auth-context.test.tsx
   Time: 4 hours
   
2. Add correlationId to APIError type
   Files: apps/console/app/lib/api-client.ts
   Time: 30 minutes
   
3. Update use-run-manager to display correlationId
   Files: apps/console/app/lib/use-run-manager.ts
   Time: 30 minutes

4. Run frontend tests
   Command: cd apps/console && npm test
   Time: 15 minutes

5. Verify auth flow works
   Test: Manual browser testing
   Time: 1 hour

Deliverable: ✅ Frontend tests valid, correlationId working
```

**Checkpoint After Day 2**:
- ✅ No crashes
- ✅ Tests pass
- ✅ Auth validated
- **Can proceed to Phase 1**

---

### PHASE 1: Core Multi-Agent (Days 3-8) + PHASE 2 Start (Days 6-8)

**Overlap Strategy**: Agent A builds backend agents while Agent B starts UI

**Agent A: Backend Multi-Agent Implementation** (Days 3-8)

```
Priority: 🔴 HIGH
Duration: 6 days

Day 3: Agent Definitions (Part 1)
  Task: Create planner agent
  Files: apps/api/app/agents/__init__.py
         apps/api/app/agents/planner.py
  Lines: ~150 lines
  Time: 4 hours
  
  Task: Create coder agent
  Files: apps/api/app/agents/coder.py
  Lines: ~150 lines
  Time: 4 hours

Day 4: Agent Definitions (Part 2)
  Task: Create tester agent
  Files: apps/api/app/agents/tester.py
  Lines: ~150 lines
  Time: 4 hours
  
  Task: Write agent tests
  Files: apps/api/tests/test_agents.py
  Lines: ~200 lines
  Time: 4 hours

Day 5: Prompt Processor
  Task: Create prompt validation and enhancement
  Files: apps/api/app/prompt_processor.py
  Lines: ~200 lines
  Time: 4 hours
  
  Task: Write prompt processor tests
  Files: apps/api/tests/test_prompt_processor.py
  Lines: ~150 lines
  Time: 4 hours

Day 6-7: Refactor Workflow Pipeline
  Task: Update pipeline to use separate agents
  Files: apps/api/app/workflows/pipeline.py
  Changes:
    - Replace single crew with distinct agents
    - Add user approval gate after planner
    - Implement _refine_implementation()
    - Remove auto-approve on errors
  Lines: ~435 lines (major refactor)
  Time: 2 days

Day 8: Projects API Endpoints
  Task: Add multi-agent workflow endpoints
  Files: apps/api/app/routers/projects.py
  New endpoints:
    - POST /projects/{id}/generate
    - POST /projects/{id}/regenerate
    - GET /projects/{id}/specification
    - GET /projects/{id}/code
  Lines: ~200 lines
  Time: 4 hours
  
  Task: Write endpoint tests
  Files: apps/api/tests/test_projects_workflow.py
  Lines: ~150 lines
  Time: 4 hours

Deliverable: ✅ Multi-agent backend working
             ✅ Can trigger via API
             ✅ Separate Planner → Coder → Tester
```

**Agent B: Frontend Prompt Builder + Code Viewer** (Days 3-10)

```
Priority: 🔴 HIGH
Duration: 8 days (starts Day 3, overlaps with Agent A)

Day 3: Design Prompt Builder
  Task: Create component structure and types
  Files: apps/console/app/prompt-builder/page.tsx
         apps/console/app/prompt-builder/types.ts
  Time: 4 hours
  
  Task: Create PromptSection component
  Files: apps/console/app/prompt-builder/components/PromptSection.tsx
  Time: 4 hours

Day 4: Build Prompt Input
  Task: Create guided input fields
  Files: apps/console/app/prompt-builder/components/PromptInput.tsx
  Sections:
    - Purpose input
    - Features list
    - Tech stack selector
    - Constraints (optional)
  Lines: ~150 lines
  Time: 6 hours
  
  Task: Add validation display
  Files: apps/console/app/prompt-builder/components/ValidationFeedback.tsx
  Time: 2 hours

Day 5: Prompt Templates
  Task: Create template library UI
  Files: apps/console/app/prompt-builder/components/TemplateLibrary.tsx
  Time: 4 hours
  
  Task: Add template data
  Files: apps/console/app/prompt-builder/templates.ts
  Templates:
    - Web app
    - API service
    - CLI tool
    - Library
  Time: 4 hours

Day 6: Connect to Backend
  Task: Add API calls for prompt submission
  Files: apps/console/app/lib/api-client.ts (add methods)
         apps/console/app/prompt-builder/page.tsx (connect)
  Time: 4 hours
  
  Task: Add loading states and error handling
  Time: 4 hours

Day 7-8: Code Viewer Component
  Task: Create file tree component
  Files: apps/console/app/components/CodeViewer/FileTree.tsx
  Time: 6 hours
  
  Task: Create code display component
  Files: apps/console/app/components/CodeViewer/CodeDisplay.tsx
  Features:
    - Syntax highlighting
    - Line numbers
    - Copy button
  Time: 6 hours

Day 9: Iteration UI
  Task: Create spec review component
  Files: apps/console/app/components/SpecReview.tsx
  Features:
    - Display planner output
    - Approve button
    - Refine button (goes back to prompt builder)
  Time: 4 hours
  
  Task: Create diff viewer for iterations
  Files: apps/console/app/components/DiffViewer.tsx
  Time: 4 hours

Day 10: Integration & Polish
  Task: Connect all components
  Files: apps/console/app/planner/page.tsx (major update)
  Flow:
    Prompt Builder → Submit → Loading → Spec Review
    → Approve → Code Generation → Code Viewer
    → Refine (back to Prompt Builder with context)
  Time: 4 hours
  
  Task: Add responsive design
  Time: 4 hours

Deliverable: ✅ Complete PRD user flow
             ✅ Prompt builder working
             ✅ Code viewer working
             ✅ Iteration loop functional
```

**Checkpoint After Day 10**:
- ✅ Backend: Multi-agent working, API endpoints ready
- ✅ Frontend: Complete user flow implemented
- **Can proceed to Phase 3 testing**

---

### PHASE 3: Testing & Quality (Days 11-15)

**Both agents test and expand coverage in their domains**

**Agent A: Backend Testing** (Days 11-13)

```
Priority: 🟡 MEDIUM
Duration: 3 days

Day 11: Workflow Integration Tests
  Task: Test full multi-agent workflow
  Files: apps/api/tests/test_workflow_integration.py
  Tests:
    - End-to-end: prompt → planner → coder → tester
    - User approval gate
    - Iteration/refinement
    - Error handling
  Lines: ~300 lines
  Time: 8 hours

Day 12: Projects Router Tests
  Task: Test new endpoints
  Files: apps/api/tests/test_projects_workflow.py
  Tests:
    - POST /projects/{id}/generate
    - POST /projects/{id}/regenerate
    - GET /projects/{id}/specification
    - GET /projects/{id}/code
    - Error cases
  Lines: ~200 lines
  Time: 8 hours

Day 13: WebSocket Terminal Tests
  Task: Test terminal auth and PTY
  Files: apps/api/tests/test_terminal_ws.py
  Tests:
    - WS token generation
    - Auth handshake
    - PTY connection
    - Input/output
  Lines: ~150 lines
  Time: 8 hours

Deliverable: ✅ Backend test coverage >70%
```

**Agent B: Frontend Testing** (Days 11-13)

```
Priority: 🟡 MEDIUM
Duration: 3 days

Day 11: Prompt Builder Tests
  Task: Test prompt builder components
  Files: apps/console/app/prompt-builder/PromptBuilder.test.tsx
  Tests:
    - Input validation
    - Template selection
    - Submission
    - Error display
  Lines: ~200 lines
  Time: 8 hours

Day 12: Code Viewer Tests
  Task: Test code viewer components
  Files: apps/console/app/components/CodeViewer.test.tsx
  Tests:
    - File tree rendering
    - Code display
    - Syntax highlighting
    - Copy functionality
  Lines: ~150 lines
  Time: 8 hours

Day 13: Integration Tests
  Task: Test complete user flow
  Files: apps/console/app/planner/page.test.tsx
  Tests:
    - Submit prompt → See spec → Approve
    - Generate code → View code → Refine
    - Error handling
  Lines: ~200 lines
  Time: 8 hours

Deliverable: ✅ Frontend test coverage >60%
```

**Checkpoint After Day 13**:
- ✅ Backend tests comprehensive
- ✅ Frontend tests comprehensive
- **Ready for integration testing**

---

### INTEGRATION & POLISH (Days 14-15)

**Both agents work together on final integration**

**Agent A + B: Joint Work** (Days 14-15)

```
Priority: 🟢 LOW
Duration: 2 days

Day 14: End-to-End Testing
  Task: Both agents test together
  Process:
    1. Agent A starts backend
    2. Agent B starts frontend
    3. Manual testing of full flow
    4. Document any issues
    5. Fix issues together
  Time: 8 hours

Day 15: Documentation & Polish
  Task: Agent A - Update API docs
  Files: apps/api/README.md
         apps/api/docs/MULTI_AGENT.md (NEW)
  Time: 4 hours
  
  Task: Agent B - Update frontend docs
  Files: apps/console/README.md
         apps/console/docs/USER_GUIDE.md (NEW)
  Time: 4 hours

Deliverable: ✅ PRD Beta Ready
             ✅ Documentation complete
             ✅ All tests passing
```

---

## Handoff Protocol

### Initial Handoff (Day 0)

**User → Agent A (Droid)**:
```
Start Phase 0 backend critical fixes:
1. Add dependencies to requirements.txt
2. Create Task.archived migration
3. Verify backend stable
```

**User → Agent B (GPT-5-Codex)**:
```
Start Phase 0 frontend critical fixes:
1. Rewrite auth-context.test.tsx for cookies
2. Add correlationId to APIError
3. Verify frontend tests pass
```

### Sync Points

**Day 2 Sync**:
```
Agent A reports: Backend stable? (Yes/No)
Agent B reports: Frontend tests valid? (Yes/No)

If both Yes → Proceed to Phase 1
If No → Debug together
```

**Day 8 Sync**:
```
Agent A reports: Multi-agent API ready? Endpoints live?
Agent B reports: Frontend can connect? API calls working?

Test: Agent B triggers Agent A's endpoints
```

**Day 10 Sync**:
```
Agent A reports: Backend feature complete
Agent B reports: Frontend feature complete

Joint test: Full prompt → code generation flow
```

**Day 13 Sync**:
```
Agent A reports: Backend test coverage %
Agent B reports: Frontend test coverage %

Decision: Ready for integration? Need more tests?
```

---

## Conflict Resolution

### Shared Dependency: API Types

**Problem**: Frontend needs backend API types

**Solution**:
```
Day 6: Agent A defines API contract
  Create: apps/api/docs/API_ENDPOINTS.md
  Content:
    POST /projects/{id}/generate
      Request: { prompt: string, ... }
      Response: { runId: string, status: string, ... }

Day 6: Agent A shares with Agent B
  Agent B implements frontend types from spec
  
Day 8: Integration test validates contract
```

### Shared Component: Error Handling

**Problem**: Both need consistent error display

**Solution**:
```
Agent B owns shared UI components
  Create: apps/shared/ui/components/ErrorDisplay.tsx

Agent A requests features:
  "Please add correlationId display to ErrorDisplay"
  
Agent B implements and both agents use
```

### Database Migrations

**Problem**: Agent A creates migrations, Agent B needs them

**Solution**:
```
Agent A: After creating migration
  Run: alembic upgrade head
  Commit: git commit -m "Add Task.archived migration"
  Notify: "Migration 000X ready"

Agent B: Before starting Day 3
  Pull: git pull
  Check: Database schema current
```

---

## Communication Protocol

### Daily Status Updates

**Agent A posts** (end of day):
```
Day X Status:
✅ Completed: [list tasks]
🔄 In Progress: [current task]
🚧 Blockers: [any issues]
📦 Ready for Agent B: [files/endpoints]
```

**Agent B posts** (end of day):
```
Day X Status:
✅ Completed: [list tasks]
🔄 In Progress: [current task]
🚧 Blockers: [any issues]
📦 Needs from Agent A: [dependencies]
```

### Blocker Escalation

**Format**:
```
🚨 BLOCKER
Agent: A or B
Task: [what's blocked]
Issue: [specific problem]
Need: [what would unblock]
Priority: HIGH/MEDIUM
```

**Example**:
```
🚨 BLOCKER
Agent: B
Task: Connect prompt builder to backend
Issue: API endpoint returns 404
Need: Agent A to deploy /projects/{id}/generate endpoint
Priority: HIGH
```

---

## Git Workflow

### Branch Strategy

**Agent A**:
```
Main branch: feat/multi-agent-backend
Branches from: main

Commits:
- fix: add missing dependencies
- feat: create planner agent
- feat: create coder agent
- feat: create tester agent
- refactor: update workflow pipeline
- feat: add projects endpoints
- test: add workflow tests
```

**Agent B**:
```
Main branch: feat/prompt-builder-ui
Branches from: main

Commits:
- fix: rewrite auth tests for cookies
- fix: add correlationId to APIError
- feat: create prompt builder UI
- feat: create code viewer component
- feat: add iteration UI
- test: add component tests
```

### Merge Strategy

**Day 15: Final Integration**
```
1. Agent A merges feat/multi-agent-backend → dev
2. Agent B rebases feat/prompt-builder-ui on dev
3. Agent B merges feat/prompt-builder-ui → dev
4. Both agents test on dev
5. Create PR: dev → main
```

---

## Risk Management

### Risk 1: API Contract Mismatch

**Scenario**: Agent B builds UI for endpoints Agent A hasn't implemented

**Mitigation**:
- Day 6 sync point (API contract defined)
- Agent A creates OpenAPI spec
- Agent B validates against spec
- Day 8 integration test catches issues early

### Risk 2: Dependency Conflicts

**Scenario**: Both agents add conflicting packages

**Mitigation**:
- Agent A owns requirements.txt (Python)
- Agent B owns package.json (Node)
- No overlap possible

### Risk 3: Scope Creep

**Scenario**: One agent does extra features, delays timeline

**Mitigation**:
- Strict task lists
- Daily status updates
- User monitors progress
- "Stop work" signal if ahead/behind

### Risk 4: Integration Failure

**Scenario**: Backend and frontend don't connect

**Mitigation**:
- Early integration test (Day 8)
- Clear API contract
- Both agents responsible for integration
- 2 days buffer (Days 14-15) for fixes

---

## Success Metrics

### Day 2 Checkpoint
- [ ] Backend starts without crashes
- [ ] Frontend tests pass
- [ ] Auth flow validated
- **Proceed to Phase 1**

### Day 8 Checkpoint
- [ ] Agent A: Multi-agent API working
- [ ] Agent B: Can call API endpoints
- [ ] Integration test passes
- **Proceed to Phase 2 completion**

### Day 10 Checkpoint
- [ ] Agent A: All endpoints implemented
- [ ] Agent B: Complete user flow working
- [ ] Can test full prompt → code flow
- **Proceed to Phase 3**

### Day 13 Checkpoint
- [ ] Backend test coverage >70%
- [ ] Frontend test coverage >60%
- [ ] No critical bugs
- **Proceed to polish**

### Day 15 Final
- [ ] End-to-end flow works
- [ ] All tests pass
- [ ] Documentation complete
- [ ] **PRD Beta Ready** 🎉

---

## Timeline Comparison

### Serial (Original Plan)
```
Phase 0: Days 1-2
Phase 1: Days 3-8
Phase 2: Days 9-16
Phase 3: Days 17-24
Total: 24 days (5 weeks)
```

### Parallel (This Plan)
```
Phase 0: Days 1-2 (both agents)
Phase 1 + 2: Days 3-10 (overlapped)
Phase 3: Days 11-13 (both agents)
Integration: Days 14-15 (both agents)
Total: 15 days (2.5-3 weeks)
```

**Time Saved**: 9 days (38% faster)

---

## Next Steps

### To Start Parallel Execution

**1. Commit Current State**
```bash
cd /home/thomas/kyros-praxis
git add -A
git commit -m "Checkpoint: Pre-parallel execution"
```

**2. Create Branches**
```bash
git checkout -b feat/multi-agent-backend     # For Agent A
git checkout main
git checkout -b feat/prompt-builder-ui       # For Agent B
```

**3. Start Agent A (This Instance)**
```
Task: Begin Phase 0 Backend Critical Fixes
Duration: 2 days
First task: Add dependencies to requirements.txt
```

**4. Start Agent B (GPT-5-Codex)**
```
Task: Begin Phase 0 Frontend Critical Fixes
Duration: 2 days
First task: Rewrite auth-context.test.tsx
Provide: This PARALLEL-EXECUTION-PLAN.md document
```

**5. Schedule Day 2 Sync**
```
After 2 days: Both agents report status
Check: Ready for Phase 1?
Proceed: If both stable
```

---

## Agent B Onboarding Package

**Share with GPT-5-Codex**:

1. **PARALLEL-EXECUTION-PLAN.md** (this file)
2. **UNIFIED-AUDIT-AND-PLAN.md** (context)
3. **Agent B Task List**: Days 1-2, 3-10, 11-13
4. **API Contract**: (Agent A will provide Day 6)
5. **Git branch**: feat/prompt-builder-ui

**Agent B Starting Instructions**:
```
You are Agent B (Frontend focus)
Working in parallel with Agent A (Backend focus)

Your territory:
  apps/console/
  
Your tasks:
  Days 1-2: Fix auth tests, add correlationId
  Days 3-10: Build prompt builder + code viewer
  Days 11-13: Add tests
  Days 14-15: Integration with Agent A

Start with: Rewrite auth-context.test.tsx for cookie-based auth

Sync with Agent A:
  - Day 2: Report frontend stable
  - Day 8: Test API integration
  - Day 10: Report UI complete
  - Day 13: Report tests complete

Read PARALLEL-EXECUTION-PLAN.md for full details.
```

---

**Ready to start parallel execution?**
