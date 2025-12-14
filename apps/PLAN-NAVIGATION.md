# Unified Audit & Plan - Navigation Guide

**Total Document**: 1,200+ lines  
**Reading Time**: 30-45 minutes (full read)  
**Quick Scan**: 10 minutes (key sections)

---

## 📚 Table of Contents (Interactive Guide)

### Part 1: Executive Overview (Lines 1-100)
**Time**: 5 minutes  
**Purpose**: High-level findings and recommendations

- Executive Summary
- Synthesis: Two Analyses Combined
- Agreement Points
- Critical Issues Must Fix

**Read If**: You want the TL;DR

---

### Part 2: Critical Issues Deep-Dive (Lines 101-200)
**Time**: 10 minutes  
**Purpose**: Understand what's breaking and why

#### 🔴 Critical #1: Missing Dependencies
```python
# These cause crashes:
apscheduler==3.10.4  # ❌ Not in requirements.txt
redis==5.0.1         # ❌ Not in requirements.txt
prometheus-client    # ❌ Not in requirements.txt
```

**Impact**: Server startup crashes when features try to load

**Fix Options**:
- Add all 3 packages (5 minutes)
- Remove unused code (4 hours)

**Recommendation**: Add packages

---

#### 🔴 Critical #2: Schema Mismatch
```python
# cleanup.py line 87:
task.archived = True

# But models.py Task has no archived field!
```

**Impact**: Background cleanup job crashes

**Fix Options**:
- Add migration for archived field (30 minutes)
- Change cleanup to use existing fields (1 hour)

**Recommendation**: Add field with migration

---

#### 🔴 Critical #3: Outdated Tests
```typescript
// auth-context.test.tsx still tests old approach:
localStorage.getItem('token')  // ❌ Code doesn't do this!

// Code actually uses:
document.cookie  // ✅ HttpOnly cookies
```

**Impact**: Tests pass but validate wrong behavior

**Fix**: Rewrite 150 lines of tests (4 hours)

---

#### 🔴 Critical #4: Single-Agent vs Multi-Agent
```
Current Workflow:
  User prompt → Single crew → Output

PRD Workflow:
  User prompt → Planner agent → User review spec
  → Coder agent → Tester agent → Documenter agent
  → User can refine → Iterate
```

**Impact**: Core feature doesn't match PRD vision

**Fix**: Refactor workflow pipeline (6 days)

---

### Part 3: Gap Analysis - Current vs PRD (Lines 201-400)
**Time**: 10 minutes  
**Purpose**: Understand what exists vs what PRD requires

#### What PRD Expects (Detailed)

**User Journey**:
```
1. User opens Prompt Builder
   → Guided form with sections:
     - Purpose: "What are you building?"
     - Features: Bullet list
     - Tech Stack: Dropdown selector
     - Constraints: Optional details
   → Prompt validation warns if too vague
   → Template library for common patterns

2. Planner Agent Runs
   → Analyzes prompt
   → Creates structured specification
   → Breaks into components
   → Returns spec to user

3. User Reviews Spec
   → Can approve and continue
   → Can refine prompt and regenerate
   → Iteration loop until satisfied

4. Coder Agent Runs
   → Generates code for each component
   → Creates file structure
   → Adds comments/documentation
   → Returns code files

5. Tester Agent Runs
   → Reviews generated code
   → Creates unit tests
   → Validates functionality
   → Reports issues

6. Documenter Agent Runs (Optional)
   → Generates README
   → Creates API documentation
   → Writes setup instructions

7. User Views Results
   → Code Viewer shows file tree
   → Can read each file
   → Can see diff between iterations
   → Can export as ZIP
   → Can refine and regenerate
```

**PRD Quotes**:
- "Guided Prompt Input: offer tips or sections to fill out"
- "Planner Agent refines prompt into structured plan"
- "iterative refinement loop"
- "user can review each file in our IDE"
- "viewing diffs on prompt regeneration"

---

#### What Currently Exists

**Current Flow**:
```
1. User triggers run (no prompt builder UI)
   → Hardcoded manifest: spec_to_tasks.yaml
   → No validation
   → No templates

2. Single Crew Executes
   → Same crew for all stages
   → Orchestrator → Implementer → Critic
   → No separate Planner/Coder/Tester
   → Auto-approves if critic errors

3. No User Review
   → One-shot execution
   → No spec approval step
   → No iteration UI

4. Results Stored
   → Database has the data
   → No Code Viewer UI
   → No diff viewer
   → No export functionality
```

