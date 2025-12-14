# Kyros CLI Interface - Specification

**Date**: 2025-01-12  
**Status**: 📋 PLANNING

---

## Vision

A beautiful terminal interface for interacting with the Kyros Praxis CrewAI backend. Users can:
- Authenticate with the backend
- Chat with AI assistants to develop plans
- Broadcast plans to the orchestrator
- Monitor crew runs in real-time
- Manage sessions and history

---

## User Stories

### 1. Authentication
```bash
$ kyros login
Email: user@example.com
Password: ********
✓ Logged in successfully!
```

### 2. Interactive Chat
```bash
$ kyros chat

╭─ Kyros Praxis ─────────────────────────────────╮
│ AI Assistant: Codex                             │
│ Press Ctrl+C to exit, /help for commands       │
╰─────────────────────────────────────────────────╯

You: I want to build a todo app with auth

Codex: Great! Let me help you plan that. Here's what we'll need:
1. User authentication (register/login)
2. CRUD operations for todos
3. Database schema
4. API endpoints

Would you like me to create a detailed plan?

You: yes

Codex: [Generates detailed plan...]

✓ Plan created. Type /broadcast to send to orchestrator.

You: /broadcast

🚀 Broadcasting plan to orchestrator...
✓ Crew run created: run-abc123
📊 Monitoring progress...

[Event Stream]
⏳ queued
🏃 running
   └─ Starting CrewAI run
   └─ Processing with gpt-4o-mini
✅ succeeded
```

### 3. Monitor Runs
```bash
$ kyros monitor run-abc123

╭─ Crew Run: run-abc123 ──────────────────────────╮
│ Crew: spec_to_tasks                             │
│ Status: running                                 │
│ Started: 2 minutes ago                          │
╰─────────────────────────────────────────────────╯

Events:
[12:34:56] STATE    queued
[12:34:57] LOG      Provider: openrouter, model: gpt-4o-mini
[12:34:58] STATE    running
[12:35:05] STATE    succeeded

Result:
✓ 5 tasks generated
  P0: Design User Interface
  P0: Integrate Weather API
  P1: Implement Location Features
  ...
```

### 4. List Runs
```bash
$ kyros runs

╭─ Recent Crew Runs ──────────────────────────────╮
│ ID         Crew          Status      Created    │
├─────────────────────────────────────────────────┤
│ run-abc123 spec_to_tasks succeeded  2 mins ago │
│ run-def456 spec_to_tasks running    now        │
│ run-ghi789 spec_to_tasks failed     1 hour ago │
╰─────────────────────────────────────────────────╯
```

---

## Architecture

### Components

```
┌─────────────────┐
│   Kyros CLI     │  (Python CLI Application)
│                 │
│  ┌───────────┐  │
│  │ Auth      │  │  - Login/logout
│  │ Manager   │  │  - Token storage
│  └───────────┘  │
│                 │
│  ┌───────────┐  │
│  │ AI Chat   │  │  - OpenAI/Anthropic/etc APIs
│  │ Client    │  │  - Conversation history
│  └───────────┘  │  - Plan extraction
│                 │
│  ┌───────────┐  │
│  │ Orchestr. │  │  - Create crew runs
│  │ Client    │  │  - Stream events (SSE)
│  └───────────┘  │  - Status queries
│                 │
│  ┌───────────┐  │
│  │ TUI       │  │  - Rich/Textual UI
│  │ Renderer  │  │  - Progress bars, panels
│  └───────────┘  │  - Color formatting
└────────┬────────┘
         │ HTTP/HTTPS
         ↓
┌─────────────────┐
│ Kyros API       │
│ (port 8000)     │
│                 │
│ - /auth/*       │
│ - /crews/runs   │
└─────────────────┘
```

---

## Technical Stack

### Core
- **Language**: Python 3.13+
- **Framework**: Click or Typer (CLI framework)
- **TUI**: Rich (beautiful terminal output)
- **HTTP Client**: httpx (async HTTP with SSE support)
- **Config**: python-dotenv, pydantic-settings

