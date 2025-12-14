# API Contract - Multi-Agent Workflow Endpoints

**Version**: 1.0  
**Date**: Day 8  
**For**: Agent B (Frontend Integration)

---

## Base URL

```
Development: http://localhost:8000
Production: TBD
```

## Authentication

All endpoints require authentication via HTTP-only cookies:
- Cookie: `access_token`
- Credentials must be included in fetch: `credentials: 'include'`

---

## Workflow Endpoints

### 1. Generate Project (Start Workflow)

**Endpoint**: `POST /projects/{project_id}/generate`

**Purpose**: Start multi-agent workflow with user's prompt

**Request**:
```typescript
{
  prompt: string  // User's detailed prompt (min 50 chars recommended)
}
```

**Response** (202 Accepted):
```typescript
{
  project_id: string
  workflow_id: string
  status: "awaiting_approval"  // PRD: Pauses at approval gate
  stage: "planner"
  specification: {
    purpose: string
    components: string[]
    technology: object
    file_structure: object
    dependencies: string[]
    // ... more fields
  }
  message: string
  validation_score: number  // 0-100
}
```

**Usage**:
```typescript
const response = await fetch(`/projects/${projectId}/generate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({ prompt: userPrompt })
});

const result = await response.json();
// Show specification to user for approval
```

---

### 2. Approve Specification

**Endpoint**: `POST /projects/{project_id}/approve`

**Purpose**: Approve planner's specification and continue to code generation

**Request**:
```typescript
{
  approved: boolean  // true to continue, false to reject
  specification: object  // The specification being approved
}
```

**Response** (200 OK):
```typescript
{
  project_id: string
  workflow_id: string
  status: "completed" | "needs_refinement" | "failed"
  code_files: Array<{
    path: string
    content: string
    description: string
  }>
  test_files: Array<{
    file: string
    content: string
    description: string
  }>
  review: {
    matches_spec: boolean
    overall_quality: "excellent" | "good" | "fair" | "poor"
    issues: Array<{
      severity: "critical" | "high" | "medium" | "low"
      description: string
      suggestion: string
    }>
  }
  message: string
}
```

**Usage**:
```typescript
// User approves specification
const response = await fetch(`/projects/${projectId}/approve`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({ 
    approved: true,
    specification: approvedSpec 
  })
});

