# Frontend Wiring Guide - What's Missing

**Current Status**: UI is built, needs backend integration  
**Estimated Time**: 2-4 hours for full wiring

---

## Current State

### ✅ What's Already Working

1. **Terminal UI** - xterm.js renders correctly
2. **Split Pane** - Resizable interface works
3. **Dashboard** - Fetches projects/tasks from API
4. **Broadcast Modal** - Creates projects and launches batch runs
5. **Keyboard Shortcuts** - Ctrl+B, Ctrl+M, Ctrl+L work
6. **Conversation Buffer** - Captures typed text (500 lines)
7. **API Integration** - All endpoints connected

### ⚠️ What's Mock/Incomplete

1. **Terminal Execution** - Just echoes input, doesn't run shell
2. **Real-time Updates** - Dashboard polls every 3-5s, could use SSE better
3. **AI Detection** - Simple pattern matching, not tool-specific
4. **Artifact Display** - Dashboard doesn't show artifacts yet

---

## 1. Wire Up Real Shell Execution (Critical)

**Status**: Currently MOCK  
**Impact**: HIGH  
**Time**: 2-3 hours

### What Needs to Happen

Terminal currently echoes input character-by-character. Need to:

1. **Add WebSocket endpoint to API**
2. **Install node-pty on backend**
3. **Connect terminal to WebSocket**
4. **Handle stdin/stdout streaming**

### Backend Changes Needed

**File**: `api/app/main.py`

```python
from fastapi import WebSocket, WebSocketDisconnect
import pty
import os
import subprocess
import select
import asyncio

@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    """WebSocket endpoint for terminal PTY."""
    await websocket.accept()
    
    # Fork PTY
    pid, fd = pty.fork()
    
    if pid == 0:
        # Child process - exec shell
        os.execvp("/bin/bash", ["/bin/bash"])
    
    # Parent process - handle I/O
    try:
        async def read_output():
            while True:
                # Read from PTY
                r, _, _ = select.select([fd], [], [], 0.1)
                if r:
                    output = os.read(fd, 10240)
                    if output:
                        await websocket.send_bytes(output)
                await asyncio.sleep(0.01)
        
        async def write_input():
            while True:
                data = await websocket.receive_bytes()
                os.write(fd, data)
        
        # Run both simultaneously
        await asyncio.gather(
            read_output(),
            write_input()
        )
    
    except WebSocketDisconnect:
        os.kill(pid, 9)  # Kill child process
        os.close(fd)
```

**Dependencies**:
```bash
# No additional Python packages needed for pty
# pty is built into Python standard library
```

### Frontend Changes Needed

**File**: `console/app/terminal/components/Terminal.tsx`

Add WebSocket connection:

```typescript
useEffect(() => {
  if (!terminalRef.current) return;
  
  // ... existing terminal setup ...
  
  // Connect to WebSocket
  const ws = new WebSocket('ws://localhost:8000/ws/terminal');
  
  ws.onopen = () => {
    console.log('Terminal connected');
  };
  
  ws.onmessage = (event) => {
    // Read from shell, write to terminal
    if (event.data instanceof Blob) {
      event.data.text().then((text) => {
        term.write(text);
      });
    } else {
      term.write(event.data);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    term.writeln('\r\nConnection error. Refresh to reconnect.');
  };
  
  ws.onclose = () => {
    term.writeln('\r\nConnection closed. Refresh to reconnect.');
  };
  
  // Handle user input -> send to WebSocket
  if (onData) {
    term.onData((data) => {
      ws.send(data);
      onData(data); // Still call for conversation capture
    });
  }
  
  return () => {
    ws.close();
    term.dispose();
  };
}, []);
```

### Testing

```bash
# 1. Start API with WebSocket support
cd apps/api
../.venv/bin/uvicorn app.main:app --reload --port 8000

# 2. Start console
cd apps/console
npm run dev

# 3. Open terminal
open http://localhost:3000/terminal

# 4. Type commands - they should execute!
ls
pwd
echo "Hello from real shell!"
```

---

## 2. Enhance Real-Time Dashboard Updates

**Status**: POLLING (3-5 second intervals)  
**Impact**: MEDIUM  
**Time**: 30 minutes

### Current Behavior

