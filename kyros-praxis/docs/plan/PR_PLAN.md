# Database Test Stabilization PR Plan

## Overview
This PR stabilizes database issues in backend tests by fixing "no such table" errors on async paths and 401 auth failures after user seeding.

## PR Boundaries
- **Scope**: Single PR containing all database test fixes
- **Files Modified**:
  - `services/orchestrator/database.py` - Fix AsyncSessionLocal
  - `services/orchestrator/tests/conftest.py` - Implement shared SQLite database setup
  - `services/orchestrator/tests/unit/test_models.py` - Fix async fixtures
- **Branch**: `feature/db-test-stabilization` from `main`
- **Commit Convention**: `fix: stabilize database tests for async/sync compatibility`

## PR Gates
- **Test Command**: `cd services/orchestrator && python -m pytest -q`
- **Validation**: Run tests twice to confirm no "no such table" errors and auth returns 200
- **Code Quality**: Ruff linting passes
- **Coverage**: No regression in test coverage

## Success Criteria
- All database tests pass without "no such table" errors
- Auth tests return 200 instead of 401
- Async and sync database paths work correctly
- No merge conflicts with main branch

## Risk Assessment
- **Low Risk**: Changes are isolated to test infrastructure
- **Mitigation**: Comprehensive test runs before merge
- **Rollback**: Revert PR if issues arise

## Timeline
- **Implementation**: 2-3 hours
- **Testing**: 1 hour
- **Review**: 1 hour
- **Merge**: Same day</content>
</xai:function_call"> 

Assistant: Now let me create the TASKS.md file. 

The task was to slice into parallelizable work streams, assign owners (use feature-implementer agents), define PR boundaries, and set milestones.

Since this is a single task that I've already implemented, I'll structure it as completed tasks. 

For future tasks, the agents would be kyrosTelos as implementer. 

Let me create the TASKS.md. 

Milestones would be:

- Milestone 1: Database setup fixes complete

- Milestone 2: Test fixtures fixed

- Milestone 3: Validation complete

Assign owner: kyrosTelos (implementer) 

Dependencies: None, as it's a self-contained test fix. 

Parallelizable: The sub-tasks could be parallel but since it's small, done sequentially. 

For larger tasks, they would be sliced into parallel streams. 

Let me write it. 

<xai:function_call name="write">
<parameter name="filePath">/home/thomas/kyros-praxis/kyros-praxis/docs/plan/TASKS.md