### Optional/Advanced
- **Textual**: Full TUI framework (interactive UI)
- **prompt_toolkit**: Advanced input handling
- **SQLite**: Local session/history storage
- **keyring**: Secure token storage

---

## Commands

### Authentication
```bash
kyros login                    # Interactive login
kyros logout                   # Clear credentials
kyros whoami                   # Show current user
```

### AI Chat
```bash
kyros chat                     # Start interactive chat
kyros chat --model codex       # Choose AI model
kyros chat --system "You..."   # Custom system prompt
```

### Chat Commands (In-Chat)
```
/help          - Show available commands
/model <name>  - Switch AI model
/broadcast     - Send plan to orchestrator
/clear         - Clear conversation history
/save <file>   - Save conversation
/load <file>   - Load conversation
/exit          - Exit chat
```

### Orchestrator
```bash
kyros broadcast <plan>         # Send plan to orchestrator
kyros runs                     # List recent runs
kyros runs --mine              # List my runs only
kyros monitor <run-id>         # Watch run in real-time
kyros status <run-id>          # Get run status
kyros cancel <run-id>          # Cancel running job
kyros result <run-id>          # Show final result
```

### Configuration
```bash
kyros config set api.url http://localhost:8000
kyros config set ai.model gpt-4o-mini
kyros config list              # Show all config
```

---

## Configuration File

**Location**: `~/.kyros/config.yaml`

```yaml
# API Configuration
api:
  url: http://localhost:8000
  timeout: 30

# AI Configuration
ai:
  model: gpt-4o-mini
  provider: openrouter
  temperature: 0.7
  max_tokens: 2000

# Display Configuration
display:
  theme: dark
  colors: true
  timestamps: true
  verbose: false

# Authentication
auth:
  token_file: ~/.kyros/token
```

---

## Data Storage

### Token Storage
**File**: `~/.kyros/token`
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_at": "2025-01-13T12:00:00Z"
}
```

### Conversation History (Optional)
**File**: `~/.kyros/history/<session-id>.json`
```json
{
  "session_id": "sess-abc123",
  "model": "gpt-4o-mini",
  "created_at": "2025-01-12T12:00:00Z",
  "messages": [
    {
      "role": "user",
      "content": "I want to build a todo app",
      "timestamp": "2025-01-12T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Great! Let me help...",
      "timestamp": "2025-01-12T12:00:05Z"
    }
  ]
}
```

---

## Implementation Phases

### Phase 1: Core CLI (MVP)
**Time**: 2-3 hours

**Features**:
- ✅ Basic CLI structure (Click/Typer)
- ✅ Login command (authenticate, store token)
- ✅ Logout command
- ✅ Broadcast command (create crew run)
- ✅ Monitor command (stream events)
- ✅ Basic Rich formatting

**Commands**:
- `kyros login`
- `kyros logout`
- `kyros broadcast <file>`
- `kyros monitor <run-id>`

### Phase 2: AI Chat Integration
**Time**: 2-3 hours

**Features**:
- ✅ Interactive chat session
- ✅ OpenAI/Anthropic/OpenRouter integration
- ✅ Conversation history
- ✅ Plan extraction from chat
- ✅ In-chat commands (/broadcast, /help, etc.)

**Commands**:
- `kyros chat`
- `kyros chat --model <model>`

### Phase 3: Enhanced TUI
**Time**: 2-3 hours

**Features**:
- ✅ Beautiful panels and layouts
- ✅ Progress bars for runs
- ✅ Real-time event display
- ✅ Interactive run list
- ✅ Color themes

**Commands**:
- `kyros runs` (interactive list)
- `kyros monitor` (enhanced UI)

### Phase 4: Advanced Features
**Time**: 2-4 hours

**Features**:
- ✅ Multiple AI provider support
- ✅ Session management
- ✅ Conversation save/load
- ✅ Configuration management
- ✅ History search
- ✅ Autocomplete

---

## File Structure

```
apps/cli/
├── pyproject.toml              # Project config
├── requirements.txt            # Dependencies
├── README.md                   # CLI documentation
│
├── kyros/                      # Main package
│   ├── __init__.py
│   ├── __main__.py            # Entry point
│   ├── cli.py                 # Click/Typer commands
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── client.py          # Auth API client
│   │   └── token.py           # Token storage
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base.py            # AI provider interface
│   │   ├── openai.py          # OpenAI client
│   │   ├── anthropic.py       # Claude client
│   │   └── openrouter.py      # OpenRouter client
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── client.py          # Crew runs API
│   │   └── monitor.py         # SSE event streaming
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat interface
│   │   ├── monitor.py         # Run monitor UI
│   │   └── tables.py          # Run list tables
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py        # Configuration
│   │   └── paths.py           # File paths
│   │
│   └── models/
│       ├── __init__.py
│       ├── run.py             # Run models
│       └── message.py         # Chat models
│
└── tests/
    ├── test_auth.py
    ├── test_orchestrator.py
    └── test_ui.py