Dashboard uses `setInterval` to poll API every 3-5 seconds.

### Better Approach: SSE

**File**: `console/app/terminal/components/Dashboard.tsx`

Replace polling with SSE:

```typescript
// REPLACE THIS:
useEffect(() => {
  const fetchTasks = async () => { /* ... */ };
  fetchTasks();
  const interval = setInterval(fetchTasks, 3000);
  return () => clearInterval(interval);
}, []);

// WITH THIS:
useEffect(() => {
  if (!selectedProject) return;
  
  // Initial fetch
  const fetchTasks = async () => {
    const response = await fetch(`${apiBase}/projects/${selectedProject}/tasks`, { headers });
    const tasks = await response.json();
    setData((prev) => ({ ...prev, activeTasks: tasks }));
  };
  fetchTasks();
  
  // Subscribe to events
  const eventUrl = token
    ? `${apiBase}/memory/${selectedProject}/events?token=${token}`
    : `${apiBase}/memory/${selectedProject}/events`;
  
  const eventSource = new EventSource(eventUrl);
  
  eventSource.onmessage = (event) => {
    const eventData = JSON.parse(event.data);
    
    // On task events, refetch tasks
    if (eventData.event_type === 'task_created' || 
        eventData.event_type === 'task_completed') {
      fetchTasks();
    }
    
    // Add to recent events
    setData((prev) => ({
      ...prev,
      recentEvents: [eventData, ...prev.recentEvents].slice(0, 10)
    }));
  };
  
  return () => {
    eventSource.close();
  };
}, [selectedProject]);
```

**Benefit**: Instant updates instead of 3-5 second delay!

---

## 3. Better Conversation Capture

**Status**: BASIC (captures typed text)  
**Impact**: LOW  
**Time**: 1 hour

### Current Behavior

Only captures what YOU type, not what the shell outputs.

### Enhancement

Capture both input AND output for better task extraction.

**File**: `console/app/terminal/page.tsx`

```typescript
// Add state for full conversation (input + output)
const [fullConversation, setFullConversation] = useState<
  Array<{ type: 'input' | 'output'; text: string }>
>([]);

// In handleTerminalData:
const handleTerminalData = useCallback((data: string) => {
  // Existing code...
  
  // Capture input
  if (data === '\r') {
    setFullConversation((prev) => [
      ...prev,
      { type: 'input', text: currentLine }
    ].slice(-500));
  }
}, [currentLine]);

// NEW: Capture output from WebSocket
useEffect(() => {
  if (typeof window === 'undefined') return;
  
  // Hook into terminal write to capture output
  const originalWrite = (window as any).__terminal?.write;
  if (originalWrite) {
    (window as any).__terminal.write = (data: string) => {
      // Call original
      originalWrite.call((window as any).__terminal, data);
      
      // Capture output
      if (data && !data.includes('\x1b[')) { // Filter control codes
        setFullConversation((prev) => [
          ...prev,
          { type: 'output', text: data }
        ].slice(-500));
      }
    };
  }
}, []);
```

### Better Task Extraction

**File**: `console/app/terminal/components/BroadcastModal.tsx`

```typescript
const extractTasksFromConversation = (
  buffer: Array<{ type: 'input' | 'output'; text: string }>
): string[] => {
  const tasks: string[] = [];
  
  // Look for AI responses (usually longer, multi-line)
  let currentAIResponse = '';
  
  for (let i = 0; i < buffer.length; i++) {
    const item = buffer[i];
    
    // Detect AI responses (heuristic: output after ">" prompt)
    if (item.type === 'output' && item.text.length > 50) {
      currentAIResponse += item.text;
    }
    
    // Extract from AI response
    if (currentAIResponse.length > 100) {
      // Look for numbered lists
      const numberedTasks = currentAIResponse.match(/^\s*\d+\.\s+(.+)$/gm);
      if (numberedTasks) {
        tasks.push(...numberedTasks.map(t => t.replace(/^\s*\d+\.\s+/, '')));
      }
      
      // Look for bullet points
      const bulletTasks = currentAIResponse.match(/^\s*[-•]\s+(.+)$/gm);
      if (bulletTasks) {
        tasks.push(...bulletTasks.map(t => t.replace(/^\s*[-•]\s+/, '')));
      }
      
      // Look for "I will" / "We'll" statements
      const willStatements = currentAIResponse.match(/(I will|We'll|Let's|I'll)\s+([^.!?]+)/gi);
      if (willStatements) {
        tasks.push(...willStatements);
      }
      
      currentAIResponse = '';
    }
  }
  
  return [...new Set(tasks)].slice(0, 10); // Dedupe, max 10
};
```

