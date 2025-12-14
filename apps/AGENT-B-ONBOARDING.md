# Agent B Onboarding Package

**Welcome, Agent B (GPT-5-Codex)!**

You're working in parallel with Agent A (Droid) to implement a PRD-compliant multi-agent code generation system.

---

## Quick Context

**Project**: Kyros Praxis - AI-powered code generation platform  
**Goal**: Build prompt-driven development system (PRD requirements)  
**Status**: 75-80% complete, needs PRD alignment  
**Timeline**: 15 days (parallel execution with Agent A)

**Your Role**: Frontend implementation (TypeScript/React)  
**Agent A's Role**: Backend implementation (Python/FastAPI)

---

## Your Territory

**You Own**:
```
apps/console/                    # Your workspace
  ├── app/
  │   ├── prompt-builder/        # You'll create this
  │   ├── code-viewer/           # You'll create this
  │   ├── components/            # You'll add components
  │   ├── lib/                   # You'll update API client
  │   └── state/                 # You'll fix tests
  └── package.json               # You can update if needed
```

**You DON'T Touch**:
```
apps/api/                        # Agent A's territory
apps/daemon/                     # Not used yet
```

**Shared (Request from Agent A)**:
```
apps/shared/ui/                  # Request component additions
```

---

## Your Tasks (15 Days)

### Days 1-2: Critical Fixes (Phase 0)

**Priority**: 🔴 CRITICAL - Must complete before Phase 1

#### Task 1: Rewrite Auth Context Tests (4 hours)
```
File: apps/console/app/state/auth-context.test.tsx
Problem: Tests still use localStorage, but code uses cookies
Fix: Rewrite tests to validate cookie-based authentication

Current (WRONG):
  const token = localStorage.getItem('token');  // ❌
  
Should test:
  - fetch() called with credentials: 'include'
  - Cookie set by browser (mock document.cookie)
  - Auth state updates correctly
  
Lines: ~150 lines to rewrite
```

#### Task 2: Add correlationId to APIError (30 min)
```
File: apps/console/app/lib/api-client.ts
Line: ~15-20

Add:
  export class APIError extends Error {
    constructor(
      message: string,
      public status: number,
      public correlationId?: string  // ✅ ADD THIS
    ) {
      super(message);
    }
  }

Extract from response headers:
  const correlationId = response.headers.get('X-Correlation-ID');
```

#### Task 3: Update use-run-manager (30 min)
```
File: apps/console/app/lib/use-run-manager.ts
Line: ~70-120

Update error display to show correlationId when available
```

#### Task 4: Run Tests & Verify (1 hour)
```bash
cd apps/console
npm test                          # Should pass
npm run dev                       # Should start
# Manual test: Login flow works
```

**Day 2 Checkpoint**: Report to user "Frontend stable ✅"

---

### Days 3-10: Build PRD Features (Phase 1+2)

**Priority**: 🔴 HIGH - Core PRD requirements

#### Day 3: Prompt Builder Foundation

**Create Directory Structure**:
```
apps/console/app/prompt-builder/
  ├── page.tsx                   # Main page
  ├── types.ts                   # TypeScript types
  └── components/
      └── PromptSection.tsx      # Reusable section component
```

**Task**: Create basic prompt builder UI
```typescript
// page.tsx - Guided prompt input
<PromptBuilder>
  <PromptSection title="Purpose">
    <textarea placeholder="What are you building?" />
  </PromptSection>
  
  <PromptSection title="Features">
    <BulletList />
  </PromptSection>
  
  <PromptSection title="Tech Stack">
    <TechStackSelector />
  </PromptSection>
</PromptBuilder>
```

Time: 8 hours

---

#### Day 4: Prompt Input Components

**Files to Create**:
- `components/PromptInput.tsx` - Main input component
- `components/ValidationFeedback.tsx` - Show validation errors

**Features**:
- Multi-section guided input (purpose, features, tech stack)
- Real-time validation display
- Character count
- Tips/hints per section

Time: 8 hours

---

#### Day 5: Template Library

**Files to Create**:
- `components/TemplateLibrary.tsx` - UI for templates
- `templates.ts` - Template data