**Current Files**:
- `crew_runner.py`: Executes one manifest
- `pipeline.py`: Chains stages but uses same crew
- `planner/page.tsx`: Triggers run, no prompt builder
- No Code Viewer component exists

---

#### The Gap Summary

| PRD Feature | Status | Gap Size |
|-------------|--------|----------|
| **Guided Prompt Builder** | ❌ Doesn't exist | 🔴 Large (3 days) |
| **Prompt Validation** | ❌ Doesn't exist | 🟡 Medium (1 day) |
| **Template Library** | ❌ Doesn't exist | 🟢 Small (future) |
| **Separate Planner Agent** | ❌ Uses same crew | 🔴 Large (2 days) |
| **User Reviews Spec** | ❌ No approval UI | 🟡 Medium (1 day) |
| **Separate Coder Agent** | ❌ Uses same crew | 🔴 Large (2 days) |
| **Separate Tester Agent** | ❌ Uses same crew | 🔴 Large (2 days) |
| **Documenter Agent** | ❌ Doesn't exist | 🟢 Small (Phase 2) |
| **Code Viewer UI** | ❌ Doesn't exist | 🔴 Large (3 days) |
| **Diff Viewer** | ❌ Doesn't exist | 🟡 Medium (1 day) |
| **Iteration Loop** | ❌ One-shot only | 🔴 Large (2 days) |
| **Export Functionality** | ❌ Doesn't exist | 🟢 Small (1 day) |

**Total Gap**: ~20 days of work to reach PRD feature parity

---

### Part 4: Component Analysis (Lines 401-700)
**Time**: 15 minutes  
**Purpose**: Detailed breakdown of each component

#### API Backend - Detailed Assessment

**File**: `apps/api/app/main.py` (450 lines)

**What Works**:
```python
✅ FastAPI setup clean
✅ CORS configured
✅ Auth routers working (just completed)
✅ SSE streaming for run events
✅ Optional middleware architecture
✅ Health checks
✅ Error handling
```

**Issues**:
```python
❌ Imports fail for optional features:
   - line 25: from .middleware.rate_limit import rate_limiter
   - line 29: from .middleware.metrics import MetricsMiddleware
   - line 32: from .cache.redis_cache import cache
   → All wrapped in try/except but advertised in startup

❌ Background jobs start on line 138:
   await start_background_jobs()
   → But apscheduler not installed
```

**Verdict**: 85% solid, 15% needs fixes

---

**File**: `apps/api/app/crew_runner.py` (193 lines)

**What Works**:
```python
✅ Manifest loading from YAML
✅ Environment variable resolution
✅ Simulation mode fallback
✅ Error handling
```

**Issues**:
```python
❌ Line 41-193: Only executes single role/task
   crew = Crew(
       agents=[spec_agent],  # Single agent!
       tasks=[spec_task],
       ...
   )

❌ No dynamic prompt processing
   → Prompt comes from manifest, not user input

❌ No multi-agent orchestration
   → PRD expects Planner → Coder → Tester
```

**Verdict**: Prototype works, but wrong architecture

---

**File**: `apps/api/app/workflows/pipeline.py` (435 lines)

**What Works**:
```python
✅ Three-stage structure:
   - orchestrator (lines 66-150)
   - implementer (lines 151-250)
   - critic (lines 251-350)

✅ Artifact persistence
✅ WorkflowStage tracking
✅ CriticFeedback stored
```

**Critical Issues**:
```python
❌ Line 100-120: Uses SAME crew for all stages
   orchestrator_run = await run_crew(
       manifest_name="spec_to_tasks",  # Same manifest!
       ...
   )
   implementer_run = await run_crew(
       manifest_name="spec_to_tasks",  # Same manifest again!
       ...
   )

❌ Line 280-300: Auto-approves on critic error
   if critic_run.status != "completed":
       logger.warning("Critic failed, auto-approving")
       workflow.status = "completed"  # ❌ Wrong!

❌ Line 350-400: _refine_implementation is TODO
   # TODO: Implement refinement loop
   pass
```

**Verdict**: Architecture exists but logic is placeholder

---

#### Frontend Console - Detailed Assessment

**File**: `apps/console/app/planner/page.tsx` (178 lines)

**What Works**:
```typescript
✅ Uses useRunManager hook
✅ SSE streaming displays
✅ Auth-aware
✅ Loading states
```