const result = await response.json();
// Show generated code to user
```

---

### 3. Regenerate with Refinements

**Endpoint**: `POST /projects/{project_id}/regenerate`

**Purpose**: Refine and regenerate project with user's feedback

**Request**:
```typescript
{
  refinement_notes: string  // User's refinement instructions
}
```

**Response** (200 OK):
```typescript
{
  project_id: string
  workflow_id: string
  status: "awaiting_approval" | "completed" | "failed"
  iteration: number  // Iteration count
  message: string
  // If awaiting_approval: includes specification
  // If completed: includes code_files and test_files
}
```

**Usage**:
```typescript
// User wants to refine
const response = await fetch(`/projects/${projectId}/regenerate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({ 
    refinement_notes: "Make it mobile-friendly with responsive design" 
  })
});
```

---

### 4. Get Specification

**Endpoint**: `GET /projects/{project_id}/specification`

**Purpose**: Retrieve planner's specification

**Response** (200 OK):
```typescript
{
  project_id: string
  specification: {
    purpose: string
    components: string[]
    technology: object
    file_structure: object
    dependencies: string[]
    data_models: object
    implementation_plan: string[]
    testing_considerations: string[]
    challenges: string[]
  }
  created_at: string  // ISO datetime
  status: "completed" | "failed"
}
```

**Usage**:
```typescript
const response = await fetch(`/projects/${projectId}/specification`, {
  credentials: 'include'
});
const { specification } = await response.json();
```

---

### 5. Get Generated Code

**Endpoint**: `GET /projects/{project_id}/code`

**Purpose**: Retrieve all generated code and test files

**Response** (200 OK):
```typescript
{
  project_id: string
  code_files: Array<{
    id: string
    name: string  // File path
    content: string  // File content
    metadata: {
      description: string
      generated_by: "coder_agent"
    }
    created_at: string
  }>
  test_files: Array<{
    id: string
    name: string
    content: string
    metadata: {
      description: string
      generated_by: "tester_agent"
    }
    created_at: string
  }>
  total_files: number
}
```

**Usage**:
```typescript
const response = await fetch(`/projects/${projectId}/code`, {
  credentials: 'include'
});
const { code_files, test_files } = await response.json();
// Display in CodeViewer component
```

---

### 6. Get Workflow Status

**Endpoint**: `GET /projects/{project_id}/status`

**Purpose**: Check current workflow progress

**Response** (200 OK):
```typescript
{
  project_id: string
  project_status: "planning" | "generating" | "completed" | "failed"
  stages: Array<{
    stage: "planner" | "coder" | "tester"
    status: "active" | "completed" | "failed"
    started_at: string
    completed_at: string | null
  }>
}
```

**Usage**:
```typescript
// Poll for status updates
const response = await fetch(`/projects/${projectId}/status`, {
  credentials: 'include'
});
const { project_status, stages } = await response.json();
```

---

## Complete User Flow

### Flow 1: Successful Generation

```typescript
// 1. User submits prompt
const generate = await fetch(`/projects/${id}/generate`, {
  method: 'POST',
  body: JSON.stringify({ prompt: userInput }),
  credentials: 'include'
});
const { status, specification } = await generate.json();
// status === "awaiting_approval"

// 2. Show specification to user → User approves
const approve = await fetch(`/projects/${id}/approve`, {
  method: 'POST',
  body: JSON.stringify({ approved: true, specification }),
  credentials: 'include'
});
const { code_files, test_files } = await approve.json();

// 3. Display generated code in CodeViewer
<CodeViewer files={code_files} tests={test_files} />
```

### Flow 2: Refinement Loop

```typescript
// User wants to refine
const refine = await fetch(`/projects/${id}/regenerate`, {
  method: 'POST',
  body: JSON.stringify({ 
    refinement_notes: "Add dark mode support" 
  }),
  credentials: 'include'
});
const result = await refine.json();

// If awaiting approval, show new spec
if (result.status === "awaiting_approval") {
  // Show updated specification
  // User can approve or refine again
}
```

---

## Error Handling

All endpoints may return:

**400 Bad Request**:
```typescript
{
  detail: string  // Error message
  validation_errors?: Array<{
    field: string
    message: string
  }>
}
```

**401 Unauthorized**:
```typescript
{
  detail: "Not authenticated"
}
```

**404 Not Found**:
```typescript
{
  detail: "Project not found" | "No specification found" | "No code files found"
}
```

**500 Internal Server Error**:
```typescript
{
  detail: string
  correlationId?: string  // For debugging
}
```

---

## TypeScript Types

```typescript
// Request Types
interface WorkflowGenerateRequest {
  prompt: string;
}

interface WorkflowApproveRequest {
  approved: boolean;
  specification: Specification;
}

interface WorkflowRefineRequest {
  refinement_notes: string;
}

// Response Types
interface Specification {
  purpose: string;
  components: string[];
  technology: Record<string, any>;
  file_structure: Record<string, any>;
  dependencies: string[];
  data_models?: Record<string, any>;
  implementation_plan?: string[];
  testing_considerations?: string[];
  challenges?: string[];
}

interface CodeFile {
  id: string;
  name: string;
  content: string;
  metadata: {
    description: string;
    generated_by: string;
  };
  created_at: string;
}

interface CodeReview {
  matches_spec: boolean;
  overall_quality: 'excellent' | 'good' | 'fair' | 'poor';
  issues: Array<{
    severity: 'critical' | 'high' | 'medium' | 'low';
    description: string;
    suggestion: string;
  }>;
}

interface WorkflowResult {
  project_id: string;
  workflow_id: string;
  status: 'awaiting_approval' | 'completed' | 'needs_refinement' | 'failed';
  stage?: string;
  specification?: Specification;
  code_files?: CodeFile[];
  test_files?: CodeFile[];
  review?: CodeReview;
  message: string;
  iteration?: number;
  validation_score?: number;
}
```

---

## Notes for Frontend Implementation

### 1. State Management

```typescript
// Recommended state structure
interface ProjectState {
  status: 'idle' | 'generating' | 'awaiting_approval' | 'completed' | 'failed';
  currentStage: 'prompt' | 'spec_review' | 'code_generation' | 'code_view';
  specification?: Specification;
  codeFiles?: CodeFile[];
  testFiles?: CodeFile[];
  error?: string;
}
```

### 2. Loading States

- Show spinner during `/generate` (may take 30-60 seconds for planner)
- Show progress during `/approve` (coder + tester may take 60-120 seconds)
- Consider SSE for real-time progress (future enhancement)

### 3. Error Display

- Show validation errors before allowing submit
- Display correlationId for debugging
- Provide "retry" option on failures

### 4. Iteration Tracking

- Store iteration count in state
- Disable refinement after max iterations (3)
- Show diff between iterations

---

## Testing

### Mock Data

```typescript
// Mock successful generation response
const mockGenerate: WorkflowResult = {
  project_id: "test-123",
  workflow_id: "wf-456",
  status: "awaiting_approval",
  stage: "planner",
  specification: {
    purpose: "Build a todo app",
    components: ["Frontend", "Backend", "Database"],
    technology: { frontend: "React", backend: "FastAPI" },
    file_structure: {},
    dependencies: ["react", "fastapi"]
  },
  message: "Specification ready for review",
  validation_score: 85
};
```

### Test Endpoints

```bash
# Create project
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "description": "Test"}' \
  --cookie "access_token=..."

# Generate
curl -X POST http://localhost:8000/projects/{id}/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Build a todo app with React and FastAPI"}' \
  --cookie "access_token=..."
```

---

**Questions?** Contact Agent A or refer to `/apps/api/app/routers/projects.py` for implementation details.