**Templates to Add**:
```typescript
const templates = [
  {
    name: "Web Application",
    description: "Full-stack web app with API",
    prompt: "I want to build a web application with..."
  },
  {
    name: "REST API",
    description: "Backend API service",
    prompt: "I need a REST API that..."
  },
  {
    name: "CLI Tool",
    description: "Command-line utility",
    prompt: "Create a CLI tool to..."
  }
];
```

Time: 8 hours

---

#### Day 6: Connect to Backend

**Prerequisites**: Agent A should provide API contract by Day 6

**Files to Update**:
- `lib/api-client.ts` - Add methods for prompt submission

**New API Methods**:
```typescript
// Add these methods to api-client.ts
async submitPrompt(projectId: string, prompt: string): Promise<Run>
async getSpecification(projectId: string): Promise<Specification>
async generateCode(projectId: string): Promise<Run>
async getGeneratedCode(projectId: string): Promise<CodeFiles>
```

**Update page.tsx**:
- Connect submit button to API
- Show loading state
- Handle errors

Time: 8 hours

**Day 6 Sync**: Get API contract from Agent A

---

#### Days 7-8: Code Viewer Component

**Files to Create**:
```
apps/console/app/components/CodeViewer/
  ├── index.tsx              # Main export
  ├── FileTree.tsx           # Left sidebar with file tree
  ├── CodeDisplay.tsx        # Right side showing code
  └── types.ts               # TypeScript types
```

**FileTree.tsx**:
- Hierarchical file/folder display
- Click to select file
- Expandable folders
- File icons

**CodeDisplay.tsx**:
- Syntax highlighting (use prism-react-renderer)
- Line numbers
- Copy button
- Search in file

Time: 12 hours (6 hours per day)

**Install Dependencies**:
```bash
npm install prism-react-renderer
npm install @types/prismjs --save-dev
```

---

#### Day 9: Iteration UI

**Files to Create**:
- `components/SpecReview.tsx` - Review planner output
- `components/DiffViewer.tsx` - Show changes between iterations

**SpecReview.tsx**:
```typescript
<SpecReview spec={plannerOutput}>
  <SpecDisplay spec={spec} />
  <ActionButtons>
    <Button onClick={approve}>Approve & Generate Code</Button>
    <Button onClick={refine}>Refine Prompt</Button>
  </ActionButtons>
</SpecReview>
```

**DiffViewer.tsx**:
- Side-by-side diff
- Highlight changes
- Use react-diff-viewer library

Time: 8 hours

---

#### Day 10: Integration & Flow

**File to Update**: `apps/console/app/planner/page.tsx`

**Complete User Flow**:
```
1. User enters prompt in Prompt Builder
   ↓
2. Submit → API call to Agent A's backend
   ↓
3. Show loading state with SSE events
   ↓
4. Planner completes → Show SpecReview
   ↓
5. User approves → Trigger code generation
   ↓
6. Code completes → Show CodeViewer
   ↓
7. User can refine → Back to Prompt Builder with context
```

**State Management**:
```typescript
type FlowState = 
  | 'input'           // Prompt builder
  | 'planning'        // Planner running
  | 'review'          // Reviewing spec
  | 'coding'          // Code generation
  | 'complete'        // Show code
  | 'error';          // Error state
```

Time: 8 hours

**Day 10 Checkpoint**: Report "Frontend feature complete ✅"

---

### Days 11-13: Testing (Phase 3)

**Priority**: 🟡 MEDIUM - Quality assurance

#### Day 11: Prompt Builder Tests

**File to Create**: `apps/console/app/prompt-builder/PromptBuilder.test.tsx`

**Tests to Write**:
```typescript
describe('PromptBuilder', () => {
  it('validates short prompts', () => { ... });
  it('shows validation feedback', () => { ... });
  it('allows template selection', () => { ... });
  it('submits prompt to API', () => { ... });
  it('handles API errors', () => { ... });
  it('shows loading state during submission', () => { ... });
});
```

Time: 8 hours

---

#### Day 12: Code Viewer Tests

**File to Create**: `apps/console/app/components/CodeViewer.test.tsx`

