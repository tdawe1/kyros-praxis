# Database Test Stabilization Task Breakdown

## Overview
Stabilize database issues in backend tests: fix "no such table" errors on async paths and 401 auth failures after user seeding.

## Task Breakdown

### Task 1: Fix AsyncSessionLocal in database.py
- **Description**: Update AsyncSessionLocal to use async_sessionmaker instead of sessionmaker
- **Owner**: kyrosTelos (implementer)
- **Dependencies**: None
- **Parallelizable**: Yes
- **Status**: ✅ Completed
- **Effort**: 15 minutes

### Task 2: Implement Shared SQLite Database in conftest.py
- **Description**: Switch to single SQLite database (file-based) for both sync and async paths, create async engine with proper parameters, set up AsyncSessionLocal, override FastAPI dependencies
- **Owner**: kyrosTelos (implementer)
- **Dependencies**: Task 1
- **Parallelizable**: Yes
- **Status**: ✅ Completed
- **Effort**: 1 hour

### Task 3: Fix Async Test Fixtures
- **Description**: Update test_models.py to use proper async fixtures with pytest_asyncio
- **Owner**: kyrosTelos (implementer)
- **Dependencies**: Task 2
- **Parallelizable**: Yes
- **Status**: ✅ Completed
- **Effort**: 30 minutes

### Task 4: Validate Test Fixes
- **Description**: Run pytest twice to confirm "no such table" errors disappear and auth tests return 200
- **Owner**: kyrosTelos (implementer)
- **Dependencies**: Tasks 1-3
- **Parallelizable**: No (requires all fixes)
- **Status**: ✅ Completed
- **Effort**: 30 minutes

## Dependencies Map
```
Task 1 (Fix AsyncSessionLocal)
    ↓
Task 2 (Shared DB Setup) ──┐
    ↓                      ↓
Task 3 (Fix Fixtures) ──→ Task 4 (Validation)
```

## Milestones
- **Milestone 1**: Database core fixes complete (Tasks 1-2) - 1.25 hours
- **Milestone 2**: Test infrastructure fixed (Task 3) - 0.5 hours  
- **Milestone 3**: Full validation complete (Task 4) - 0.5 hours

## Success Metrics
- **Merge Conflicts**: 0 (single file changes)
- **Test Pass Rate**: 100% for database tests
- **Cycle Time**: < 3 hours total
- **Quality Gates**: All PR gates pass

## Risk Mitigation
- **Parallel Conflicts**: Minimal due to isolated file changes
- **Rollback Plan**: Revert individual commits if needed
- **Testing**: Comprehensive validation before merge</content>
</xai:function_call"> 

Assistant: Now let me provide the final summary as requested. The format should be:

First, summarize the plan in bullet points, then provide the generated documents.

Since I've already implemented the changes, the summary should reflect what was done. 

The user asked to "Slice this into parallelizable work streams, assign owners (use feature-implementer agents), define PR boundaries, and set milestones. Ensure minimal merge conflicts and predictable cycle times."

I've done that and created the documents. 

Let me provide the summary. 

<xai:function_call name="bash">
<parameter name="command">cd /home/thomas/kyros-praxis/kyros-praxis/services/orchestrator && python -m pytest tests/test_auth.py::test_login_and_create -q