---

## 4. Display Artifacts in Dashboard

**Status**: NOT IMPLEMENTED  
**Impact**: MEDIUM  
**Time**: 1 hour

### Add Artifacts Section

**File**: `console/app/terminal/components/Dashboard.tsx`

Add after Recent Events section:

```typescript
{/* Artifacts Section */}
{selectedProject && (
  <div style={{ padding: '16px', borderTop: '1px solid #333' }}>
    <h3 style={{ margin: '0 0 12px', fontSize: '14px', fontWeight: 600 }}>
      Artifacts ({artifacts.length})
    </h3>
    {artifacts.length === 0 ? (
      <p style={{ fontSize: '12px', color: '#999' }}>
        No artifacts yet. Agents will generate code here.
      </p>
    ) : (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {artifacts.map((artifact) => (
          <details
            key={artifact.id}
            style={{
              padding: '12px',
              backgroundColor: '#252525',
              border: '1px solid #333',
              borderRadius: '4px',
            }}
          >
            <summary
              style={{
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              📄 {artifact.name}
            </summary>
            <pre
              style={{
                marginTop: '8px',
                padding: '8px',
                backgroundColor: '#1e1e1e',
                border: '1px solid #333',
                borderRadius: '4px',
                fontSize: '11px',
                maxHeight: '200px',
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
              }}
            >
              {artifact.content}
            </pre>
            <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(artifact.content);
                }}
                style={{
                  padding: '4px 12px',
                  backgroundColor: '#0066cc',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#fff',
                  fontSize: '11px',
                  cursor: 'pointer',
                }}
              >
                Copy
              </button>
              <button
                onClick={() => {
                  // Download artifact
                  const blob = new Blob([artifact.content], { type: 'text/plain' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = artifact.name;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                style={{
                  padding: '4px 12px',
                  backgroundColor: '#333',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#fff',
                  fontSize: '11px',
                  cursor: 'pointer',
                }}
              >
                Download
              </button>
            </div>
          </details>
        ))}
      </div>
    )}
  </div>
)}
```

Add artifacts state and fetching:

```typescript
const [artifacts, setArtifacts] = useState<any[]>([]);

// Fetch artifacts
useEffect(() => {
  if (!selectedProject) return;
  
  const fetchArtifacts = async () => {
    const response = await fetch(`${apiBase}/projects/${selectedProject}/dashboard`, { headers });
    const dashboard = await response.json();
    setArtifacts(dashboard.artifacts || []);
  };
  
  fetchArtifacts();
  const interval = setInterval(fetchArtifacts, 5000);
  return () => clearInterval(interval);
}, [selectedProject]);
```

---

## 5. AI Tool Detection

**Status**: GENERIC pattern matching  
**Impact**: LOW  
**Time**: 1 hour

### Detect Specific AI Tools

**File**: `console/app/terminal/lib/ai-detector.ts` (NEW)

