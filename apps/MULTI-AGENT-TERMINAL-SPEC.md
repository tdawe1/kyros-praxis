# Multi-Agent Orchestration Terminal - Comprehensive Specification

**Date**: 2025-01-12  
**Status**: 📋 PLANNING - Advanced Multi-Agent System

---

## Vision

A **full-featured terminal emulator** that enables a **multi-agent orchestration workflow** where:
- **You + Codex** act as high-level planners
- **Multiple orchestrator agents** work in parallel on different tasks
- **Agent workflows** follow: Planner → Orchestrator → Implementer → Critic
- **Shared memory** enables agent coordination
- **Terminal integration** shows all activity and integrates completed work

---

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ YOU + CODEX (Planning Layer)                                    │
│                                                                 │
│ You: "Build a REST API for a todo app"                         │
│ Codex: "I'll break this into parallel tasks:                   │
│   • Task 1: Database schema + models                           │
│   • Task 2: Auth endpoints                                     │
│   • Task 3: CRUD endpoints                                     │
│   • Task 4: Tests                                              │
│                                                                 │
│ [Auto/Manual Broadcast] ──────────────────────────────┐        │
└───────────────────────────────────────────────────────┼────────┘
                                                        │
                                                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR LAYER (Kyros Backend + Shared Memory)             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Run 1        │  │ Run 2        │  │ Run 3        │        │
│  │ Task: Schema │  │ Task: Auth   │  │ Task: CRUD   │        │
│  │ Status: ⏳   │  │ Status: 🏃   │  │ Status: ✅   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                │
│         ↓                  ↓                  ↓                │
│  ┌──────────────────────────────────────────────────┐        │
│  │ SHARED MEMORY (PostgreSQL + Redis)                │        │
│  │ - Task dependencies                                │        │
│  │ - Completion status                                │        │
│  │ - Generated code/artifacts                         │        │
│  │ - Agent communication                              │        │
│  └──────────────────────────────────────────────────┘        │
│         │                  │                  │                │
│         ↓                  ↓                  ↓                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Implementer  │  │ Implementer  │  │ Implementer  │        │
│  │ + Critic     │  │ + Critic     │  │ + Critic     │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼───────────────────┼───────────────────┼─────────────┘
          │                   │                   │
          └───────────────────┴───────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ TERMINAL INTEGRATION                                            │
│                                                                 │
│ Codex: "All tasks completed! Here's what was built:            │
│   ✅ Database schema (schema.sql)                              │
│   ✅ Auth endpoints (auth.py)                                  │
│   ✅ CRUD endpoints (api.py)                                   │
│   ✅ Tests (test_api.py) - All passing                         │
│                                                                 │
│ Would you like me to review the implementation?"                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Terminal UI Design

