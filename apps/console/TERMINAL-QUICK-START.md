# Terminal Emulator - Quick Start

**Status**: ✅ Ready to use  
**URL**: http://localhost:3001/terminal

---

## Start Everything

```bash
# Terminal 1: API
cd /home/thomas/kyros-praxis/apps/api
../.venv/bin/uvicorn app.main:app --reload --port 8000

# Terminal 2: Console
cd /home/thomas/kyros-praxis/apps/console
npm run dev -- --port 3001

# Browser
open http://localhost:3001/terminal
```

---

## Interface

```
┌─────────────────────────────────────────────────────┐
│ Kyros Terminal                    Ctrl+B Ctrl+M... │
├───────────────────────────┬─────────────────────────┤
│                           │  Agent Dashboard        │
│  Terminal Window          │                         │
│  (xterm.js)               │  📦 Projects (2)        │
│                           │    My Project ✓         │
│  $ echo "Hello"           │    Test Project ⏳      │
│  Hello                    │                         │
│  $                        │  📋 Tasks (3)           │
│                           │    Task 1 🟢 completed  │
│  Type here...             │    Task 2 🔵 running    │
│                           │    Task 3 ⚪ queued     │
│  Press Ctrl+B to          │                         │
│  broadcast!               │  📡 Events (5)          │
│                           │    task_completed       │
└───────────────────────────┴─────────────────────────┘
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Ctrl+B** | Open broadcast modal |
| **Ctrl+M** | Toggle dashboard on/off |
| **Ctrl+L** | Clear terminal |
| **Esc** | Close modal |

---

## Workflow

### 1. Type in Terminal
```
$ aider main.py
> I want to add authentication

AI: I'll help you. We need:
1. User model with email and password
2. Login and register routes
3. JWT token generation
4. Password hashing with bcrypt
```

### 2. Press Ctrl+B
Modal appears with extracted tasks:
- ✅ User model with email and password
- ✅ Login and register routes
- ✅ JWT token generation
- ✅ Password hashing with bcrypt

### 3. Edit & Broadcast
- Edit task names if needed
- Click "🚀 Broadcast to Orchestrator"
- Watch dashboard update in real-time!

### 4. Monitor Progress
Dashboard shows:
- 🆕 New project created
- 📋 4 tasks queued → running → completed
- 📡 Live events streaming
- ✅ Success notifications

---

## Features

### Terminal
- ✅ Full xterm.js terminal
- ✅ Dark theme for coding
- ✅ Scrollback buffer
- ✅ Copy/paste support
- ✅ Text selection
- ✅ Clickable links

### Dashboard
- ✅ Real-time project list
- ✅ Task status with colors
- ✅ Event stream (SSE)
- ✅ Auto-refresh every 3-5s
- ✅ Select projects to view tasks

### Broadcast
- ✅ Auto-detects numbered lists (1., 2., 3.)
- ✅ Auto-detects bullet points (-, •)
- ✅ Auto-detects "I will" statements
- ✅ Manual add/edit/remove tasks
- ✅ Creates project automatically
- ✅ Launches parallel execution

---

## Status Colors

| Color | Status |
|-------|--------|
| 🟢 Green | completed, succeeded |
| 🔵 Blue | running, executing |
| 🟡 Yellow | queued, planning |
| 🔴 Red | failed |
| ⚪ Gray | other |

---

## Example Session

```bash
# Open terminal
open http://localhost:3001/terminal

# Type some work
$ echo "Planning my app"
Planning my app
$ cat tasks.txt
1. Add user authentication
2. Create dashboard
3. Add payment integration

# Press Ctrl+B
# Modal shows:
#   ✓ Add user authentication
#   ✓ Create dashboard
#   ✓ Add payment integration

# Click "Broadcast"
# Terminal shows:
✓ Broadcast successful!
  Project: Terminal Session - 2025-01-12 10:30
  Tasks: 3

Check the dashboard → for status updates
$ 

# Dashboard updates:
📦 Projects (1)
  Terminal Session - 2025-01-12 10:30 🔵 executing

📋 Tasks (3)
  Add user authentication 🔵 running
  Create dashboard ⚪ queued
  Add payment integration ⚪ queued

📡 Events (2)
  batch_started
  task_created
```

---

## Tips

1. **Split Pane**: Drag the divider to resize
2. **Toggle Dashboard**: Press Ctrl+M for full terminal
3. **Clear Terminal**: Press Ctrl+L to start fresh
4. **Multiple Projects**: Create as many as you want
5. **Task Editing**: Add/remove tasks in broadcast modal
6. **Real-time**: Dashboard updates automatically

---

## Troubleshooting

### Terminal not loading
- Check console is running on port 3001
- Check browser console for errors
- Refresh page (Ctrl+R)

### Dashboard empty
- Check API is running on port 8000
- Check database is running
- Create a project first

### Broadcast not working
- Check API connection
- Check token/auth if required
- Check browser console for errors

### Can't type in terminal
- Terminal is currently mock-only
- Will echo back what you type
- Real shell coming in Phase 2.5

---

## What's Next

### Coming Soon:
- Real shell integration (PTY)
- Run actual commands
- aider/claude/codex detection
- Artifact viewer
- Code preview

### Current Limitations:
- Terminal is mock (echoes input)
- No actual shell execution
- No file system access
- Simple pattern matching

**But**: Broadcast and monitoring work perfectly!

---

## Need Help?

1. Check API is running: http://localhost:8000/health
2. Check console is running: http://localhost:3001
3. Check database: `docker ps | grep kyros-api-db`
4. Check browser console for errors
5. Restart everything if needed

---

**Ready to use!** 🚀

Start typing in the terminal and press Ctrl+B when you see a plan!
