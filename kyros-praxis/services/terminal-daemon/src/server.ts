import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import { WebSocketServer } from 'ws';
import type { WebSocket } from 'ws';
import pty from 'node-pty';
import { z } from 'zod';
import { createRemoteJWKSet, jwtVerify } from 'jose';
import { randomUUID } from 'crypto';

const PORT = Number(process.env.PORT || 8080);
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS || '*').split(',').map(s => s.trim());
const JWKS_URL = process.env.JWKS_URL || '';
const AUTH_ISSUER = process.env.AUTH_ISSUER || '';
const AUTH_AUDIENCE = process.env.AUTH_AUDIENCE || '';
const PTY_ALLOW = (process.env.PTY_ALLOW || 'bash,sh').split(',').map(s => s.trim()).filter(Boolean);
const IDLE_TIMEOUT_MS = Number(process.env.IDLE_TIMEOUT_MS || 5 * 60_000);

const app = express();
app.use(helmet());
app.use(cors({ origin: ALLOWED_ORIGINS[0] === '*' ? true : ALLOWED_ORIGINS, credentials: true }));
app.use(express.json({ limit: '256kb' }));
app.use(rateLimit({ windowMs: 60_000, max: 120 }));
app.use((req, res, next) => {
  const id = req.header('x-request-id') || randomUUID();
  res.setHeader('x-request-id', id);
  (req as any).requestId = id;
  next();
});

const server = app.listen(PORT, () => {
  console.log(JSON.stringify({ event: 'startup', service: 'terminal-daemon', port: PORT }));
});

const wss = new WebSocketServer({ server, path: '/ws' });

// JWT verification
const jwks = JWKS_URL ? createRemoteJWKSet(new URL(JWKS_URL)) : null;
async function verifyJwt(token: string) {
  if (!jwks) throw new Error('JWKS not configured');
  const { payload } = await jwtVerify(token, jwks, {
    issuer: AUTH_ISSUER || undefined,
    audience: AUTH_AUDIENCE || undefined,
  });
  return payload;
}

interface TerminalSession {
  id: string;
  ws: WebSocket | null;
  ptyProcess: pty.IPty | null;
  lastActivity: number;
}

const sessions: TerminalSession[] = [];
const capabilities = PTY_ALLOW; // Negotiable capabilities from allowlist

const CapabilityNegotiation = z.object({
  type: z.literal('capability-negotiation'),
  capabilities: z.array(z.string()),
  negotiate: z.boolean().optional(),
});

const PtySessionStart = z.object({
  type: z.literal('pty-session'),
  command: z.string(),
  args: z.array(z.string()).optional().default([]),
  env: z.record(z.string(), z.string()).optional().default({}),
  sessionId: z.string().optional(),
});

const PtyInput = z.object({
  type: z.literal('pty-input'),
  sessionId: z.string(),
  input: z.string(),
});

const CloseSession = z.object({
  type: z.literal('close-session'),
  sessionId: z.string(),
});

wss.on('connection', async (ws: WebSocket, req) => {
  try {
    const url = new URL(req.url || '', `http://${req.headers.host}`);
    const token = url.searchParams.get('token') || '';
    if (!token) {
      ws.close(1008, 'Missing token');
      return;
    }
    await verifyJwt(token);
  } catch (err) {
    console.error(JSON.stringify({ event: 'ws_auth_error', error: String(err) }));
    try { ws.close(1008, 'Unauthorized'); } catch {}
    return;
  }
  console.log(JSON.stringify({ event: 'ws_connection' }));

  // Capability Negotiation
  ws.on('message', (message: string | Buffer) => {
    try {
      const data = JSON.parse(message.toString());
      (ws as any).lastActivity = Date.now();
      if (CapabilityNegotiation.safeParse(data).success) {
        const parsed = CapabilityNegotiation.parse(data);
        const clientCaps = parsed.capabilities;
        const agreedCaps = (clientCaps as string[]).filter(cap => capabilities.includes(cap));
        const sessionId = `session-${Date.now()}`;
        const session: TerminalSession = { id: sessionId, ws, ptyProcess: null, lastActivity: Date.now() };
        sessions.push(session);
        ws.send(JSON.stringify({
          event_type: 'capability-negotiated',
          agent_id: 'terminal-daemon',
          payload: { agreedCaps, sessionId },
          timestamp: Date.now()
        }));
        return;
      }

      if (PtySessionStart.safeParse(data).success) {
        const { command, args, env, sessionId } = PtySessionStart.parse(data);
        if (!PTY_ALLOW.includes(command)) {
          ws.send(JSON.stringify({ event_type: 'error', payload: { message: 'Command not allowed' }, timestamp: Date.now() }));
          return;
        }
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
            if (ws.readyState === ws.OPEN) ws.send(JSON.stringify({
              event_type: 'pty-output',
              agent_id: sessionId,
              payload: { data },
              timestamp: Date.now()
            }));
          });

          session.ptyProcess.onExit((e: { exitCode: number; signal?: number }) => {
            if (ws.readyState === ws.OPEN) ws.send(JSON.stringify({
              event_type: 'pty-closed',
              agent_id: sessionId,
              payload: { code: e.exitCode, signal: e.signal },
              timestamp: Date.now()
            }));
          });

          console.log(JSON.stringify({ event: 'pty_start', sessionId, command, args }));
        }
        return;
      }

      if (PtyInput.safeParse(data).success) {
        const { sessionId, input } = PtyInput.parse(data);
        const session = sessions.find(s => s.id === sessionId);
        if (session && session.ptyProcess) {
          session.ptyProcess.write(input);
        }
        return;
      }

      if (CloseSession.safeParse(data).success) {
        const { sessionId } = CloseSession.parse(data);
        const sessionIndex = sessions.findIndex(s => s.id === sessionId);
        if (sessionIndex !== -1) {
          if (sessions[sessionIndex].ptyProcess) {
            sessions[sessionIndex].ptyProcess.kill();
          }
          sessions.splice(sessionIndex, 1);
          console.log(JSON.stringify({ event: 'session_closed', sessionId }));
        }
        return;
      }
    } catch (error) {
      console.error(JSON.stringify({ event: 'ws_message_error', error: String(error) }));
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
      console.log(JSON.stringify({ event: 'ws_closed' }));
    }
  });

  // Idle timeout enforcement
  const interval = setInterval(() => {
    const s = sessions.find(s => s.ws === ws);
    if (!s) return;
    if (Date.now() - s.lastActivity > IDLE_TIMEOUT_MS) {
      try { ws.close(1000, 'Idle timeout'); } catch {}
      clearInterval(interval);
    }
  }, 30_000);
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', capabilities });
});

// API for session management
app.post('/sessions', async (req, res) => {
  const auth = req.header('authorization') || '';
  try {
    const token = auth.toLowerCase().startsWith('bearer ')
      ? auth.split(' ', 2)[1]
      : '';
    await verifyJwt(token);
  } catch (e) {
    return res.status(401).json({ error: 'unauthorized' });
  }
  const { command, args, env } = req.body || {};
  if (!PTY_ALLOW.includes(command || '')) {
    return res.status(400).json({ error: 'command not allowed' });
  }
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
    ptyProcess,
    lastActivity: Date.now()
  };
  sessions.push(session);

  res.json({ sessionId });
});

console.log(JSON.stringify({ event: 'ready', service: 'terminal-daemon' }));