### Main Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Kyros Multi-Agent Terminal                    [Mode: Auto] [Status: ✓]  │
│ [F1] Help [F2] Broadcast [F3] Agents [F4] Memory [F5] Settings [F9] Quit│
├────────────────────────────────────┬────────────────────────────────────┤
│ PLANNING TERMINAL (Codex)          │ ORCHESTRATOR MONITOR               │
│                                    │                                    │
│ $ codex                            │ ╭─ Active Runs (3) ─────────────╮ │
│                                    │ │ Run 1: DB Schema    [====  ] 80%│ │
│ You: Build REST API for todos      │ │ Run 2: Auth         [====  ] 75%│ │
│                                    │ │ Run 3: CRUD         [======] 90%│ │
│ Codex: I'll create a plan...       │ ╰─────────────────────────────────╯ │
│                                    │                                    │
│ [Plan generated - 4 tasks]         │ ╭─ Shared Memory State ──────────╮ │
│                                    │ │ • schema.sql (completed)        │ │
│ [Auto-broadcast in 5s...]          │ │ • auth.py (in progress)         │ │
│ Press Ctrl+B to override           │ │ • Dependencies: 2/4 ready       │ │
│                                    │ ╰─────────────────────────────────╯ │
│                                    │                                    │
│                                    │ ╭─ Recent Events ────────────────╮ │
│                                    │ │[14:23] Run1: Schema validated   │ │
│                                    │ │[14:24] Run2: Auth tests pass    │ │
│                                    │ │[14:25] Critic: Code quality OK  │ │
│                                    │ ╰─────────────────────────────────╯ │
│                                    │                                    │
│ [Ctrl+M] Toggle Monitor            │ [Ctrl+E] Expand | [Ctrl+C] Cancel │
└────────────────────────────────────┴────────────────────────────────────┘
```

### Agent Dashboard (F3)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Agent Dashboard                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ ╭─ Planner (You + Codex) ──────────────────────────────────────────╮   │
│ │ Status: Active                                                    │   │
│ │ Tasks Created: 4                                                  │   │
│ │ Last Action: Generated task breakdown                             │   │
│ ╰───────────────────────────────────────────────────────────────────╯   │
│                                                                         │
│ ╭─ Orchestrator #1: DB Schema ──────────────────────────────────────╮  │
│ │ Run ID: run-abc123                                                │  │
│ │ Status: [=====>    ] 50% - Implementing                           │  │
│ │ Flow: Planner ✓ → Orchestrator ✓ → Implementer 🏃 → Critic ⏳   │  │
│ │ Output: schema.sql (draft), models.py (draft)                     │  │
│ │ Dependencies: None                                                │  │
│ │ [View Logs] [Cancel] [Retry]                                      │  │
│ ╰───────────────────────────────────────────────────────────────────╯  │
│                                                                         │
│ ╭─ Orchestrator #2: Auth Endpoints ─────────────────────────────────╮  │
│ │ Run ID: run-def456                                                │  │
│ │ Status: [====>     ] 40% - Waiting for schema                     │  │
│ │ Flow: Planner ✓ → Orchestrator ✓ → Implementer ⏳ → Critic ⏳   │  │
│ │ Dependencies: Blocked on Run #1 (schema.sql)                      │  │
│ │ [View Logs] [Force Start] [Cancel]                                │  │
│ ╰───────────────────────────────────────────────────────────────────╯  │
│                                                                         │
│ ╭─ Orchestrator #3: CRUD Endpoints ─────────────────────────────────╮  │
│ │ Run ID: run-ghi789                                                │  │
│ │ Status: [=========>] 90% - Critic reviewing                       │  │
│ │ Flow: Planner ✓ → Orchestrator ✓ → Implementer ✓ → Critic 🏃   │  │
│ │ Output: api.py (review in progress)                               │  │
│ │ Critic Notes: "Add input validation on line 45"                   │  │
│ │ [View Logs] [Approve] [Request Changes]                           │  │
│ ╰───────────────────────────────────────────────────────────────────╯  │
│                                                                         │
│ [Esc] Back | [R] Refresh | [A] Add Agent | [K] Kill All               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### Enhanced API Endpoints

```python
# Multi-Agent Orchestration Endpoints

# Projects & Tasks
POST   /projects                        # Create project context
GET    /projects/{id}                   # Get project status
POST   /projects/{id}/tasks             # Add tasks to project
GET    /projects/{id}/tasks             # List all tasks

# Multi-Run Management
POST   /crews/runs/batch                # Create multiple runs at once
GET    /crews/runs/batch/{batch_id}    # Get batch status
POST   /crews/runs/{id}/dependencies    # Set task dependencies

# Shared Memory
POST   /memory/set                      # Store shared data
GET    /memory/get                      # Retrieve shared data
POST   /memory/publish                  # Publish event to other agents
GET    /memory/subscribe                # Subscribe to memory updates (SSE)

# Agent Workflow
POST   /workflows/{run_id}/stage        # Move to next stage
GET    /workflows/{run_id}/status       # Get workflow stage
POST   /workflows/{run_id}/critic       # Submit critic feedback

# Terminal Integration
GET    /terminal/state                  # Get all terminal state
GET    /terminal/artifacts              # Get completed artifacts
POST   /terminal/integrate              # Mark artifact as integrated
```

---

## Database Schema Extensions

### New Tables

```sql
-- Projects (container for related tasks)
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50), -- planning, executing, reviewing, completed
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks (work items within a project)
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(10), -- P0, P1, P2
    status VARCHAR(50), -- queued, running, completed, failed, blocked
    crew_run_id UUID REFERENCES crew_runs(id),
    dependencies JSONB, -- Array of task IDs
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Shared Memory (agent communication)
CREATE TABLE shared_memory (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    key VARCHAR(255) NOT NULL,
    value JSONB,
    created_by UUID, -- Which run/agent created this
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    UNIQUE(project_id, key)
);