**Issues**:
```typescript
❌ No prompt builder UI (lines 50-100)
   → Simple button: "Start New Run"
   → No guided input
   → No validation
   → No templates

❌ No iteration loop (lines 120-178)
   → Shows run results
   → But no "Refine" button
   → No diff viewer
   → Can't regenerate
```

**Verdict**: Basic run trigger, not PRD prompt builder

---

**File**: `apps/console/app/lib/api-client.ts` (119 lines)

**What Works**:
```typescript
✅ Global API client
✅ credentials: 'include' on all requests
✅ Auto-retry on 401
✅ Refresh token logic
✅ Type-safe
```

**Issues**:
```typescript
❌ Line 15-20: APIError type missing correlationId
   export class APIError extends Error {
     constructor(
       message: string,
       public status: number
       // ❌ Missing: public correlationId?: string
     ) {
       super(message);
     }
   }

❌ Used in 3 places expecting correlationId:
   - use-run-manager.ts line 97
   - page.tsx line 117
   - Dashboard.tsx line 58
```

**Verdict**: 95% correct, needs correlationId field

---

### Part 5: Migration Strategy (Lines 701-900)
**Time**: 10 minutes  
**Purpose**: Understand how to get from current → PRD

#### Phase 0: Critical Fixes (2 days)

**Goal**: Make current code production-stable

**Task 1: Add Dependencies (30 minutes)**
```bash
cd /home/thomas/kyros-praxis/apps/api
cat >> requirements.txt << 'EOF'

# Background Jobs
apscheduler==3.10.4

# Caching (optional but referenced)
redis==5.0.1

# Metrics (optional but referenced)
prometheus-client==0.19.0
EOF

# Test
.venv/bin/pip install -r requirements.txt
```

**Alternative**: Remove unused code (4 hours)
```python
# Remove from main.py:
- from .jobs.cleanup import start_background_jobs  # Delete this
- await start_background_jobs()  # Delete this

# Remove from jobs/cleanup.py:
- task.archived = True  # Change to task.status = 'archived'
```

**Decision**: Add packages (easier, more functionality)

---

**Task 2: Fix Schema (1 hour)**

Option A: Add Migration (30 min)
```bash
cd apps/api
../.venv/bin/alembic revision -m "add_task_archived"
```

```python
# In new migration file:
def upgrade():
    op.add_column('tasks', 
        sa.Column('archived', sa.Boolean(), default=False, nullable=False)
    )

def downgrade():
    op.drop_column('tasks', 'archived')
```

```bash
../.venv/bin/alembic upgrade head
```

Option B: Change cleanup.py (30 min)
```python
# Line 87 in cleanup.py:
# OLD:
task.archived = True

# NEW:
task.status = 'archived'
```

**Decision**: Add field (better for future features)

---

**Task 3: Fix Auth Tests (4 hours)**

```typescript
// apps/console/app/state/auth-context.test.tsx
// Complete rewrite needed

// OLD (lines 61-90):
describe('login', () => {
  it('stores token in localStorage', () => {
    const token = localStorage.getItem('token');  // ❌
    expect(token).toBe('fake-jwt');
  });
});

// NEW:
describe('login', () => {
  beforeEach(() => {
    // Mock document.cookie
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: ''
    });
    
    // Mock fetch to set cookies in response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ /* ... */ }),
        headers: new Headers({
          'Set-Cookie': 'access_token=fake-jwt; HttpOnly'
        })
      })
    );
  });

  it('sends credentials and receives cookie', async () => {
    await auth.login('test@example.com', 'password');
    
    // Verify fetch called with credentials
    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        credentials: 'include'  // ✅
      })
    );
    
    // Verify cookie would be set by browser
    // (Can't directly test HttpOnly in JSDOM)
  });
});
```

**Files to Update**:
- `auth-context.test.tsx` (150 lines)

**Test**: Run `npm test` after changes

---

**Task 4: Add correlationId (30 min)**

```typescript
// apps/console/app/lib/api-client.ts
// Line 15-20:

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public correlationId?: string  // ✅ ADD THIS
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Line 50-60: Extract from response
async function handleResponse(response: Response) {
  if (!response.ok) {
    const correlationId = response.headers.get('X-Correlation-ID');  // ✅
    const body = await response.json();
    throw new APIError(
      body.message || 'Request failed',
      response.status,
      correlationId  // ✅
    );
  }
  return response.json();
}
```