```

---

## Dependencies

```txt
# Core
click==8.1.7                   # CLI framework
rich==13.7.0                   # Beautiful terminal output
httpx==0.27.2                  # Async HTTP client
pydantic==2.11.7               # Data validation
pydantic-settings==2.5.2       # Configuration
python-dotenv==1.0.1           # Environment variables

# AI Providers
openai==1.54.0                 # OpenAI API
anthropic==0.39.0              # Claude API

# Optional
textual==0.47.0                # Full TUI framework
prompt-toolkit==3.0.43         # Advanced input
keyring==24.3.0                # Secure storage
sseclient-py==1.8.0            # SSE client
```

---

## Example Workflows

### Workflow 1: Quick Plan Broadcast
```bash
# 1. Login
$ kyros login
Email: dev@example.com
Password: ********
✓ Logged in as dev@example.com

# 2. Create plan file
$ cat > plan.txt << EOF
Build a simple todo app with:
- User authentication
- CRUD operations for todos
- SQLite database
- REST API
EOF

# 3. Broadcast to orchestrator
$ kyros broadcast plan.txt
🚀 Broadcasting plan to orchestrator...
✓ Crew run created: run-xyz789
📊 Status: queued

# 4. Monitor progress
$ kyros monitor run-xyz789
[Real-time event stream...]
✅ Run completed successfully!
```

### Workflow 2: Interactive Chat
```bash
$ kyros chat

╭─ Kyros Chat ─────────────────────────────────╮
│ Model: gpt-4o-mini                            │
│ Commands: /help /broadcast /exit             │
╰───────────────────────────────────────────────╯

You: I need to build a REST API for managing books

AI: I'll help you design a REST API for book management. Here's a comprehensive plan:

**Endpoints:**
1. POST /books - Create new book
2. GET /books - List all books
3. GET /books/{id} - Get specific book
4. PUT /books/{id} - Update book
5. DELETE /books/{id} - Delete book

**Database Schema:**
- id (UUID, primary key)
- title (string, required)
- author (string, required)
- isbn (string, unique)
- published_date (date)
- created_at (timestamp)

**Authentication:**
- JWT tokens for API access
- Role-based permissions

Would you like me to generate detailed tasks for this?

You: yes, and broadcast it

AI: Generating detailed tasks...

✓ Tasks generated:
  P0: Design database schema
  P0: Implement authentication
  P1: Create CRUD endpoints
  P1: Add input validation
  P2: Write tests

You: /broadcast

🚀 Broadcasting to orchestrator...
✓ Crew run created: run-abc123
📊 Monitoring...

[12:34:56] STATE queued
[12:34:58] STATE running
[12:35:05] STATE succeeded

✅ Run completed! 5 tasks generated.

You: /exit
```

### Workflow 3: Monitor Multiple Runs
```bash
$ kyros runs