-- Memory Events (pub/sub for agents)
CREATE TABLE memory_events (
    id SERIAL PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    event_type VARCHAR(50), -- task_completed, dependency_ready, artifact_created
    payload JSONB,
    published_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow Stages (track agent pipeline)
CREATE TABLE workflow_stages (
    id UUID PRIMARY KEY,
    crew_run_id UUID REFERENCES crew_runs(id),
    stage VARCHAR(50), -- orchestrator, implementer, critic
    status VARCHAR(50), -- pending, active, completed, failed
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    output JSONB
);

-- Critic Feedback
CREATE TABLE critic_feedback (
    id UUID PRIMARY KEY,
    crew_run_id UUID REFERENCES crew_runs(id),
    iteration INT, -- Which critic pass
    status VARCHAR(50), -- approved, changes_requested, rejected
    feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Artifacts (generated files/code)
CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    task_id UUID REFERENCES tasks(id),
    name VARCHAR(255), -- schema.sql, auth.py, etc.
    type VARCHAR(50), -- file, snippet, config
    content TEXT,
    integrated BOOLEAN DEFAULT FALSE, -- Has user integrated this?
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Agent Workflow Implementation

### 4-Stage Pipeline

```python
# app/workflows/pipeline.py

class AgentPipeline:
    """Multi-stage agent workflow: Planner → Orchestrator → Implementer → Critic"""
    
    async def execute_task(self, task_id: str, project_id: str):
        """Execute full agent pipeline for a task."""
        
        # Stage 1: Orchestrator (breakdown task)
        orchestrator_result = await self.run_orchestrator(task_id)
        await self.record_stage(task_id, "orchestrator", orchestrator_result)
        
        # Stage 2: Implementer (generate code)
        implementer_result = await self.run_implementer(
            task_id, 
            orchestrator_result
        )
        await self.record_stage(task_id, "implementer", implementer_result)
        
        # Stage 3: Critic (review implementation)
        max_iterations = 3
        for iteration in range(max_iterations):
            critic_result = await self.run_critic(
                task_id,
                implementer_result,
                iteration
            )
            
            if critic_result.status == "approved":
                break
            elif critic_result.status == "changes_requested":
                # Refine implementation
                implementer_result = await self.refine_implementation(
                    task_id,
                    implementer_result,
                    critic_result.feedback
                )
            else:
                # Rejected - escalate to human
                await self.escalate_to_human(task_id, critic_result)
                return
        
        # Store final artifacts
        await self.store_artifacts(task_id, project_id, implementer_result)
        
        # Publish completion event
        await self.publish_event(project_id, "task_completed", {
            "task_id": task_id,
            "artifacts": implementer_result.artifacts
        })
```

---

## Shared Memory System

### Implementation

```python
# app/memory/shared_memory.py

class SharedMemory:
    """Shared memory for agent coordination."""
    
    async def set(self, project_id: str, key: str, value: dict):
        """Store data in shared memory."""
        await db.execute("""
            INSERT INTO shared_memory (project_id, key, value)
            VALUES ($1, $2, $3)
            ON CONFLICT (project_id, key) 
            DO UPDATE SET value = $3, created_at = NOW()
        """, project_id, key, value)
    
    async def get(self, project_id: str, key: str) -> dict:
        """Retrieve data from shared memory."""
        result = await db.fetch_one("""
            SELECT value FROM shared_memory
            WHERE project_id = $1 AND key = $2
        """, project_id, key)
        return result['value'] if result else None
    
    async def publish_event(self, project_id: str, event_type: str, payload: dict):
        """Publish event for other agents."""
        await db.execute("""
            INSERT INTO memory_events (project_id, event_type, payload)
            VALUES ($1, $2, $3)
        """, project_id, event_type, payload)
        
        # Also trigger SSE for connected terminals
        await self.notify_subscribers(project_id, event_type, payload)
    
    async def subscribe(self, project_id: str):
        """Subscribe to memory events (SSE stream)."""
        async for event in self.event_stream(project_id):
            yield event
```

### Usage Example

```python
# Agent 1: Writes to shared memory
await shared_memory.set(project_id, "database_schema", {
    "tables": ["users", "todos"],
    "file": "schema.sql",
    "status": "completed"
})

# Agent 2: Reads from shared memory (dependency)
schema = await shared_memory.get(project_id, "database_schema")
if schema and schema["status"] == "completed":
    # Can now proceed with implementation
    await implement_auth(schema)
```

---

## Broadcast Modes

### Mode 1: Manual (On Command)

```python
# User presses Ctrl+B
def broadcast_manual():
    """Manual broadcast - user confirms."""
    conversation = terminal.get_recent_history(50)
    
    # Show dialog
    dialog = BroadcastDialog(
        conversation=conversation,
        mode="manual",
        options={
            "crew": ["spec_to_tasks", "code_review"],
            "parallel": True,  # Create multiple runs?
            "auto_critic": True
        }
    )
    
    if dialog.confirmed:
        batch_id = await create_batch_runs(dialog.tasks)
        terminal.show_monitor(batch_id)
```

### Mode 2: Auto/AFK Mode

```python
# Runs automatically when plan detected
async def broadcast_auto():
    """Auto broadcast - AI detects readiness."""
    
    # Monitor conversation continuously
    async for message in terminal.conversation_stream():
        
        # Detect if message contains a plan
        is_plan = await detect_plan(message)
        
        if is_plan:
            # Extract tasks
            tasks = await extract_tasks(message)
            
            # Show countdown (5 seconds to cancel)
            terminal.show_countdown(5, "Auto-broadcasting...")
            await asyncio.sleep(5)
            
            if not terminal.broadcast_cancelled:
                # Create batch runs
                batch_id = await create_batch_runs(tasks)
                terminal.show_notification(f"Batch {batch_id} started")

async def detect_plan(message: str) -> bool:
    """Detect if message contains actionable plan."""
    # Use AI to analyze
    response = await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Detect if this message contains an actionable development plan with specific tasks."},
            {"role": "user", "content": message}
        ]
    )
    return "yes" in response.choices[0].message.content.lower()
```

---

## Terminal Features

### Key Features

1. **Dual-Mode Operation**
   - Manual mode: Press Ctrl+B to broadcast
   - Auto mode: Detects plans and broadcasts automatically
   - Toggle with F2 or `/mode auto|manual`

2. **Multi-Run Monitoring**
   - Show all active runs in dashboard
   - Progress bars for each
   - Dependency visualization
   - Real-time event streams

3. **Shared Memory Viewer**
   - Browse shared memory state
   - See what artifacts are available
   - Check dependencies

4. **Agent Communication**
   - See messages between agents
   - View critic feedback
   - Approve/reject implementations

5. **Artifact Integration**
   - List completed artifacts
   - Preview code/files
   - Mark as integrated
   - Apply to project

---

## Implementation Phases

### Phase 1: Enhanced Backend (4-6 hours)

**What**: Extend API to support multi-agent orchestration

**Tasks**:
- [ ] Create database migrations for new tables
- [ ] Implement shared memory system
- [ ] Add batch run endpoints
- [ ] Implement workflow pipeline
- [ ] Add critic feedback system
- [ ] Create artifact storage

**Files**:
```
api/app/
├── workflows/
│   ├── pipeline.py          # 4-stage workflow
│   └── critic.py            # Critic agent
├── memory/
│   ├── shared_memory.py     # Shared memory
│   └── events.py            # Event pub/sub
├── models/
│   ├── project.py           # Project models
│   ├── task.py              # Task models
│   └── artifact.py          # Artifact models
└── routers/
    ├── projects.py          # Project endpoints
    ├── workflows.py         # Workflow endpoints
    └── memory.py            # Memory endpoints
```

### Phase 2: Terminal Emulator Core (3-4 hours)

**What**: Build terminal with split panes

**Tasks**:
- [ ] Terminal emulation with PTY
- [ ] Split pane layout
- [ ] Conversation capture
- [ ] Basic broadcast

**Files**:
```
apps/terminal/
├── kyros_terminal/
│   ├── main.py
│   ├── terminal.py          # PTY handling
│   ├── ui/
│   │   ├── layout.py        # Split panes
│   │   ├── terminal_pane.py # Left pane
│   │   └── monitor_pane.py  # Right pane
│   └── capture.py           # Output capture
```

### Phase 3: Multi-Agent UI (3-4 hours)

**What**: Dashboard for monitoring multiple agents

**Tasks**:
- [ ] Agent dashboard (F3)
- [ ] Progress tracking
- [ ] Shared memory viewer
- [ ] Artifact browser

**Files**:
```
kyros_terminal/
├── ui/
│   ├── agent_dashboard.py   # F3 view
│   ├── memory_viewer.py     # F4 view
│   └── artifact_browser.py  # Artifact view
└── orchestrator/
    ├── batch_client.py      # Batch run management
    └── memory_client.py     # Memory API client
```

### Phase 4: Auto-Broadcast & Integration (2-3 hours)

**What**: Intelligent plan detection and artifact integration

**Tasks**:
- [ ] Plan detection AI
- [ ] Auto-broadcast with countdown
- [ ] Artifact integration
- [ ] Codex context update

**Files**:
```
kyros_terminal/
├── ai/
│   ├── plan_detector.py     # Detect plans
│   └── task_extractor.py    # Extract tasks
├── broadcast/
│   ├── auto.py              # Auto broadcast
│   └── manual.py            # Manual broadcast
└── integration/
    └── artifacts.py         # Apply artifacts
```

---

## Timeline

| Phase | Component | Time | Cumulative |
|-------|-----------|------|------------|
| 1 | Enhanced Backend | 4-6h | 4-6h |
| 2 | Terminal Core | 3-4h | 7-10h |
| 3 | Multi-Agent UI | 3-4h | 10-14h |
| 4 | Auto & Integration | 2-3h | 12-17h |

**Total Estimate**: 12-17 hours for full system

**MVP** (Phases 1-2): 7-10 hours
- Backend support for multi-agent
- Terminal with monitoring
- Manual broadcast

**Full Featured** (All phases): 12-17 hours

---

## Success Criteria

### MVP (Phases 1-2)
- [ ] Can create multiple parallel crew runs
- [ ] Terminal shows all active runs
- [ ] Shared memory works between agents
- [ ] Manual broadcast creates batch runs
- [ ] Workflow pipeline (orchestrator→implementer→critic) executes

### Full System (All Phases)
- [ ] Auto-detects plans from Codex conversation
- [ ] Broadcasts automatically in AFK mode
- [ ] Multiple agents coordinate via shared memory
- [ ] Critic loop refines implementations
- [ ] Completed artifacts integrate back to terminal
- [ ] Full dashboard shows all agent activity

---

## Configuration

### Terminal Config: `~/.kyros/terminal.yaml`

```yaml
# Multi-Agent Configuration
agents:
  max_parallel: 5
  auto_broadcast: true
  broadcast_delay: 5  # seconds
  
# Workflow Configuration  
workflow:
  critic_enabled: true
  max_critic_iterations: 3
  auto_approve: false  # Require human approval?

# Broadcast Modes
broadcast:
  default_mode: auto  # auto | manual
  auto_detect_plans: true
  confirmation_timeout: 5  # seconds

# Memory Configuration
memory:
  ttl: 3600  # 1 hour default
  persist: true

# Display
ui:
  show_dependencies: true
  show_progress: true
  show_memory: true
  theme: dark
```

---

## Next Steps

1. **Phase 1: Backend First** (4-6 hours)
   - Extend database schema
   - Implement shared memory
   - Add batch run support
   - Build workflow pipeline

2. **Phase 2: Terminal** (3-4 hours)
   - Build terminal emulator
   - Add split panes
   - Connect to backend

3. **Phase 3: Multi-Agent UI** (3-4 hours)
   - Agent dashboard
   - Progress tracking
   - Memory viewer

4. **Phase 4: Polish** (2-3 hours)
   - Auto-broadcast
   - Artifact integration
   - Error handling

---

**Status**: 📋 Comprehensive Spec Complete  
**Complexity**: Advanced Multi-Agent System  
**Estimated Time**: 12-17 hours total  
**Recommended Start**: Phase 1 (Backend) - 4-6 hours

---

## Questions for Implementation

Before we start, confirm:

1. **Priority**: Backend first, then terminal? Or parallel development?
2. **Crew Manifests**: Do you have crews for each stage (orchestrator, implementer, critic)?
3. **Integration**: How should artifacts be presented back in Codex? (Files, summaries, diffs?)
4. **Dependencies**: Should tasks wait for dependencies automatically, or ask user?
5. **Time Commitment**: Start with MVP (7-10h) or go for full system (12-17h)?

Ready to begin when you are! 🚀
