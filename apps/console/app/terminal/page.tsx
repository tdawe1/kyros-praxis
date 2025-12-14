'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';

import { API_BASE } from '@/app/lib/api';
import { APIError, apiFetch } from '@/app/lib/api-client';
import { useAuth } from '../state/auth-context';
import { BroadcastModal } from './components/BroadcastModal';
import { Dashboard } from './components/Dashboard';
import { SplitPane } from './components/SplitPane';

// Import Terminal dynamically to avoid SSR issues with xterm.js
const Terminal = dynamic(
  () => import('./components/Terminal').then((mod) => ({ default: mod.Terminal })),
  { ssr: false, loading: () => <div style={{ padding: '20px', color: '#ccc' }}>Loading terminal...</div> }
);

export default function TerminalPage() {
  const { token } = useAuth();
  const [isBroadcastModalOpen, setIsBroadcastModalOpen] = useState(false);
  const [isDashboardVisible, setIsDashboardVisible] = useState(true);
  const [conversationBuffer, setConversationBuffer] = useState<string[]>([]);
  
  // Use ref to track current line without causing re-renders
  const currentLineRef = useRef('');

  // Handle terminal data input - optimized with ref to prevent re-creation
  const handleTerminalData = useCallback((data: string) => {
    // Update conversation buffer
    if (data === '\r') {
      // Enter pressed
      const line = currentLineRef.current;
      if (line.trim()) {
        setConversationBuffer((prev) => [...prev, line].slice(-500)); // Keep last 500 lines
        currentLineRef.current = '';
      }
    } else if (data === '\x7f') {
      // Backspace
      currentLineRef.current = currentLineRef.current.slice(0, -1);
    } else if (data >= ' ') {
      // Printable character
      currentLineRef.current = currentLineRef.current + data;
    }
  }, []); // No dependencies - stable callback

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+B: Broadcast
      if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        setIsBroadcastModalOpen(true);
      }

      // Ctrl+M: Toggle monitor
      if (e.ctrlKey && e.key === 'm') {
        e.preventDefault();
        setIsDashboardVisible((prev) => !prev);
      }

      // Ctrl+L: Clear terminal
      if (e.ctrlKey && e.key === 'l') {
        e.preventDefault();
        const bridge = (window as any).__terminal;
        if (bridge?.send) {
          bridge.send('\u000c'); // Ctrl+L clear screen
        }
        currentLineRef.current = '';
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Handle broadcast
  const handleBroadcast = useCallback(
    async (projectName: string, tasks: string[]) => {
      try {
        const project = await apiFetch<{ id: string; name: string }>('/projects', {
          method: 'POST',
          body: JSON.stringify({
            name: projectName,
            description: 'Created from terminal session',
          }),
        });

        await apiFetch('/batch/runs', {
          method: 'POST',
          body: JSON.stringify({
            project_id: project.id,
            tasks: tasks.map((title) => ({
              title,
              description: title,
              priority: 'P1',
            })),
          }),
        });

        // Show success message in terminal
        if ((window as any).__terminal) {
          (window as any).__terminal.writeln('');
          (window as any).__terminal.writeln('✓ Broadcast successful!');
          (window as any).__terminal.writeln(`  Project: ${project.name}`);
          (window as any).__terminal.writeln(`  Tasks: ${tasks.length}`);
          (window as any).__terminal.writeln('');
          (window as any).__terminal.writeln('Check the dashboard → for status updates');
        }
      } catch (err) {
        if ((window as any).__terminal) {
          (window as any).__terminal.writeln('');
          (window as any).__terminal.writeln(
            `✗ Broadcast failed: ${
              err instanceof APIError
                ? `${err.message}${
                    err.correlationId ? ` (Correlation ID: ${err.correlationId})` : ''
                  }`
                : err instanceof Error
                  ? err.message
                  : 'Unknown error'
            }`
          );
        }
        throw err;
      }
    },
    [token]
  );

  const terminalComponent = (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: '#252525',
          borderBottom: '1px solid #333',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#cccccc' }}>
            Kyros Terminal
          </h1>
          <p style={{ margin: '2px 0 0', fontSize: '11px', color: '#999' }}>
            Multi-Agent Orchestration Interface
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: '#999' }}>
          <kbd
            style={{
              padding: '4px 8px',
              backgroundColor: '#1e1e1e',
              border: '1px solid #333',
              borderRadius: '4px',
            }}
          >
            Ctrl+B
          </kbd>
          <span>Broadcast</span>
          <kbd
            style={{
              padding: '4px 8px',
              backgroundColor: '#1e1e1e',
              border: '1px solid #333',
              borderRadius: '4px',
            }}
          >
            Ctrl+M
          </kbd>
          <span>Toggle Monitor</span>
          <kbd
            style={{
              padding: '4px 8px',
              backgroundColor: '#1e1e1e',
              border: '1px solid #333',
              borderRadius: '4px',
            }}
          >
            Ctrl+L
          </kbd>
          <span>Clear</span>
        </div>
      </div>

      {/* Terminal */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <Terminal onData={handleTerminalData} />
      </div>
    </div>
  );

  const content = isDashboardVisible ? (
    <SplitPane
      left={terminalComponent}
      right={<Dashboard apiBase={API_BASE} token={token} />}
      defaultSplit={60}
    />
  ) : (
    terminalComponent
  );

  return (
    <>
      {content}

      <BroadcastModal
        isOpen={isBroadcastModalOpen}
        onClose={() => setIsBroadcastModalOpen(false)}
        conversationBuffer={conversationBuffer}
        onBroadcast={handleBroadcast}
      />
    </>
  );
}
