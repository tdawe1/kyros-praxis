# Kyros Terminal Daemon Service

The Kyros Terminal Daemon is a WebSocket-based service that provides real-time terminal operations within the Kyros Praxis platform. It enables secure command execution and output streaming for AI agent workflows.

## 🏗️ Architecture

### Technology Stack
- **Node.js 18+** with TypeScript
- **WebSocket** for real-time communication
- **node-pty** for pseudo-terminal operations
- **Express.js** for HTTP endpoints
- **JWT** authentication integration
- **Session management** with persistence

### Core Responsibilities
- **Terminal Operations**: Command execution and output streaming
- **WebSocket Management**: Secure connection handling
- **Session Persistence**: Terminal session state management
- **Authentication Integration**: JWT token validation
- **Resource Management**: Process lifecycle and cleanup

## 🚀 Development Setup

### Prerequisites
- Node.js 18 or higher
- npm or yarn package manager
- TypeScript compiler

### Installation

1. **Navigate to service directory**:
   ```bash
   cd services/terminal-daemon
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Environment Configuration**:
   ```bash
   cp .env.example .env
   ```

4. **Configure environment variables**:
   ```bash
   # Required
   PORT=8787
   JWT_SECRET=your_very_secure_jwt_secret_minimum_32_chars
   ALLOWED_ORIGINS=http://localhost:3001
   ORCHESTRATOR_URL=http://localhost:8000
   
   # Optional
   LOG_LEVEL=info
   MAX_SESSIONS=100
   SESSION_TIMEOUT=3600
   ```

### Running the Service

**Development Mode**:
```bash
npm run dev
```

**Production Mode**:
```bash
npm run build
npm start
```

## 📁 Project Structure

```
services/terminal-daemon/
├── server.ts            # Main server entry point
├── websocket/
│   ├── handler.ts      # WebSocket connection handler
│   └── session.ts      # Terminal session management
├── terminal/
│   ├── manager.ts      # Terminal process manager
│   └── pty.ts          # PTY wrapper for node-pty
├── auth/
│   └── validator.ts    # JWT token validation
├── http/
│   └── routes.ts       # HTTP endpoint routes
├── utils/
│   ├── logger.ts       # Logging utilities
│   └── config.ts       # Configuration management
├── types/              # TypeScript type definitions
└── tests/              # Test suite
```

## 🔌 WebSocket Protocol

### Connection URL
- Development: `ws://localhost:8787`
- Production: `wss://your-domain.com:8787`

### Authentication
WebSocket connections require JWT authentication:

```javascript
const ws = new WebSocket('ws://localhost:8787', [], {
  headers: {
    'Authorization': 'Bearer your_jwt_token'
  }
});
```

### Message Format

#### Terminal Command
```json
{
  "type": "command",
  "id": "command-uuid",
  "session": "session-uuid",
  "command": "ls -la",
  "cwd": "/working/directory",
  "env": {
    "PATH": "/usr/local/bin:/usr/bin:/bin"
  }
}
```

#### Terminal Output
```json
{
  "type": "output",
  "id": "command-uuid",
  "session": "session-uuid",
  "data": "terminal output text",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Session Management
```json
{
  "type": "session",
  "action": "create",
  "id": "session-uuid",
  "config": {
    "shell": "/bin/bash",
    "cwd": "/working/directory",
    "env": {},
    "cols": 80,
    "rows": 24
  }
}
```

#### Error Messages
```json
{
  "type": "error",
  "id": "command-uuid",
  "session": "session-uuid",
  "error": "Error message",
  "code": "COMMAND_FAILED"
}
```

## 🔧 HTTP Endpoints

### Health Check
```
GET /health
```

**Response**:
```json
{
  "status": "running",
  "sessions": 5,
  "uptime": 3600,
  "version": "1.0.0"
}
```

### Session Info
```
GET /sessions
```

**Response**:
```json
{
  "sessions": [
    {
      "id": "session-uuid",
      "created_at": "2024-01-01T00:00:00Z",
      "last_activity": "2024-01-01T00:01:00Z",
      "status": "active"
    }
  ]
}
```

## 🔐 Security Features

### Authentication
- JWT token validation for all connections
- Token expiration checking
- User session management
- CORS protection

### Process Isolation
- Sandboxed terminal processes
- Resource limits (CPU, memory, file descriptors)
- Process cleanup on session termination
- Working directory restrictions

### Input Validation
- Command sanitization
- Path traversal prevention
- Environment variable filtering
- Command length limits

## 🔧 Development Commands

```bash
# Development server with hot reload
npm run dev

# TypeScript compilation
npm run build

# Production server
npm start

# Type checking
npm run type-check

# Linting
npm run lint

# Testing
npm test
npm run test:watch
npm run test:coverage
```

## 🧪 Testing

### Test Structure
```
tests/
├── unit/
│   ├── websocket.test.ts
│   ├── terminal.test.ts
│   └── auth.test.ts
├── integration/
│   ├── session.test.ts
│   └── commands.test.ts
└── e2e/
    └── workflow.test.ts