**Test**: Check use-run-manager.ts errors now show correlationId

---

**Phase 0 Checklist**:
```
[ ] Add dependencies to requirements.txt
[ ] Run pip install -r requirements.txt
[ ] Add Task.archived migration
[ ] Run alembic upgrade head
[ ] Rewrite auth-context.test.tsx for cookies
[ ] Run npm test and verify pass
[ ] Add APIError.correlationId field
[ ] Verify no TypeScript errors
[ ] Start servers and verify no crashes
[ ] All tests pass
```

**Time**: 2 days  
**Effort**: 8 hours coding  
**Impact**: Production-stable, no crashes

---

#### Phase 1: Multi-Agent Workflow (6 days)

**Goal**: Transform single-agent prototype into PRD multi-agent system

**Task 1: Create Agent Definitions (2 days)**

```bash
mkdir -p apps/api/app/agents
```

**File Structure**:
```
apps/api/app/agents/
├── __init__.py
├── planner.py     # NEW
├── coder.py       # NEW
├── tester.py      # NEW
└── documenter.py  # Phase 2
```

**planner.py** (PRD: "refines prompt into structured plan"):
```python
"""
Planner Agent: Analyzes user prompt and creates structured specification.

PRD Requirements:
- "Planner Agent refines the user's prompt into a structured plan"
- "outlines the components needed"
- "creates a pseudo-design document"
"""

from crewai import Agent, Task, Crew

def create_planner_agent() -> Agent:
    """Create agent that analyzes prompts and creates specs."""
    return Agent(
        role="Software Architect",
        goal="Analyze user requirements and create detailed specifications",
        backstory="""You are an experienced software architect who excels at 
        understanding project requirements and breaking them down into 
        structured, actionable plans. You ask clarifying questions when 
        requirements are ambiguous.""",
        tools=[],  # Could add: web_search, documentation_lookup
        verbose=True
    )

def create_planning_task(user_prompt: str) -> Task:
    """Create task for analyzing prompt and generating spec."""
    return Task(
        description=f"""
        Analyze this user requirement and create a detailed specification:
        
        USER PROMPT:
        {user_prompt}
        
        Create a specification including:
        1. Purpose: What is being built and why
        2. Components: List of major components needed
        3. Technology: Recommended tech stack
        4. File Structure: Proposed project organization
        5. Dependencies: External libraries/services needed
        6. Validation: Edge cases and testing considerations
        
        Format as structured JSON.
        """,
        expected_output="Structured specification in JSON format",
    )

async def run_planner(user_prompt: str) -> dict:
    """
    Run planner agent to analyze prompt and create spec.
    
    PRD: "user can review and approve before coding starts"
    """
    agent = create_planner_agent()
    task = create_planning_task(user_prompt)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process='sequential'
    )
    
    result = crew.kickoff()
    return result
```

**coder.py** (PRD: "generates actual code"):
```python
"""
Coder Agent: Generates code based on approved specification.

PRD Requirements:
- "generates actual code for each component"
- "creates file structure"
- "adds comments/documentation"
"""

from crewai import Agent, Task, Crew

def create_coder_agent() -> Agent:
    """Create agent that writes code from specifications."""
    return Agent(
        role="Senior Software Engineer",
        goal="Generate clean, well-documented code from specifications",
        backstory="""You are a senior developer who writes production-quality 
        code. You follow best practices, add meaningful comments, and ensure 
        code is maintainable and testable.""",
        tools=[],  # Could add: code_search, documentation_lookup
        verbose=True
    )

def create_coding_task(specification: dict) -> Task:
    """Create task for generating code from spec."""
    return Task(
        description=f"""
        Generate production-ready code based on this specification:
        
        SPECIFICATION:
        {specification}
        
        For each component:
        1. Write complete, functional code
        2. Add docstrings and comments
        3. Follow language best practices
        4. Include error handling
        5. Make code testable
        
        Return as structured file objects with path and content.
        """,
        expected_output="Generated code files with paths and contents",
    )

async def run_coder(specification: dict) -> dict:
    """
    Run coder agent to generate code from approved spec.
    """
    agent = create_coder_agent()
    task = create_coding_task(specification)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process='sequential'
    )
    
    result = crew.kickoff()
    return result
```

