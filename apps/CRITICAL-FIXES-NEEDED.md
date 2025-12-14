# Critical Fixes Required Before Testing

These issues MUST be fixed before running the system.

---

## 1. Fix Artifact Response Model (CRITICAL)

**File**: `app/models_multi_agent.py`  
**Line**: ~240

**Problem**: Model field name doesn't match database column  
Database has `meta` (aliased to `metadata` in column definition)  
Pydantic model has `metadata`

**Current Code**:
```python
class ArtifactResponse(BaseModel):
    """Response model for artifact."""
    id: str
    project_id: str
    task_id: Optional[str]
    name: str
    type: ArtifactType
    content: str
    metadata: Optional[Dict[str, Any]]  # WRONG - DB column is 'meta'
    integrated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
```

**Fixed Code**:
```python
class ArtifactResponse(BaseModel):
    """Response model for artifact."""
    id: str
    project_id: str
    task_id: Optional[str]
    name: str
    type: ArtifactType
    content: str
    meta: Optional[Dict[str, Any]] = Field(None, alias="metadata")
    integrated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True  # Allow both 'meta' and 'metadata'
```

**Why**: Without this, artifact serialization will fail with AttributeError

---

## 2. Fix ArtifactCreate/Update Models

**File**: `app/models_multi_agent.py`  
**Lines**: ~230, ~235

**Also need to update**:
```python
class ArtifactCreate(BaseModel):
    """Request model for creating artifact."""
    project_id: str
    task_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    type: ArtifactType
    content: str
    meta: Optional[Dict[str, Any]] = Field(None, alias="metadata")  # FIX THIS

class ArtifactUpdate(BaseModel):
    """Request model for updating artifact."""
    integrated: Optional[bool] = None
    content: Optional[str] = None
    meta: Optional[Dict[str, Any]] = Field(None, alias="metadata")  # FIX THIS
```

---

## 3. Fix Background Task Execution

**File**: `app/routers/batch_runs.py`  
**Line**: ~72-77

**Problem**: Adding async function to FastAPI BackgroundTasks (expects sync)

**Current Code**:
```python
for task in tasks:
    # Add to background tasks
    bg.add_task(
        workflow_pipeline.execute_task,  # This is async!
        task_id=task.id,
        project_id=batch_data.project_id,
        task_input={"prompt": task.description or task.title}
    )
```

**Fixed Code - Option 1** (Use asyncio):
```python
import asyncio

for task in tasks:
    # Create async task directly
    asyncio.create_task(
        workflow_pipeline.execute_task(
            task_id=task.id,
            project_id=batch_data.project_id,
            task_input={"prompt": task.description or task.title}
        )
    )
```

**Fixed Code - Option 2** (Wrap in sync function):
```python
def _run_workflow_sync(task_id: str, project_id: str, task_input: dict):
    """Wrapper to run async workflow in background."""
    asyncio.run(workflow_pipeline.execute_task(task_id, project_id, task_input))

for task in tasks:
    bg.add_task(
        _run_workflow_sync,
        task.id,
        batch_data.project_id,
        {"prompt": task.description or task.title}
    )
```

**Recommended**: Option 1 (asyncio.create_task)

---

## 4. Add Missing Crew Manifests

**Location**: `crews/` directory

**Need to create**:
1. `code_implementer.yaml` or `code_implementer.py`
2. Optional: `code_critic.yaml` or stub out critic functionality

**Temporary Fix** (until crews are created):

Update `workflows/pipeline.py` to use existing crew:

```python
# Line ~87: Change crew_id
implementer_result = await self._run_stage(
    task_id=task_id,
    project_id=project_id,
    stage="implementer",
    crew_id="spec_to_tasks",  # Use existing crew temporarily
    input_data=implementer_input
)
```

---

## 5. Fix Auth Dependency (Optional but Recommended)

**File**: `app/routers/projects.py`  
**Line**: ~39-41

**Current Code**:
```python
@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),  # This is optional!
):
```

**Problem**: Auth is optional, anyone can create projects

**Option 1** - Make auth required:
```python
from ..auth import get_current_user_required  # Create this function

async def create_project(
    project_data: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_required),
):
```

**Option 2** - Keep optional but document:
```python
async def create_project(
    project_data: ProjectCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),  # Optional: pass None to allow anonymous
):
    """Create a new multi-agent project.
    
    Note: Authentication is optional. If authenticated, project is associated with user.
    """
```

---

## 6. Add Unique Constraint to Migration

**File**: `alembic/versions/0003_add_multi_agent_tables.py`  
**Line**: After line 65

**Add after creating shared_memory table**:
```python
op.create_index(
    "ix_shared_memory_project_key", 
    "shared_memory", 
    ["project_id", "key"], 
    unique=True  # Already there, good!
)

# ADD THIS: Unique constraint at DB level
op.create_unique_constraint(
    "uq_shared_memory_project_key",
    "shared_memory",
    ["project_id", "key"]
)
```

This prevents race conditions in memory storage.

---

## Quick Command to Apply Fixes

```bash
cd /home/thomas/kyros-praxis/apps/api

# 1. Fix models (manual edit required)
# Edit app/models_multi_agent.py and change 'metadata' to 'meta'

# 2. Fix batch_runs (manual edit required)  
# Edit app/routers/batch_runs.py and use asyncio.create_task

# 3. Update workflow to use existing crew (temporary)
# Edit app/workflows/pipeline.py line 87

# 4. Then run migrations
../.venv/bin/alembic upgrade head

# 5. Test startup
../.venv/bin/uvicorn app.main:app --reload
```

---

## Testing Checklist After Fixes

- [ ] App starts without errors
- [ ] Can create a project: `POST /projects`
- [ ] Can create a task: `POST /projects/{id}/tasks`
- [ ] Can set memory: `POST /memory/set`
- [ ] Can get memory: `POST /memory/get`
- [ ] Can subscribe to events: `GET /memory/{id}/events`
- [ ] Dashboard endpoint works: `GET /projects/{id}/dashboard`

---

## Estimated Time to Fix

- Fix 1 (Models): 5 minutes
- Fix 2 (Models): 2 minutes  
- Fix 3 (Background): 5 minutes
- Fix 4 (Crews): 10 minutes OR use temp fix (2 min)
- Fix 5 (Auth): Optional, 10 minutes
- Fix 6 (Migration): 5 minutes

**Total**: 15-40 minutes depending on crew strategy

---

## After Fixes, These Still Need Attention

1. **Add rate limiting** (security)
2. **Add project ownership validation** (security)
3. **Add pagination** (performance)
4. **Write tests** (reliability)
5. **Add logging** (observability)
6. **Schedule memory cleanup** (maintenance)

But the system will be **functional** after the critical fixes above.
