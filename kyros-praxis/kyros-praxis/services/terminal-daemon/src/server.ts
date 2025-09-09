import express from 'express';
import { WebSocketServer } from 'ws';
import type { WebSocket } from 'ws';
import pty from 'node-pty';
import { CoordinateEvent, CoordinateEventSchema, validate } from '../../../packages/core/src/index';

const app = express();
const server = app.listen(8080, () => {
  console.log('Terminal Daemon listening on port 8080');
});

const wss = new WebSocketServer({ server });

interface TerminalSession {
  id: string;
  ws: WebSocket | null;
  ptyProcess: pty.IPty | null;
}

const sessions: TerminalSession[] = [];
const capabilities = ['bash', 'zsh', 'fish', 'cmd', 'powershell']; // Negotiable capabilities

wss.on('connection', (ws: WebSocket) => {
  console.log('New WebSocket connection');

  // Capability Negotiation
  ws.on('message', (message: string | Buffer) => {
    try {
      const data = JSON.parse(message.toString());
      const { type, capabilities: clientCaps, negotiate } = data;

      if (type === 'capability-negotiation') {
        // Validate using core schema
        const event = validate(CoordinateEventSchema, {
          event_type: 'capability-negotiate',
          agent_id: 'terminal-daemon',
          payload: { clientCaps, serverCaps: capabilities, negotiate },
          timestamp: Date.now()
        });

        // Negotiate capabilities (mock - agree on common)
        const agreedCaps = (clientCaps as string[]).filter(cap => capabilities.includes(cap));
        ws.send(JSON.stringify({
          event_type: 'capability-negotiated',
          agent_id: 'terminal-daemon',
          payload: { agreedCaps, sessionId: `session-${Date.now()}` },
          timestamp: Date.now()
        }));

        // Create session
        const sessionId = `session-${Date.now()}`;
        const session: TerminalSession = {
          id: sessionId,
          ws,
          ptyProcess: null
        };
        sessions.push(session);

        console.log(`Capability negotiation complete for ${sessionId}`);
      } else if (type === 'pty-session') {
        const { command, args, env, sessionId } = data;
        const session = sessions.find(s => s.id === sessionId);
        if (session) {
          // Spawn PTY
          session.ptyProcess = pty.spawn(command || 'bash', args || [], {
            name: 'xterm-color',
            cols: 80,
            rows: 30,
            cwd: process.cwd(),
            env: { ...process.env, ...env }
          });

          session.ptyProcess.onData((data: string) => {
            ws.send(JSON.stringify({
              event_type: 'pty-output',
              agent_id: sessionId,
              payload: { data },
              timestamp: Date.now()
            }));
          });

          session.ptyProcess.onExit((code, signal) => {
            ws.send(JSON.stringify({
              event_type: 'pty-closed',
              agent_id: sessionId,
              payload: { code, signal },
              timestamp: Date.now()
            }));
          });

          console.log(`PTY session started for ${sessionId}: ${command} ${args.join(' ')}`);
        }
      } else if (type === 'pty-input') {
        const { sessionId, input } = data;
        const session = sessions.find(s => s.id === sessionId);
        if (session && session.ptyProcess) {
          session.ptyProcess.write(input);
        }
      } else if (type === 'close-session') {
        const { sessionId } = data;
        const sessionIndex = sessions.findIndex(s => s.id === sessionId);
        if (sessionIndex !== -1) {
          if (sessions[sessionIndex].ptyProcess) {
            sessions[sessionIndex].ptyProcess.kill();
          }
          sessions.splice(sessionIndex, 1);
          console.log(`Session closed: ${sessionId}`);
        }
      }
    } catch (error) {
      console.error('Invalid message:', error);
      ws.send(JSON.stringify({
        event_type: 'error',
        agent_id: 'terminal-daemon',
        payload: { message: 'Invalid request' },
        timestamp: Date.now()
      }));
    }
  });

  ws.on('close', () => {
    // Clean up session
    const sessionIndex = sessions.findIndex(s => s.ws === ws);
    if (sessionIndex !== -1) {
      if (sessions[sessionIndex].ptyProcess) {
        sessions[sessionIndex].ptyProcess.kill();
      }
      sessions.splice(sessionIndex, 1);
      console.log('WebSocket connection closed');
    }
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', capabilities });
});

// API for session management
app.post('/sessions', express.json(), (req, res) => {
  const { command, args, env } = req.body;
  const sessionId = `session-${Date.now()}`;
  // Spawn pty and return session ID
  const ptyProcess = pty.spawn(command || 'bash', args || [], {
    name: 'xterm-color',
    cols: 80,
    rows: 30,
    cwd: process.cwd(),
    env: { ...process.env, ...env }
  });

  const session: TerminalSession = {
    id: sessionId,
    ws: null, // Will be set on WS connection
    ptyProcess
  };
  sessions.push(session);

  res.json({ sessionId });
});

console.log('Terminal Daemon server ready');