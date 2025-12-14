'use client';

import { useEffect, useRef, useState } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import { SearchAddon } from '@xterm/addon-search';
import '@xterm/xterm/css/xterm.css';

import { getWebSocketToken } from '@/app/lib/api-client';
import { TERMINAL_WS_URL, withTokenQuery } from '@/app/lib/api';

export interface TerminalProps {
  onData?: (data: string) => void;
  onResize?: (cols: number, rows: number) => void;
  className?: string;
}

const textDecoder = new TextDecoder();

/**
 * Terminal component with cookie-based authentication
 * 
 * Uses temporary WebSocket tokens for authentication since WebSockets
 * don't support httpOnly cookies in all scenarios.
 * 
 * Flow:
 * 1. Get temporary WS token from API (using httpOnly cookie)
 * 2. Connect to WebSocket with token in URL
 * 3. Token expires in 5 minutes (single session use)
 */
export function Terminal({ onData, onResize, className }: TerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pendingMessagesRef = useRef<string[]>([]);
  const termRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const onDataRef = useRef(onData);
  const onResizeRef = useRef(onResize);
  const isAuthenticatedRef = useRef(false);

  const [connectionStatus, setConnectionStatus] = useState<
    'connecting' | 'connected' | 'error' | 'getting_token'
  >('getting_token');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    onDataRef.current = onData;
    onResizeRef.current = onResize;
  }, [onData, onResize]);

  useEffect(() => {
    if (!terminalRef.current) {
      return;
    }

    const term = new XTerm({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: {
        background: '#0a0d13',
        foreground: '#e2e8f0',
        cursor: '#7ddfff',
        cursorAccent: '#020305',
        selectionBackground: 'rgba(125, 223, 255, 0.25)',
      },
      allowProposedApi: true,
      scrollback: 10000,
      fastScrollModifier: 'shift',
    });

    termRef.current = term;

    const fitAddon = new FitAddon();
    fitAddonRef.current = fitAddon;
    const webLinksAddon = new WebLinksAddon();
    const searchAddon = new SearchAddon();

    term.loadAddon(fitAddon);
    term.loadAddon(webLinksAddon);
    term.loadAddon(searchAddon);

    term.open(terminalRef.current);

    setTimeout(() => {
      try {
        fitAddon.fit();
        term.focus();
      } catch (err) {
        console.error('Failed to fit terminal on mount', err);
      }
    }, 0);

    pendingMessagesRef.current = [];

    // Get WebSocket token and connect
    const connectTerminal = async () => {
      try {
        setConnectionStatus('getting_token');
        term.writeln('🔑 Getting WebSocket token...');

        // Get temporary WS token (5-minute expiry)
        const wsToken = await getWebSocketToken();

        term.writeln('🔗 Connecting to terminal...');
        setConnectionStatus('connecting');

        // Connect with token in URL
        const wsUrl = withTokenQuery(TERMINAL_WS_URL, wsToken);
        const ws = new WebSocket(wsUrl);
        ws.binaryType = 'arraybuffer';
        wsRef.current = ws;

        const sendMessage = (payload: string) => {
          if (ws && ws.readyState === WebSocket.OPEN && isAuthenticatedRef.current) {
            ws.send(payload);
          } else {
            pendingMessagesRef.current.push(payload);
          }
        };

        const flushPending = () => {
          if (!ws || ws.readyState !== WebSocket.OPEN || !isAuthenticatedRef.current) {
            return;
          }
          while (pendingMessagesRef.current.length > 0) {
            const value = pendingMessagesRef.current.shift();
            if (value !== undefined) {
              ws.send(value);
            }
          }
        };

        ws.onopen = () => {
          isAuthenticatedRef.current = true;
          setConnectionStatus('connected');
          term.writeln('✅ Connected\n');
          flushPending();
        };

        ws.onmessage = (event) => {
          if (typeof event.data === 'string') {
            try {
              const message = JSON.parse(event.data);

              if (message?.type === 'auth_success') {
                isAuthenticatedRef.current = true;
                setConnectionStatus('connected');
                term.writeln(`✅ Authenticated as ${message.user?.username || 'operator'}\n`);
                flushPending();
                return;
              }

              if (message?.type === 'error') {
                term.writeln(`❌ ${message.message ?? 'Authentication error'}\n`);
                setConnectionStatus('error');
                setErrorMessage(message.message || 'Authentication error');
                return;
              }
            } catch {
              // fall through to write as text
            }
            term.write(event.data);
            return;
          }

          if (event.data instanceof ArrayBuffer) {
            term.write(textDecoder.decode(event.data));
            return;
          }

          if (event.data instanceof Blob) {
            event.data
              .arrayBuffer()
              .then((buffer) => term.write(textDecoder.decode(buffer)))
              .catch((err) => console.error('Failed to decode terminal blob payload', err));
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionStatus('error');
          setErrorMessage('WebSocket connection error');
          term.writeln('\r\n❌ Connection error\r\n');
        };

        ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          isAuthenticatedRef.current = false;
          setConnectionStatus('error');

          if (event.code === 1000) {
            term.writeln('\r\n✅ Connection closed normally\r\n');
          } else {
            term.writeln(`\r\n❌ Connection closed (code ${event.code})\r\n`);
            if (event.reason) {
              term.writeln(`Reason: ${event.reason}\r\n`);
            }
          }
        };

        // Handle terminal input
        const onDataDisposable = term.onData((data) => {
          sendMessage(data);
          onDataRef.current?.(data);
        });

        // Handle terminal resize
        const onResizeDisposable = term.onResize(({ cols, rows }) => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'resize', cols, rows }));
          }
          onResizeRef.current?.(cols, rows);
        });

        // Cleanup
        return () => {
          onDataDisposable.dispose();
          onResizeDisposable.dispose();
          if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
            ws.close();
          }
          term.dispose();
        };
      } catch (error) {
        console.error('Failed to connect to terminal:', error);
        setConnectionStatus('error');
        setErrorMessage(error instanceof Error ? error.message : 'Failed to connect');
        term.writeln('❌ Error: Failed to get WebSocket token.');
        term.writeln('Please ensure you are logged in.');

        return () => {
          term.dispose();
        };
      }
    };

    const cleanup = connectTerminal();

    return () => {
      cleanup.then((fn) => fn?.());
    };
  }, []);

  // Status indicator
  const statusColors = {
    getting_token: 'bg-yellow-500',
    connecting: 'bg-yellow-500',
    connected: 'bg-green-500',
    error: 'bg-red-500',
  };

  const statusLabels = {
    getting_token: 'Getting token...',
    connecting: 'Connecting...',
    connected: 'Connected',
    error: 'Error',
  };

  return (
    <div className={`relative flex flex-col h-full ${className || ''}`}>
      {/* Status indicator */}
      <div className="absolute top-2 right-2 z-10 flex items-center gap-2 bg-gray-900/80 backdrop-blur px-3 py-1 rounded-full text-sm">
        <div className={`w-2 h-2 rounded-full ${statusColors[connectionStatus]}`} />
        <span className="text-gray-300">{statusLabels[connectionStatus]}</span>
      </div>

      {/* Error message */}
      {errorMessage && (
        <div className="absolute top-12 right-2 z-10 max-w-md bg-red-900/90 backdrop-blur px-4 py-2 rounded text-sm text-red-100">
          {errorMessage}
        </div>
      )}

      {/* Terminal */}
      <div ref={terminalRef} className="flex-1 p-2" />
    </div>
  );
}