**Tests to Write**:
```typescript
describe('CodeViewer', () => {
  it('renders file tree', () => { ... });
  it('selects file on click', () => { ... });
  it('displays code with syntax highlighting', () => { ... });
  it('copies code to clipboard', () => { ... });
  it('shows line numbers', () => { ... });
});
```

Time: 8 hours

---

#### Day 13: Integration Tests

**File to Create**: `apps/console/app/planner/page.test.tsx`

**Tests to Write**:
```typescript
describe('Full User Flow', () => {
  it('submits prompt and shows spec', async () => { ... });
  it('approves spec and generates code', async () => { ... });
  it('displays generated code', async () => { ... });
  it('allows refinement', async () => { ... });
  it('handles errors gracefully', async () => { ... });
});
```

Time: 8 hours

**Day 13 Checkpoint**: Report "Frontend tests complete ✅"

---

### Days 14-15: Integration & Polish

**Priority**: 🟢 LOW - Final touches

#### Day 14: End-to-End Testing with Agent A

**Joint Activity**:
1. Agent A starts backend (`cd apps/api && uvicorn app.main:app`)
2. You start frontend (`cd apps/console && npm run dev`)
3. Test full flow manually:
   - Enter prompt
   - See planner output
   - Approve spec
   - See code generation
   - View code
   - Try refinement
4. Document any issues
5. Fix issues

Time: 8 hours

---

#### Day 15: Documentation

**Files to Create**:
- `apps/console/docs/USER_GUIDE.md` - How to use the system
- Update `apps/console/README.md` - Developer docs

**User Guide Contents**:
```markdown
# User Guide

## Getting Started
1. Login to Kyros Praxis
2. Navigate to Planner

## Creating a Project
1. Enter your prompt
2. Use templates if needed
3. Review validation feedback
4. Submit

## Reviewing Specification
1. Read the generated spec
2. Approve or refine
3. Wait for code generation

## Viewing Code
1. Browse file tree
2. View code files
3. Copy code
4. Export as ZIP

## Refining
1. Click "Refine"
2. Adjust prompt
3. Regenerate
```

Time: 4 hours

**Day 15 Final**: Report "PRD Beta Ready ✅"

---

## Sync Protocol

### Daily Status Update Format

Post at end of each day:
```
Day X Status:
✅ Completed: [list tasks]
🔄 In Progress: [current task]
🚧 Blockers: [any issues]
📦 Needs from Agent A: [dependencies]
```

### Critical Sync Points

**Day 2**: Report frontend stable
- Tests pass
- No crashes
- Auth flow works

**Day 6**: Request API contract from Agent A
- Endpoint URLs
- Request/response types
- Error formats

**Day 8**: Test API integration
- Can call Agent A's endpoints
- Responses match contract
- Errors handled

**Day 10**: Report frontend complete
- All components built
- Full flow works (mock or real API)

**Day 13**: Report tests complete
- Test coverage >60%
- All critical paths tested

---

## Blocker Escalation

If blocked, post immediately:
```
🚨 BLOCKER
Agent: B
Task: [what's blocked]
Issue: [specific problem]
Need: [what would unblock]
Priority: HIGH/MEDIUM
```

Example:
```
🚨 BLOCKER
Agent: B
Task: Connect prompt builder to backend
Issue: API endpoint returns 404
Need: Agent A to deploy /projects/{id}/generate
Priority: HIGH
```

---

## Git Workflow

### Your Branch

```bash
cd /home/thomas/kyros-praxis
git checkout -b feat/prompt-builder-ui
```

### Commit Frequently

```bash
git add apps/console/
git commit -m "feat: create prompt builder UI"
git push origin feat/prompt-builder-ui
```

### Commit Message Format

```
type: description

Types:
- feat: new feature
- fix: bug fix
- test: add tests
- docs: documentation
- refactor: code refactor
```

### Example Commits

```
Day 1-2:
- fix: rewrite auth tests for cookies
- fix: add correlationId to APIError

Day 3-5:
- feat: create prompt builder foundation
- feat: add guided input components
- feat: add template library

Day 6:
- feat: connect prompt builder to backend API

Day 7-8:
- feat: create code viewer component
- feat: add syntax highlighting

Day 9:
- feat: add spec review UI
- feat: add diff viewer

Day 10:
- feat: integrate complete user flow

Day 11-13:
- test: add prompt builder tests
- test: add code viewer tests
- test: add integration tests

Day 14-15:
- docs: add user guide
- docs: update README
```

