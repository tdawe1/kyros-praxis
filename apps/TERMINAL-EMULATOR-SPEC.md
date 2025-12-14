# Kyros Terminal Emulator - Specification

**Date**: 2025-01-12  
**Status**: 📋 PLANNING

---

## Vision

A **full terminal emulator** that integrates with AI coding assistants (Codex, Claude, Aider, etc.) and the Kyros orchestrator. Users can work naturally with their preferred AI tools while having seamless access to broadcast plans and monitor orchestrated workflows.

---

## User Experience

### Scenario 1: Working with Aider

```
┌─────────────────────────────────────────────────────────────────┐
│ Kyros Terminal - Session: aider-2025-01-12                      │
│ [Ctrl+B] Broadcast  [Ctrl+M] Monitor  [Ctrl+H] Help            │
├────────────────────────────────┬────────────────────────────────┤
│ Terminal (aider)               │ Orchestrator                   │
│                                │                                │
│ $ aider                        │ Status: Connected ✓            │
│ Aider v0.55.0                  │ User: dev@example.com          │
│                                │                                │
│ Added main.py to chat          │ Recent Runs:                   │
│                                │ • run-abc123  succeeded  2m    │
│ > I want to add user auth      │ • run-def456  running    now   │
│   to this Flask app            │                                │
│                                │ [No active broadcast]          │
│ I'll help you add auth. We'll  │                                │
│ need:                          │                                │
│ 1. User model                  │                                │
│ 2. Login/register routes       │                                │
│ 3. JWT tokens                  │                                │
│ 4. Password hashing            │                                │
│                                │                                │
│ Should I proceed?              │                                │
│                                │                                │
│ > yes                          │                                │
│                                │                                │
│ [Creating implementation...]   │                                │
│                                │                                │
│ ⚡ Press Ctrl+B to broadcast   │                                │
│   this plan to orchestrator    │                                │
└────────────────────────────────┴────────────────────────────────┘
```

### Scenario 2: Broadcasting Plan

```
[User presses Ctrl+B]

┌─────────────────────────────────────────────────────────────────┐
│ Broadcast to Orchestrator                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Extract plan from conversation?                                 │
│                                                                 │
│ Last 10 messages:                                              │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ User: I want to add user auth to this Flask app          │ │
│ │ AI: I'll help you add auth. We'll need:                  │ │
│ │ 1. User model                                             │ │
│ │ 2. Login/register routes                                  │ │
│ │ 3. JWT tokens                                             │ │
│ │ 4. Password hashing                                       │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│ Select crew:                                                    │
│ › spec_to_tasks                                                 │
│   code_review                                                   │
│   test_generator                                                │
│                                                                 │
│ [Enter] Broadcast  [Esc] Cancel                                │
└─────────────────────────────────────────────────────────────────┘

[After broadcast]

┌────────────────────────────────┬────────────────────────────────┐
│ Terminal (aider)               │ Orchestrator                   │
│                                │                                │
│ [continuing aider session...]  │ 🚀 Broadcasting...             │
│                                │                                │
│                                │ ✓ Run created: run-xyz789      │
│                                │ Status: queued                 │
│                                │                                │
│                                │ [12:34:56] STATE queued        │
│                                │ [12:34:58] STATE running       │
│                                │   └─ Processing...             │
│                                │                                │
└────────────────────────────────┴────────────────────────────────┘
```

---

## Core Features

### 1. Full Terminal Emulation
- **PTY (Pseudo-Terminal)**: Real terminal, not just subprocess
- **ANSI Support**: Colors, cursor control, etc.
- **Shell Integration**: Bash, zsh, fish, etc.
- **Program Compatibility**: Can run any CLI tool (aider, claude, codex, etc.)

### 2. Split Pane Layout
- **Left Pane**: Main terminal (runs AI tools)
- **Right Pane**: Orchestrator monitor
- **Resizable**: Adjust pane sizes
- **Toggleable**: Hide/show orchestrator pane

### 3. Conversation Monitoring
- **Passive Capture**: Records terminal output
- **AI Detection**: Identifies AI assistant responses
- **Plan Extraction**: Extracts structured plans from conversation
- **History**: Stores conversation for later review

### 4. Orchestrator Integration
- **Broadcast**: Send plan to orchestrator (Ctrl+B)
- **Real-time Monitor**: Stream events in right pane
- **Status Display**: Show active runs
- **Quick Actions**: Cancel, view result, etc.

