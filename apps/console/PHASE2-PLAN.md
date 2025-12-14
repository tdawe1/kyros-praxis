# Phase 2: Terminal Emulator Implementation Plan

**Target**: 8-11 hours  
**Approach**: Incremental with testing at each step

---

## Implementation Phases

### Phase 2.1: Terminal Component (3-4h)
1. **Install Dependencies** (15 min)
   - xterm.js and addons
   - node-pty (for backend PTY)
   - WebSocket support

2. **Create Terminal Component** (2h)
   - Basic xterm.js integration
   - Terminal session management
   - PTY backend endpoint
   - Input/output handling

3. **Test Terminal** (30 min)
   - Can run shell commands
   - Copy/paste works
   - Resizing works
   - Colors/formatting work

4. **Polish** (1h)
   - Fit addon
   - Search addon
   - Web links addon
   - Keyboard shortcuts

### Phase 2.2: Conversation Capture (2h)
1. **AI Detection** (45 min)
   - Detect aider/claude/codex prompts
   - Parse conversation structure
   - Extract plans/tasks

2. **Capture Buffer** (45 min)
   - Store conversation history
   - Mark AI responses
   - Track context

3. **Test Capture** (30 min)
   - Run aider session
   - Verify capture
   - Check parsing

### Phase 2.3: Broadcast Integration (1-2h)
1. **Broadcast UI** (45 min)
   - Keyboard shortcut (Ctrl+B)
   - Modal dialog
   - Plan extraction

2. **API Integration** (45 min)
   - Connect to /batch/runs
   - Send tasks to orchestrator
   - Show confirmation

3. **Test Broadcast** (30 min)
   - Capture conversation
   - Broadcast to API
   - Verify run created

### Phase 2.4: Dashboard UI (2-3h)
1. **Split Pane Layout** (1h)
   - Terminal left, dashboard right
   - Resizable split
   - Responsive design

2. **Agent Status Display** (1h)
   - Project list
   - Task status
   - Progress indicators

3. **Real-time Updates** (1h)
   - SSE connection
   - Live task updates
   - Memory viewer

4. **Polish** (30 min)
   - Styling
   - Transitions
   - Error handling

---

## Technical Stack

### Frontend
- **Terminal**: xterm.js + addons
- **UI Framework**: React (existing Next.js)
- **Styling**: CSS modules / Tailwind
- **State**: React Context + hooks
- **Real-time**: EventSource (SSE)

### Backend (Already exists!)
- **PTY**: Need to add WebSocket endpoint
- **Multi-agent API**: ✅ Already built

---

## File Structure

```
apps/console/
├── app/
│   ├── terminal/
│   │   ├── page.tsx                    # Main terminal page
│   │   ├── components/
│   │   │   ├── Terminal.tsx            # xterm.js component
│   │   │   ├── TerminalSession.tsx     # Session manager
│   │   │   ├── ConversationCapture.tsx # AI detection
│   │   │   ├── BroadcastModal.tsx      # Ctrl+B modal
│   │   │   ├── Dashboard.tsx           # Agent dashboard
│   │   │   ├── SplitPane.tsx           # Layout component
│   │   │   ├── ProjectList.tsx         # Projects view
│   │   │   ├── TaskList.tsx            # Tasks view
│   │   │   └── MemoryViewer.tsx        # Shared memory
│   │   └── hooks/
│   │       ├── useTerminal.ts          # Terminal hook
│   │       ├── useConversation.ts      # Capture hook
│   │       └── useOrchestrator.ts      # API hook
│   └── lib/
│       └── terminal/
│           ├── pty.ts                  # PTY client
│           ├── ai-detector.ts          # AI prompt detection
│           └── plan-extractor.ts       # Parse plans
└── package.json
```

---

## Dependencies to Install

```json
{
  "dependencies": {
    "@xterm/xterm": "^5.3.0",
    "@xterm/addon-fit": "^0.8.0",
    "@xterm/addon-web-links": "^0.9.0",
    "@xterm/addon-search": "^0.13.0",
    "socket.io-client": "^4.7.0"
  },
  "devDependencies": {
    "@types/socket.io-client": "^3.0.0"
  }
}
```

Backend (Python):
```txt
python-socketio
```

---

## API Endpoints Needed

### Already Built ✅:
- `POST /projects` - Create project
- `POST /projects/{id}/tasks` - Create tasks
- `POST /batch/runs` - Launch batch
- `GET /memory/{project_id}/events` - SSE stream
- `GET /projects/{id}/dashboard` - Dashboard data

### Need to Build:
- `WebSocket /terminal` - PTY connection

---

## Testing Strategy

### Phase 2.1 Test:
```bash
# Terminal should work
cd apps/console
npm run dev
# Visit /terminal
# Type: echo "Hello World"
# Should see output
```

### Phase 2.2 Test:
```bash
# In terminal:
aider main.py
# > Add a user class
# Verify conversation captured
```

### Phase 2.3 Test:
```bash
# Press Ctrl+B
# Should show broadcast modal
# Select crew, broadcast
# Verify batch run created
```

### Phase 2.4 Test:
```bash
# Dashboard should show:
# - Active projects
# - Running tasks
# - Real-time updates
```

---

## Success Criteria

- [ ] Terminal runs shell commands
- [ ] Can run aider/claude/codex
- [ ] Conversation is captured
- [ ] Ctrl+B broadcasts plan
- [ ] Dashboard shows agent status
- [ ] Real-time SSE updates work
- [ ] Split pane is resizable
- [ ] Works on localhost + docker

---

## Time Estimates

| Phase | Optimistic | Realistic | Pessimistic |
|-------|-----------|-----------|-------------|
| 2.1   | 2.5h      | 3.5h      | 5h          |
| 2.2   | 1.5h      | 2h        | 3h          |
| 2.3   | 1h        | 1.5h      | 2.5h        |
| 2.4   | 2h        | 2.5h      | 4h          |
| **Total** | **7h** | **9.5h**  | **14.5h**   |

---

## Start Point

Begin with Phase 2.1 - Terminal Component.

First steps:
1. Install xterm.js
2. Create Terminal.tsx component
3. Add WebSocket endpoint to API
4. Test basic terminal I/O

Let's go! 🚀