**tester.py** (PRD: "reviews or generates tests"):
```python
"""
Tester Agent: Reviews code and creates tests.

PRD Requirements:
- "reviews generated code"
- "creates unit tests"
- "validates functionality"
"""

from crewai import Agent, Task, Crew

def create_tester_agent() -> Agent:
    """Create agent that reviews code and writes tests."""
    return Agent(
        role="QA Engineer",
        goal="Review code for issues and create comprehensive tests",
        backstory="""You are a meticulous QA engineer who finds edge cases 
        and ensures code quality. You write thorough unit tests and validate 
        that implementations match specifications.""",
        tools=[],  # Could add: linter, code_analyzer
        verbose=True
    )

def create_testing_task(code_files: dict, specification: dict) -> Task:
    """Create task for reviewing code and generating tests."""
    return Task(
        description=f"""
        Review this generated code and create tests:
        
        CODE:
        {code_files}
        
        SPECIFICATION:
        {specification}
        
        For each file:
        1. Review for bugs and issues
        2. Check against specification
        3. Create unit tests
        4. Test edge cases
        5. Validate error handling
        
        Return: Test files + review feedback
        """,
        expected_output="Test files and code review feedback",
    )

async def run_tester(code_files: dict, specification: dict) -> dict:
    """
    Run tester agent to review code and create tests.
    """
    agent = create_tester_agent()
    task = create_testing_task(code_files, specification)
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process='sequential'
    )
    
    result = crew.kickoff()
    return result
```

**Time**: 2 days (coding + testing each agent)

---

**Task 2: Create Prompt Processor (1 day)**

```python
# apps/api/app/prompt_processor.py (NEW)
"""
Prompt processing and validation.

PRD Requirements:
- "validate prompt quality"
- "warn if too short or ambiguous"
- "inject system prompts to guide agents"
"""

from typing import Dict, List
from pydantic import BaseModel

class ValidationResult(BaseModel):
    valid: bool
    issues: List[str]
    suggestions: List[str]
    score: int  # 0-100

class PromptProcessor:
    """
    Validates and enhances user prompts for better AI generation.
    
    PRD: "The system should analyze the prompt before execution."
    """
    
    MIN_LENGTH = 50  # characters
    RECOMMENDED_LENGTH = 200
    
    def validate(self, prompt: str) -> ValidationResult:
        """
        Check if prompt has sufficient detail.
        
        PRD: "if the prompt is too short or ambiguous, we will warn the user"
        """
        issues = []
        suggestions = []
        score = 100
        
        # Length check
        if len(prompt) < self.MIN_LENGTH:
            issues.append(f"Prompt too short ({len(prompt)} chars, need {self.MIN_LENGTH}+)")
            suggestions.append("Add more details about what you want to build")
            score -= 40
        
        # Missing key sections
        has_purpose = any(word in prompt.lower() for word in ['build', 'create', 'want', 'need'])
        if not has_purpose:
            issues.append("Purpose unclear")
            suggestions.append("Start with 'I want to build...' or 'I need...'")
            score -= 20
        
        has_features = len(prompt.split('.')) > 1
        if not has_features:
            issues.append("No features described")
            suggestions.append("List the key features you need")
            score -= 20
        
        # Tech stack mentioned
        tech_keywords = ['flask', 'fastapi', 'django', 'react', 'vue', 'python', 'javascript']
        has_tech = any(word in prompt.lower() for word in tech_keywords)
        if not has_tech:
            suggestions.append("Consider mentioning preferred tech stack")
            score -= 10
        
        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
            score=max(0, score)
        )
    
    def enhance(self, prompt: str, context: dict = None) -> str:
        """
        Add system instructions to guide agents.
        
        PRD: "inject certain system prompts or context to guide the agents' behavior"
        """
        enhanced = f"""
System Context:
- Generate production-ready code
- Follow language best practices
- Include error handling
- Add docstrings and comments
- Make code testable

User Requirements:
{prompt}

Additional Context:
{context or 'None provided'}

Please analyze these requirements and proceed with implementation.
"""
        return enhanced.strip()
    
    def extract_requirements(self, prompt: str) -> Dict:
        """
        Parse structured information from prompt.
        """
        # Simple extraction (could use NLP in future)
        return {
            'purpose': 'Extracted from prompt',  # TODO: Implement
            'features': [],  # TODO: Parse features
            'tech_stack': [],  # TODO: Detect tech mentions
            'constraints': []  # TODO: Find constraints
        }
```

**Time**: 1 day

---

**Task 3: Refactor Workflow Pipeline (2 days)**

```python
# apps/api/app/workflows/pipeline.py
# MAJOR REFACTOR