---

## Technical Guidelines

### TypeScript

Use strict mode:
```typescript
// Always type your props
interface Props {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
}

// Use type inference where obvious
const [count, setCount] = useState(0);  // ✅

// Explicit types for complex state
const [state, setState] = useState<FlowState>('input');  // ✅
```

### React Patterns

Use functional components:
```typescript
export function PromptBuilder({ onSubmit }: Props) {
  // ✅ Functional component
}
```

Use hooks:
```typescript
const [prompt, setPrompt] = useState('');
const { data, error, isLoading } = useQuery(...);
```

### Styling

Follow existing patterns in codebase:
```typescript
// Use Tailwind classes
<div className="flex flex-col gap-4 p-6">
  ...
</div>

// Or use shared UI components
import { Button } from '@/shared/ui/components/button';
```

### Error Handling

```typescript
try {
  const result = await apiClient.submitPrompt(projectId, prompt);
  // Handle success
} catch (error) {
  if (error instanceof APIError) {
    console.error('API Error:', error.message, error.correlationId);
    // Show user-friendly error
  } else {
    console.error('Unexpected error:', error);
    // Show generic error
  }
}
```

---

## Resources

### Codebase Files to Read First

Before starting, read these files to understand the structure:

```
1. apps/console/app/state/auth-context.tsx
   → Understand auth flow

2. apps/console/app/lib/api-client.ts
   → Understand API calls

3. apps/console/app/lib/use-run-manager.ts
   → Understand run management

4. apps/console/app/planner/page.tsx
   → See current planner implementation

5. apps/shared/ui/components/button.tsx
   → See shared component pattern
```

### External Dependencies

Already installed:
- Next.js 15
- React 18
- TypeScript
- Tailwind CSS
- Vitest (testing)

You may need to add:
- `prism-react-renderer` (syntax highlighting)
- `react-diff-viewer` (diff display)

### Documentation

- **PRD**: See `PRD_ Prompt-Driven Development via CrewAI Integration.docx`
- **Architecture**: See `apps/ARCHITECTURE.md`
- **Full Plan**: See `apps/UNIFIED-AUDIT-AND-PLAN.md`
- **Parallel Plan**: See `apps/PARALLEL-EXECUTION-PLAN.md` (detailed breakdown)

---

## Success Criteria

### Day 2 Success
- [ ] Auth tests pass
- [ ] Tests validate cookie-based auth
- [ ] correlationId field added
- [ ] No TypeScript errors
- [ ] Frontend starts without crashes

### Day 10 Success
- [ ] Prompt builder UI complete
- [ ] Code viewer component complete
- [ ] Iteration loop functional
- [ ] Can test full flow (even with mock data)
- [ ] No critical bugs

### Day 13 Success
- [ ] Frontend test coverage >60%
- [ ] All components tested
- [ ] Integration tests pass
- [ ] No failing tests

### Day 15 Success
- [ ] End-to-end flow works with Agent A's backend
- [ ] Documentation complete
- [ ] User can:
  - Enter prompt
  - See spec
  - Approve
  - See generated code
  - Refine and iterate
- [ ] **PRD Beta Ready** 🎉

---

## Questions?

If you have questions or need clarification:

1. **About tasks**: Refer to `PARALLEL-EXECUTION-PLAN.md` for detailed breakdown
2. **About architecture**: Refer to `UNIFIED-AUDIT-AND-PLAN.md`
3. **About PRD requirements**: Read the PRD document
4. **Blockers**: Post blocker message immediately

---

## Quick Start

**Your first task** (right now):

1. Read `apps/console/app/state/auth-context.tsx` (understand current code)
2. Read `apps/console/app/state/auth-context.test.tsx` (see wrong tests)
3. Start rewriting tests for cookie-based auth
4. Goal: Tests pass and validate actual behavior

**File**: `apps/console/app/state/auth-context.test.tsx`  
**Time**: 4 hours  
**Priority**: 🔴 CRITICAL

---

**Welcome aboard, Agent B! Let's build this together.** 🚀
