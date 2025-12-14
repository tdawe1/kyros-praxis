# Integration Verification - Agents A & B

**Date**: Day 14  
**Status**: Both agents complete, starting integration testing  
**Goal**: Verify PRD Beta readiness

---

## Pre-Integration Status

### Agent A (Backend) - COMPLETE ✅
- Multi-agent system (planner, coder, tester)
- Prompt processor (validation, enhancement)
- Workflow pipeline (PRD-compliant)
- 6 API endpoints implemented
- 78/78 tests passing
- >95% test coverage
- API-CONTRACT.md documentation

### Agent B (Frontend) - COMPLETE ✅
- Prompt builder (wired to API)
- Code viewer (live)
- Iteration/refinement UI (connected)
- Auth tests (cookie-based)
- correlationId support
- All components functional

---

## Integration Test Checklist

### 1. Server Startup ✓

**Backend**:
```bash
cd apps/api
../.venv/bin/uvicorn app.main:app --reload --port 8000
```
**Expected**: Server starts, no errors, health check responds

**Frontend**:
```bash
cd apps/console
npm run dev
```
**Expected**: Next.js starts, no errors, accessible at http://localhost:3000

---

### 2. API Connectivity Test

**Test**: Frontend can reach backend
```bash
# Frontend should be able to:
curl http://localhost:8000/health
curl http://localhost:8000/projects
```

**Verify**:
- [ ] CORS headers allow console.localhost
- [ ] Cookies sent with credentials: 'include'
- [ ] Auth working between services

---

### 3. Complete User Flow Test

#### Step 1: Login
- [ ] User can access login page
- [ ] Login sets httpOnly cookies
- [ ] Auth context updates correctly
- [ ] Redirect to dashboard works

#### Step 2: Create Project
- [ ] Click "New Project" button
- [ ] Fill project name/description
- [ ] POST /projects creates project
- [ ] Redirects to project page

#### Step 3: Submit Prompt (Planner Stage)
- [ ] Prompt builder UI displays
- [ ] User enters detailed prompt
- [ ] Validation runs client-side
- [ ] POST /projects/{id}/generate called
- [ ] Loading state shows
- [ ] Specification returned
- [ ] Validation score displayed

**Expected Backend Flow**:
```
1. Receive prompt
2. Validate (score 0-100)
3. Enhance with system context
4. Run planner agent
5. Return specification
6. Status: "awaiting_approval"
```

**Expected Frontend Flow**:
```
1. Submit prompt
2. Show loading spinner
3. Receive specification
4. Display in review component
5. Show approve/reject buttons
```

#### Step 4: Review Specification
- [ ] Specification displays in structured format
- [ ] All 9 sections visible:
  - Purpose
  - Components
  - Technology
  - File Structure
  - Dependencies
  - Data Models
  - Implementation Plan
  - Testing Considerations
  - Challenges
- [ ] User can read each section
- [ ] Approve button enabled
- [ ] Refine button enabled

#### Step 5: Approve Specification (Coder + Tester Stage)
- [ ] Click "Approve" button
- [ ] POST /projects/{id}/approve called
- [ ] Loading state shows (this takes longer)
- [ ] Progress indication (if available)
- [ ] Code files returned
- [ ] Test files returned
- [ ] Review results included

**Expected Backend Flow**:
```
1. Receive approval
2. Run coder agent with spec
3. Generate code files
4. Run tester agent with code
5. Review and create tests
6. Store artifacts
7. Return everything
8. Status: "completed"
```

**Expected Frontend Flow**:
```
1. Submit approval
2. Show "Generating code..." loading
3. Receive code + tests
4. Switch to code viewer
5. Display file tree
6. Show first file by default
```

#### Step 6: View Generated Code
- [ ] Code viewer displays
- [ ] File tree shows all files
- [ ] Code files organized by path
- [ ] Test files separate section
- [ ] Click file to view
- [ ] Syntax highlighting works
- [ ] Line numbers display
- [ ] Copy button functional
- [ ] Can switch between files

#### Step 7: Refine/Iterate
- [ ] "Refine" button visible
- [ ] Click opens refinement input
- [ ] User enters refinement notes
- [ ] POST /projects/{id}/regenerate called
- [ ] New iteration starts
- [ ] Can see what changed (diff)
- [ ] Max 3 iterations enforced

---

### 4. API Endpoint Verification

Test each endpoint independently:

#### ✓ POST /projects/{id}/generate
```bash
curl -X POST http://localhost:8000/projects/{id}/generate \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=..." \
  -d '{"prompt":"Build a todo app with React and FastAPI"}'
```
**Expected**: 
- Status: 202
- Returns: workflow_id, status="awaiting_approval", specification
- Validation score included

#### ✓ POST /projects/{id}/approve
```bash
curl -X POST http://localhost:8000/projects/{id}/approve \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=..." \
  -d '{"approved":true,"specification":{...}}'
```
**Expected**:
- Status: 200
- Returns: code_files[], test_files[], review{}

#### ✓ POST /projects/{id}/regenerate
```bash
curl -X POST http://localhost:8000/projects/{id}/regenerate \
  -H "Content-Type: application/json" \
  -H "Cookie: access_token=..." \
  -d '{"refinement_notes":"Add dark mode"}'
```
**Expected**:
- Status: 200
- Returns: new workflow_id, iteration incremented

#### ✓ GET /projects/{id}/specification
```bash
curl http://localhost:8000/projects/{id}/specification \
  -H "Cookie: access_token=..."
```
**Expected**:
- Status: 200
- Returns: specification object

#### ✓ GET /projects/{id}/code
```bash
curl http://localhost:8000/projects/{id}/code \
  -H "Cookie: access_token=..."
```
**Expected**:
- Status: 200
- Returns: code_files[], test_files[], total_files