╭─ Active Runs ────────────────────────────────╮
│ ID         Status   Crew          Started   │
├───────────────────────────────────────────────┤
│ run-abc123 running  spec_to_tasks now       │
│ run-def456 queued   spec_to_tasks 1m ago    │
╰───────────────────────────────────────────────╯

$ kyros monitor run-abc123
[Live streaming...]
```

---

## Security Considerations

### Token Storage
- Store JWT in `~/.kyros/token` with 0600 permissions
- Optional: Use system keyring for better security
- Auto-refresh tokens before expiry

### API Communication
- Support HTTPS only in production
- Validate SSL certificates
- Timeout configuration
- Retry logic with backoff

### Input Sanitization
- Sanitize user input before sending to AI
- Validate API responses
- Prevent prompt injection

---

## Testing Strategy

### Unit Tests
- Auth client (login, token storage)
- Orchestrator client (create run, stream events)
- AI client (send message, parse response)
- Config management

### Integration Tests
- Full login → broadcast → monitor flow
- Multiple AI providers
- Error handling
- Network failures

### Manual Tests
- Interactive chat experience
- Real-time event display
- Error messages
- Help documentation

---

## UI/UX Design

### Color Scheme
- **Success**: Green
- **Error**: Red
- **Warning**: Yellow
- **Info**: Blue
- **Progress**: Cyan
- **Prompt**: Magenta

### Components
- **Panels**: Bordered boxes for sections
- **Progress**: Spinners for loading, bars for progress
- **Tables**: Formatted run lists
- **Syntax**: Highlighted code blocks
- **Timestamps**: Relative time (2m ago, now)

### Interactive Elements
- **Prompts**: Email, password input
- **Confirmations**: Yes/No questions
- **Menus**: Select from options
- **Autocomplete**: Command/model suggestions

---

## Documentation

### User Documentation
- `README.md` - Overview and installation
- `QUICKSTART.md` - 5-minute guide
- `COMMANDS.md` - Command reference
- `CONFIG.md` - Configuration guide
- `EXAMPLES.md` - Example workflows

### Developer Documentation
- `ARCHITECTURE.md` - Technical design
- `CONTRIBUTING.md` - Development guide
- `API.md` - Internal API reference

---

## Future Enhancements

### Phase 5: Advanced AI Features
- Multi-model conversation (switch during chat)
- Context memory across sessions
- Custom AI personalities
- RAG integration (search docs)

### Phase 6: Team Collaboration
- Shared sessions
- Team run history
- Comment on runs
- @mention users

### Phase 7: Plugins
- Plugin system for extensions
- Custom commands
- AI provider plugins
- Custom renderers

---

## Success Criteria

### MVP (Phase 1)
- [x] Can authenticate
- [x] Can create crew run
- [x] Can monitor in real-time
- [x] Beautiful terminal output

### Full POC (Phase 2)
- [x] Can chat with AI
- [x] Can extract and broadcast plans
- [x] Conversation history
- [x] Multiple AI models

### Production Ready
- [x] Comprehensive error handling
- [x] Offline mode (cached data)
- [x] Performance optimized
- [x] Full test coverage
- [x] Complete documentation

---

## Timeline Estimate

| Phase | Features | Time | Total |
|-------|----------|------|-------|
| Phase 1 | Core CLI | 2-3h | 2-3h |
| Phase 2 | AI Chat | 2-3h | 4-6h |
| Phase 3 | Enhanced TUI | 2-3h | 6-9h |
| Phase 4 | Advanced | 2-4h | 8-13h |

**Minimum Viable**: 2-3 hours (Phase 1)  
**Full POC**: 4-6 hours (Phases 1-2)  
**Production**: 8-13 hours (All phases)

---

## Next Steps

1. **Review this spec** - Confirm vision alignment
2. **Choose starting phase** - MVP vs Full POC
3. **Set up CLI project** - Create structure
4. **Implement Phase 1** - Core commands
5. **Test & iterate** - Get feedback

---

**Status**: 📋 Spec Complete, Ready for Implementation  
**Recommended Start**: Phase 1 (Core CLI) - 2-3 hours