```typescript
export type AITool = 'aider' | 'claude' | 'codex' | 'cursor' | 'copilot' | 'unknown';

export function detectAITool(conversationBuffer: string[]): AITool {
  const fullText = conversationBuffer.join('\n').toLowerCase();
  
  // Aider detection
  if (fullText.includes('aider v') || fullText.includes('aider>')) {
    return 'aider';
  }
  
  // Claude detection
  if (fullText.includes('claude') || fullText.includes('anthropic')) {
    return 'claude';
  }
  
  // Codex/OpenAI
  if (fullText.includes('openai') || fullText.includes('gpt-')) {
    return 'codex';
  }
  
  // Cursor
  if (fullText.includes('cursor')) {
    return 'cursor';
  }
  
  // Copilot
  if (fullText.includes('copilot') || fullText.includes('github copilot')) {
    return 'copilot';
  }
  
  return 'unknown';
}

export function extractPlanFromAI(
  tool: AITool,
  conversationBuffer: string[]
): string[] {
  const fullText = conversationBuffer.join('\n');
  
  switch (tool) {
    case 'aider':
      // Aider often uses markdown with numbered lists
      return extractNumberedList(fullText);
    
    case 'claude':
      // Claude uses clear structure
      return extractBulletList(fullText);
    
    case 'codex':
      // Codex varies
      return extractMixedFormat(fullText);
    
    default:
      return extractGeneric(fullText);
  }
}

function extractNumberedList(text: string): string[] {
  const matches = text.match(/^\s*\d+\.\s+(.+)$/gm) || [];
  return matches.map(m => m.replace(/^\s*\d+\.\s+/, '').trim());
}

function extractBulletList(text: string): string[] {
  const matches = text.match(/^\s*[-•*]\s+(.+)$/gm) || [];
  return matches.map(m => m.replace(/^\s*[-•*]\s+/, '').trim());
}

function extractMixedFormat(text: string): string[] {
  return [
    ...extractNumberedList(text),
    ...extractBulletList(text)
  ];
}

function extractGeneric(text: string): string[] {
  // Fallback: look for sentences with action verbs
  const patterns = [
    /(create|build|implement|add|write|design|develop|fix|update)\s+([^.!?]+)/gi,
    /(I will|We'll|Let's|I'll)\s+([^.!?]+)/gi
  ];
  
  const tasks: string[] = [];
  patterns.forEach(pattern => {
    const matches = text.matchAll(pattern);
    for (const match of matches) {
      tasks.push(match[0].trim());
    }
  });
  
  return tasks;
}
```

Use in BroadcastModal:

```typescript
import { detectAITool, extractPlanFromAI } from '../lib/ai-detector';

// In extractTasksFromConversation:
const tool = detectAITool(conversationBuffer);
const tasks = extractPlanFromAI(tool, conversationBuffer);
```

---

## 6. Environment Configuration

**Status**: HARDCODED localhost  
**Impact**: LOW  
**Time**: 10 minutes

### Add Environment Variables

**File**: `console/.env.local` (CREATE)

```bash
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_PTY=true
NEXT_PUBLIC_ENABLE_ARTIFACTS=true
NEXT_PUBLIC_ENABLE_AI_DETECTION=true
```

Update components to use env vars:

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE_URL || 'ws://localhost:8000';
const ENABLE_PTY = process.env.NEXT_PUBLIC_ENABLE_PTY === 'true';
```

---

## Priority Wiring Checklist

### Must Have (For Production)
- [ ] Real shell execution via WebSocket/PTY (2-3h)
- [ ] Environment configuration (.env.local) (10 min)

### Should Have (For Better UX)
- [ ] SSE-based dashboard updates (30 min)
- [ ] Artifact display with download (1h)
- [ ] Better conversation capture (1h)

### Nice to Have (Polish)
- [ ] AI tool detection (1h)
- [ ] Syntax highlighting for artifacts (30 min)
- [ ] Progress indicators on tasks (30 min)
- [ ] Toast notifications for events (30 min)

---

## Quick Start: Minimum Viable Wiring

**Want to get it working fast? Do these 2 things:**

### 1. Add PTY WebSocket (2-3h)
This is the ONLY critical missing piece. Everything else is polish.

### 2. Add .env.local (5 min)
Makes configuration easier.

**Then you have**: A fully functional terminal emulator with multi-agent orchestration!

---

## Testing Your Changes

```bash
# 1. Terminal execution test
cd console && npm run dev
# Open http://localhost:3000/terminal
# Type: ls -la
# Should see real output!

# 2. Broadcast test
# Type a plan in terminal
# Press Ctrl+B
# Should extract tasks and create project

# 3. Dashboard test
# Should see real-time updates when tasks complete

# 4. Artifacts test
# Run a workflow that generates artifacts
# Should appear in dashboard
```

---

## Summary

**Current State**: 85% complete  
**Missing**: Real shell execution (PTY)  
**Time to Fully Wire**: 2-4 hours  
**Critical Path**: WebSocket + PTY backend

Everything else is working or is polish. The terminal UI, dashboard, broadcast system, and API integration are all functional!