### 5. Keyboard Shortcuts
- **Ctrl+B**: Broadcast plan to orchestrator
- **Ctrl+M**: Toggle orchestrator monitor
- **Ctrl+L**: List recent runs
- **Ctrl+X**: Cancel active run
- **Ctrl+R**: Show run result
- **Ctrl+H**: Help overlay
- **Ctrl+Q**: Quit

---

## Technical Architecture

### Technology Stack

#### Option A: Python + Textual (Recommended)
**Pros**: 
- Pure Python
- Rich TUI framework
- Built-in widgets
- Easy to extend

**Cons**:
- Performance (vs native)
- Limited terminal emulation

**Stack**:
```python
# UI Framework
textual==0.47.0              # TUI framework
rich==13.7.0                 # Rich text rendering

# Terminal Emulation
pyte==0.8.2                  # Terminal emulator library
ptyprocess==0.7.0            # PTY handling

# Backend Integration
httpx==0.27.2                # HTTP client
sseclient-py==1.8.0          # SSE streaming

# AI Integration (optional)
openai==1.54.0               # For plan extraction
```

#### Option B: Rust + TUI-rs (High Performance)
**Pros**:
- Native performance
- Better terminal emulation
- Smaller binary

**Cons**:
- Rust learning curve
- More complex

#### Option C: Electron + xterm.js (Web-based)
**Pros**:
- Best terminal emulation
- Modern UI
- Cross-platform

**Cons**:
- Heavy (Electron)
- Not native terminal

---

## Implementation Plan

### Phase 1: Basic Terminal Emulator (MVP)
**Time**: 3-4 hours

**Features**:
- [x] Basic terminal emulation (PTY)
- [x] Run any shell command
- [x] ANSI color support
- [x] Keyboard input handling
- [x] Resize support

**Files**:
```
apps/terminal/
├── pyproject.toml
├── requirements.txt
├── kyros_terminal/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── terminal.py          # PTY terminal emulator
│   └── ui.py                # Basic UI
```

### Phase 2: Split Pane + Orchestrator
**Time**: 2-3 hours

**Features**:
- [x] Split pane layout (terminal + monitor)
- [x] Orchestrator client integration
- [x] Real-time event streaming
- [x] Keyboard shortcuts (Ctrl+B, Ctrl+M)

**Files**:
```
kyros_terminal/
├── orchestrator/
│   ├── __init__.py
│   ├── client.py            # API client
│   └── monitor.py           # Event stream handler
└── ui/
    ├── __init__.py
    ├── terminal_widget.py   # Terminal pane
    ├── monitor_widget.py    # Orchestrator pane
    └── layout.py            # Split layout
```

### Phase 3: Conversation Capture
**Time**: 2-3 hours

**Features**:
- [x] Capture terminal output
- [x] Detect AI assistant responses
- [x] Extract structured plans
- [x] Conversation history storage

**Files**:
```
kyros_terminal/
├── capture/
│   ├── __init__.py
│   ├── recorder.py          # Output recorder
│   ├── parser.py            # AI response parser
│   └── extractor.py         # Plan extractor
└── storage/
    ├── __init__.py
    └── history.py           # SQLite storage
```

### Phase 4: Polish + Features
**Time**: 2-3 hours

**Features**:
- [x] Broadcast dialog (select crew)
- [x] Run list overlay
- [x] Help overlay
- [x] Theme customization
- [x] Configuration file

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Kyros Terminal Emulator                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────┐        ┌──────────────────────┐    │
│  │  Terminal Widget   │        │  Monitor Widget      │    │
│  │                    │        │                      │    │
│  │  ┌──────────────┐  │        │  ┌────────────────┐ │    │
│  │  │ PTY Process  │  │        │  │ Event Stream   │ │    │
│  │  │ (aider/etc)  │  │        │  │ (SSE)          │ │    │
│  │  └──────────────┘  │        │  └────────────────┘ │    │
│  │         ↓          │        │         ↑           │    │
│  │  ┌──────────────┐  │        │  ┌────────────────┐ │    │
│  │  │ Output       │  │        │  │ Run Status     │ │    │
│  │  │ Capturer     │──┼────────┼─→│ Display        │ │    │
│  │  └──────────────┘  │        │  └────────────────┘ │    │
│  └────────────────────┘        └──────────────────────┘    │
│           │                               ↑                 │
│           ↓                               │                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Conversation Analyzer                      │   │
│  │  - Detect AI responses                              │   │
│  │  - Extract plans                                    │   │
│  │  - Store history                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                 │
│           ↓                                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          Orchestrator Client                        │   │
│  │  - Authenticate (JWT)                               │   │
│  │  - Create runs                                      │   │
│  │  - Stream events                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                 │
└───────────┼─────────────────────────────────────────────────┘
            │ HTTP/SSE
            ↓