```

### Running Tests
```bash
# All tests
npm test

# Watch mode for development
npm run test:watch

# Coverage report
npm run test:coverage

# Specific test file
npm test -- websocket.test.ts
```

## 🚀 Deployment

### Environment Variables
Required for production:

```bash
# Server Configuration
PORT=8787
NODE_ENV=production

# Security
JWT_SECRET=your_production_secret
ALLOWED_ORIGINS=https://your-console-domain.com

# Resource Limits
MAX_SESSIONS=100
SESSION_TIMEOUT=3600
MAX_COMMAND_LENGTH=10000

# Logging
LOG_LEVEL=info
```

### Docker Deployment
```dockerfile
# Build image
docker build -t kyros-terminal-daemon .

# Run container
docker run -p 8787:8787 \
  -e JWT_SECRET=your_secret \
  -e NODE_ENV=production \
  kyros-terminal-daemon
```

### Docker Compose
```yaml
services:
  terminal-daemon:
    build: ./services/terminal-daemon
    ports:
      - "8787:8787"
    environment:
      - JWT_SECRET=your_secret
      - NODE_ENV=production
      - ALLOWED_ORIGINS=https://console.your-domain.com
    depends_on:
      - orchestrator
```

## 🔧 Troubleshooting

### Common Issues

**WebSocket Connection Issues**
```bash
# Check if service is running
curl http://localhost:8787/health

# Test WebSocket connection
wscat -c ws://localhost:8787 -H "Authorization: Bearer your_token"
```

**Authentication Issues**
1. Verify JWT token is valid and not expired
2. Check `JWT_SECRET` matches orchestrator secret
3. Verify user has proper permissions
4. Check CORS settings

**Process Management Issues**
```bash
# Check running processes
ps aux | grep node-pty

# Check system resources
top
htop

# Check file descriptors
lsof -p <process_id>
```

**Session Cleanup Issues**
```bash
# Monitor session count
curl http://localhost:8787/sessions

# Force cleanup (development only)
npm run cleanup-sessions
```

### Debug Mode
Enable debug logging:

```bash
export LOG_LEVEL=debug
npm run dev
```

### Performance Monitoring
```bash
# Monitor WebSocket connections
netstat -an | grep :8787

# Monitor process count
pgrep -f node-pty | wc -l

# Monitor memory usage
ps -p <pid> -o rss
```

## 📊 Monitoring & Observability

### Health Metrics
- Active session count
- Connection success/failure rates
- Average session duration
- Command execution success rates

### Performance Metrics
- WebSocket message latency
- Terminal command execution time
- Memory usage per session
- CPU utilization

### Logging
- Structured JSON logging
- Connection lifecycle events
- Command execution logs
- Error tracking with stack traces

## 🛡️ Security Best Practices

### Production Security
1. Use strong, randomly generated JWT secrets
2. Implement proper CORS policies
3. Use HTTPS/WSS in production
4. Set appropriate resource limits
5. Monitor for suspicious activities

### Process Security
- Run processes with minimal privileges
- Implement chroot jails if possible
- Use read-only filesystems where possible
- Implement proper signal handling

### Network Security
- Firewall rules to restrict access
- Rate limiting on connections
- IP whitelisting for internal services
- Network segmentation

## 📚 Integration Examples

### JavaScript/Node.js Client
```javascript
class TerminalClient {
  constructor(url, token) {
    this.ws = new WebSocket(url, [], {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };
  }
  
  async executeCommand(command, cwd = null) {
    const sessionId = await this.createSession();
    const commandId = generateUUID();
    
    this.ws.send(JSON.stringify({
      type: 'command',
      id: commandId,
      session: sessionId,
      command,
      cwd
    }));
    
    return new Promise((resolve) => {
      this.outputBuffer[commandId] = [];
      this.resolveCallbacks[commandId] = resolve;
    });
  }
  
  handleMessage(message) {
    switch (message.type) {
      case 'output':
        this.handleOutput(message);
        break;
      case 'error':
        this.handleError(message);
        break;
    }
  }
}
```

### Python Client
```python
import asyncio
import websockets
import json

async def terminal_client():
    uri = "ws://localhost:8787"
    token = "your_jwt_token"
    
    async with websockets.connect(
        uri,
        extra_headers={"Authorization": f"Bearer {token}"}
    ) as websocket:
        
        # Create session
        await websocket.send(json.dumps({
            "type": "session",
            "action": "create",
            "id": "session-123"
        }))
        
        # Execute command
        await websocket.send(json.dumps({
            "type": "command",
            "id": "cmd-123",
            "session": "session-123",
            "command": "ls -la"
        }))
        
        # Receive output
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "output":
                print(data["data"])
```

## 🔗 Additional Resources

- [Node.js Documentation](https://nodejs.org/docs/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [node-pty Documentation](https://github.com/microsoft/node-pty)
- [JWT Documentation](https://jwt.io/)
- [Project Architecture](../../docs/architecture/overview.md)
- [API Documentation](../../docs/api/README.md)