#### ✓ GET /projects/{id}/status
```bash
curl http://localhost:8000/projects/{id}/status \
  -H "Cookie: access_token=..."
```
**Expected**:
- Status: 200
- Returns: project_status, stages[]

---

### 5. Error Handling Tests

#### Test Invalid Prompt
- [ ] Submit very short prompt ("hi")
- [ ] Backend returns validation error
- [ ] Frontend displays validation feedback
- [ ] User can see issues and suggestions

#### Test Network Error
- [ ] Stop backend server
- [ ] Try to submit prompt
- [ ] Frontend shows connection error
- [ ] Provides retry option

#### Test Auth Error
- [ ] Clear auth cookies
- [ ] Try to use workflow
- [ ] Gets 401 Unauthorized
- [ ] Redirects to login

#### Test Max Iterations
- [ ] Complete workflow 3 times (refine 3x)
- [ ] Try 4th refinement
- [ ] Should prevent or warn
- [ ] Max iterations message shown

---

### 6. Performance Verification

**Timing Tests** (in simulation mode):

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Prompt validation | <100ms | | |
| Planner agent | <60s | | |
| Coder agent | <120s | | |
| Tester agent | <60s | | |
| Get code | <500ms | | |
| Total workflow | <300s | | |

**Note**: Real CrewAI execution will be slower. These are simulation targets.

---

### 7. Data Validation

**Check Database**:
```sql
-- Projects created
SELECT * FROM projects;

-- Workflow stages recorded
SELECT * FROM workflow_stages;

-- Artifacts stored
SELECT * FROM artifacts;

-- Workflow progression
SELECT stage, status FROM workflow_stages 
ORDER BY started_at;
```

**Verify**:
- [ ] Project records created
- [ ] Workflow stages tracked
- [ ] Artifacts stored with correct type (code/test)
- [ ] Stage progression recorded

---

### 8. UI/UX Verification

**Prompt Builder**:
- [ ] Guided input sections clear
- [ ] Validation feedback helpful
- [ ] Templates accessible
- [ ] Submit button state correct
- [ ] Loading states smooth

**Specification Review**:
- [ ] Spec readable and formatted
- [ ] Sections clearly labeled
- [ ] Approve/Reject buttons obvious
- [ ] Can scroll through content

**Code Viewer**:
- [ ] File tree intuitive
- [ ] Syntax highlighting readable
- [ ] Copy button works
- [ ] Can navigate between files
- [ ] Test files clearly separated

**Iteration UI**:
- [ ] Refine button accessible
- [ ] Refinement input clear
- [ ] Diff viewer shows changes
- [ ] Iteration count visible

---

## Issues to Watch For

### Potential Backend Issues
1. **Timeout on agent execution** - CrewAI might take longer than expected
2. **Database connection issues** - Postgres connection pool
3. **Memory with large specs** - Large specifications or code outputs
4. **CORS misconfig** - Cross-origin issues between frontend/backend

### Potential Frontend Issues
1. **Auth cookies** - Cookie domain/path issues
2. **Large code rendering** - Syntax highlighting performance
3. **State management** - Workflow state consistency
4. **Error display** - correlationId visibility

### Integration Issues
1. **Type mismatches** - API contract vs actual responses
2. **Timing issues** - Race conditions in async operations
3. **Error propagation** - Backend errors not reaching frontend
4. **Session handling** - Cookie expiry during long operations

---

## Bug Fix Protocol

**If Issue Found**:

1. **Document**:
   - What happened
   - Expected vs actual behavior
   - Steps to reproduce
   - Error messages/logs

2. **Classify**:
   - 🔴 Blocking: Prevents workflow completion
   - 🟡 Major: Impacts user experience
   - 🟢 Minor: Cosmetic or edge case

3. **Assign**:
   - Backend issue → Agent A fixes
   - Frontend issue → Agent B fixes
   - Integration issue → Both agents coordinate

4. **Test Fix**:
   - Verify fix resolves issue
   - Run relevant tests
   - Check for regressions

5. **Document Resolution**:
   - Update integration notes
   - Add test if needed

---

## Success Criteria

### Minimum (Must Have)
- [ ] User can submit prompt
- [ ] Specification displays correctly
- [ ] User can approve specification
- [ ] Code generates and displays
- [ ] Basic error handling works
- [ ] No crashes or data loss

### Standard (Should Have)
- [ ] All 6 endpoints working
- [ ] Refinement loop functional
- [ ] Validation feedback helpful
- [ ] Performance acceptable (<5 min total)
- [ ] Proper error messages with correlationId

### Excellent (Nice to Have)
- [ ] Diff viewer shows iterations
- [ ] Template library accessible
- [ ] Export code functionality
- [ ] Real-time progress updates
- [ ] Smooth, polished UX

---

## Final Verification Steps

### Step 1: Start Services
```bash
# Terminal 1: Backend
cd /home/thomas/kyros-praxis/apps/api
../.venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd /home/thomas/kyros-praxis/apps/console
npm run dev
```

### Step 2: Manual Testing
1. Open http://localhost:3000
2. Login as test user
3. Create new project
4. Go through complete workflow
5. Test refinement
6. Verify all components

### Step 3: Automated API Tests
```bash
# Run from project root
cd /home/thomas/kyros-praxis/apps/api
../.venv/bin/pytest tests/ -v
```

### Step 4: Frontend Tests
```bash
cd /home/thomas/kyros-praxis/apps/console
npm test
```

### Step 5: Integration Sign-off
- [ ] Agent A: Backend verified ✅
- [ ] Agent B: Frontend verified ✅
- [ ] Joint: E2E flow works ✅
- [ ] **PRD Beta Ready** 🎉

---

**Status**: Ready to begin integration testing  
**Next**: Test end-to-end workflow