┌───────────────────────┐
│   Kyros API           │
│   (localhost:8000)    │
└───────────────────────┘
```

---

## Code Structure

### Main Entry Point
```python
# kyros_terminal/main.py
from textual.app import App
from .ui.layout import KyrosLayout
from .orchestrator.client import OrchestratorClient

class KyrosTerminal(App):
    """Kyros Terminal Emulator with Orchestrator Integration."""
    
    BINDINGS = [
        ("ctrl+b", "broadcast", "Broadcast to Orchestrator"),
        ("ctrl+m", "toggle_monitor", "Toggle Monitor"),
        ("ctrl+l", "list_runs", "List Runs"),
        ("ctrl+h", "help", "Help"),
        ("ctrl+q", "quit", "Quit"),
    ]
    
    def compose(self):
        yield KyrosLayout()
    
    async def on_mount(self):
        # Initialize orchestrator client
        self.orchestrator = OrchestratorClient()
        await self.orchestrator.connect()
    
    async def action_broadcast(self):
        """Broadcast plan to orchestrator."""
        # Extract conversation
        conversation = self.query_one(TerminalWidget).get_history()
        
        # Show broadcast dialog
        await self.push_screen(BroadcastDialog(conversation))
    
    async def action_toggle_monitor(self):
        """Toggle orchestrator monitor pane."""
        monitor = self.query_one(MonitorWidget)
        monitor.visible = not monitor.visible

if __name__ == "__main__":
    KyrosTerminal().run()
```

### Terminal Widget
```python
# kyros_terminal/ui/terminal_widget.py
from textual.widget import Widget
from ptyprocess import PtyProcess
import pyte

class TerminalWidget(Widget):
    """Terminal emulator widget."""
    
    def __init__(self):
        super().__init__()
        self.screen = pyte.Screen(80, 24)
        self.stream = pyte.ByteStream(self.screen)
        self.process = None
        self.history = []
    
    async def on_mount(self):
        """Start PTY process."""
        self.process = PtyProcess.spawn(['/bin/bash'])
        self.set_interval(0.1, self.read_output)
    
    def read_output(self):
        """Read from PTY and update display."""
        try:
            data = self.process.read(1024)
            self.stream.feed(data)
            self.history.append(data.decode('utf-8', errors='ignore'))
            self.refresh()
        except:
            pass
    
    def render(self):
        """Render terminal screen."""
        lines = []
        for y in range(self.screen.lines):
            line = "".join(self.screen.buffer[y])
            lines.append(line)
        return "\n".join(lines)
    
    def on_key(self, event):
        """Handle keyboard input."""
        if self.process:
            self.process.write(event.character.encode())
    
    def get_history(self) -> list[str]:
        """Get conversation history."""
        return self.history[-100:]  # Last 100 lines
```

### Monitor Widget
```python
# kyros_terminal/ui/monitor_widget.py
from textual.widget import Widget
from textual.containers import Container
from rich.text import Text

class MonitorWidget(Widget):
    """Orchestrator monitor widget."""
    
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.current_run = None
        self.events = []
    
    async def watch_run(self, run_id: str):
        """Watch a run's events."""
        self.current_run = run_id
        self.events = []
        
        async for event in self.client.stream_events(run_id):
            self.events.append(event)
            self.refresh()
    
    def render(self):
        """Render monitor display."""
        if not self.current_run:
            return Text("No active run", style="dim")
        
        lines = [
            Text(f"Run: {self.current_run}", style="bold"),
            Text(""),
        ]
        
        for event in self.events[-20:]:  # Last 20 events
            ts = event.get("ts", "")[:8]  # HH:MM:SS
            type_ = event.get("type", "")
            msg = event.get("message", "")
            
            if type_ == "state":
                status = event.get("status", "")
                lines.append(Text(f"[{ts}] {status}", style="cyan"))
            elif type_ == "log":
                lines.append(Text(f"  └─ {msg}", style="dim"))
        
        return "\n".join(str(line) for line in lines)
```

---

## Configuration

### Config File: `~/.kyros/terminal.yaml`

```yaml
# API Configuration
api:
  url: http://localhost:8000
  token_file: ~/.kyros/token

# UI Configuration
ui:
  theme: dark
  monitor_position: right  # right, bottom, hidden
  monitor_width: 40        # percentage
  
# Terminal Configuration
terminal:
  shell: /bin/bash
  capture_output: true
  history_size: 10000

# AI Detection
ai:
  detect_aider: true
  detect_claude: true
  detect_codex: true
  
# Keyboard Shortcuts
shortcuts:
  broadcast: "ctrl+b"
  monitor: "ctrl+m"
  list_runs: "ctrl+l"
  help: "ctrl+h"
  quit: "ctrl+q"
```

---

## Example Workflows

### Workflow 1: Aider + Orchestrator

```bash
# 1. Start Kyros Terminal
$ kyros-terminal

# 2. Run aider inside
$ aider main.py

# 3. Chat with aider
> Add user authentication

# 4. Press Ctrl+B to broadcast plan
[Broadcast dialog appears]

# 5. Plan is sent to orchestrator
[Right pane shows real-time progress]

# 6. Continue working with aider
> Now add password reset
```

### Workflow 2: Claude CLI

```bash
# 1. Start Kyros Terminal
$ kyros-terminal

# 2. Run Claude CLI
$ claude

# 3. Discuss architecture
> Help me design a microservices architecture

# 4. Extract and broadcast
[Ctrl+B to broadcast]

# 5. Monitor in right pane while continuing chat
```

---

## Installation

```bash
# Install from PyPI (future)
pip install kyros-terminal

# Or install from source
cd apps/terminal
pip install -e .

# Run
kyros-terminal
```

---

## Development Roadmap

### MVP (Phase 1-2): 5-7 hours
- [x] Basic terminal emulation
- [x] Split pane layout
- [x] Orchestrator integration
- [x] Keyboard shortcuts

**Result**: Working terminal that can run aider/claude and broadcast to orchestrator

### Full POC (Phase 3): 7-10 hours
- [x] Conversation capture
- [x] Plan extraction
- [x] History storage
- [x] Broadcast dialog

**Result**: Intelligent extraction of plans from AI conversations

### Production (Phase 4): 10-13 hours
- [x] Polish and themes
- [x] Configuration system
- [x] Multiple AI tool detection
- [x] Error handling
- [x] Tests

---

## Success Criteria

### MVP
- [x] Can run shell commands
- [x] Can run aider/claude CLI tools
- [x] Can broadcast to orchestrator
- [x] Can see real-time events
- [x] Keyboard shortcuts work

### Full POC
- [x] Automatically detects AI responses
- [x] Extracts plans intelligently
- [x] Stores conversation history
- [x] Beautiful UI with themes

### Production
- [x] Stable and performant
- [x] Error recovery
- [x] Configuration options
- [x] Documentation
- [x] Tests

---

## Alternatives Considered

### 1. tmux Plugin
**Idea**: Create tmux plugin instead of full emulator  
**Pros**: Lightweight, works with existing tmux setup  
**Cons**: Requires tmux, limited UI control

### 2. VS Code Extension
**Idea**: Build as VS Code terminal integration  
**Pros**: Integrated with editor  
**Cons**: VS Code specific, harder to capture output

### 3. Shell Wrapper
**Idea**: Just wrap existing shells  
**Pros**: Simple, no terminal emulation  
**Cons**: Limited control, no split panes

**Decision**: Full terminal emulator gives best control and UX

---

## Next Steps

1. **Validate approach** - Is this the right direction?
2. **Choose tech stack** - Python+Textual vs Rust vs Electron
3. **Build MVP** - Phase 1-2 (5-7 hours)
4. **Test with real tools** - Try with aider, claude, etc.
5. **Iterate** - Add features based on usage

---

**Status**: 📋 Spec Complete  
**Recommended**: Start with Python+Textual MVP (5-7 hours)  
**Alternative**: Quick prototype with tmux integration (2-3 hours)
