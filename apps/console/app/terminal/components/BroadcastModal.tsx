'use client';

import { useState, useEffect, useRef } from 'react';

export interface BroadcastModalProps {
  isOpen: boolean;
  onClose: () => void;
  conversationBuffer: string[];
  onBroadcast: (projectName: string, tasks: string[]) => Promise<void>;
}

export function BroadcastModal({
  isOpen,
  onClose,
  conversationBuffer,
  onBroadcast,
}: BroadcastModalProps) {
  const [projectName, setProjectName] = useState('');
  const [extractedTasks, setExtractedTasks] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Extract tasks from conversation
      const tasks = extractTasksFromConversation(conversationBuffer);
      setExtractedTasks(tasks);

      // Generate project name
      const name = generateProjectName();
      setProjectName(name);

      // Focus first input
      modalRef.current?.querySelector<HTMLInputElement>('input')?.focus();
    } else {
      setError(null);
    }
  }, [isOpen, conversationBuffer]);

  const extractTasksFromConversation = (buffer: string[]): string[] => {
    const tasks: string[] = [];
    const recentLines = buffer.slice(-50); // Last 50 lines

    for (const line of recentLines) {
      // Look for numbered lists
      const match = line.match(/^\s*(\d+)[.)]\s+(.+)$/);
      if (match) {
        tasks.push(match[2].trim());
      }

      // Look for bullet points
      const bulletMatch = line.match(/^\s*[-•]\s+(.+)$/);
      if (bulletMatch) {
        tasks.push(bulletMatch[1].trim());
      }

      // Look for "I will" or "We'll" statements
      if (line.match(/(I will|We'll|Let's|I'll|We will)/i)) {
        tasks.push(line.trim());
      }
    }

    return tasks.slice(0, 10); // Max 10 tasks
  };

  const generateProjectName = (): string => {
    const timestamp = new Date().toISOString().slice(0, 16).replace('T', ' ');
    return `Terminal Session - ${timestamp}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!projectName.trim()) {
      setError('Project name is required');
      return;
    }

    if (extractedTasks.length === 0) {
      setError('No tasks to broadcast. Add at least one task.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await onBroadcast(projectName, extractedTasks);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to broadcast');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  const addTask = () => {
    setExtractedTasks([...extractedTasks, '']);
  };

  const updateTask = (index: number, value: string) => {
    const newTasks = [...extractedTasks];
    newTasks[index] = value;
    setExtractedTasks(newTasks);
  };

  const removeTask = (index: number) => {
    setExtractedTasks(extractedTasks.filter((_, i) => i !== index));
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        ref={modalRef}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
        style={{
          backgroundColor: '#1e1e1e',
          border: '1px solid #333',
          borderRadius: '8px',
          padding: '24px',
          maxWidth: '600px',
          width: '90%',
          maxHeight: '80vh',
          overflow: 'auto',
          color: '#cccccc',
        }}
      >
        <h2 style={{ margin: '0 0 8px', fontSize: '20px', fontWeight: 600 }}>
          Broadcast to Orchestrator
        </h2>
        <p style={{ margin: '0 0 24px', fontSize: '14px', color: '#999' }}>
          Send tasks to multi-agent system for parallel execution
        </p>

        <form onSubmit={handleSubmit}>
          {/* Project Name */}
          <div style={{ marginBottom: '20px' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: 500,
              }}
            >
              Project Name
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                backgroundColor: '#252525',
                border: '1px solid #333',
                borderRadius: '4px',
                color: '#cccccc',
                fontSize: '14px',
              }}
              placeholder="My Project"
            />
          </div>

          {/* Extracted Tasks */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label style={{ fontSize: '14px', fontWeight: 500 }}>
                Tasks ({extractedTasks.length})
              </label>
              <button
                type="button"
                onClick={addTask}
                style={{
                  padding: '4px 12px',
                  backgroundColor: '#0066cc',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#fff',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                + Add Task
              </button>
            </div>

            {extractedTasks.length === 0 ? (
              <p style={{ fontSize: '12px', color: '#999', padding: '12px', backgroundColor: '#252525', borderRadius: '4px' }}>
                No tasks detected. Click &quot;Add Task&quot; to add manually.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {extractedTasks.map((task, index) => (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      gap: '8px',
                      alignItems: 'start',
                    }}
                  >
                    <span style={{ fontSize: '12px', color: '#999', paddingTop: '10px', minWidth: '20px' }}>
                      {index + 1}.
                    </span>
                    <input
                      type="text"
                      value={task}
                      onChange={(e) => updateTask(index, e.target.value)}
                      style={{
                        flex: 1,
                        padding: '8px 12px',
                        backgroundColor: '#252525',
                        border: '1px solid #333',
                        borderRadius: '4px',
                        color: '#cccccc',
                        fontSize: '13px',
                      }}
                      placeholder="Task description"
                    />
                    <button
                      type="button"
                      onClick={() => removeTask(index)}
                      style={{
                        padding: '8px 12px',
                        backgroundColor: '#333',
                        border: 'none',
                        borderRadius: '4px',
                        color: '#fff',
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Conversation Preview */}
          <details style={{ marginBottom: '20px' }}>
            <summary
              style={{
                fontSize: '14px',
                fontWeight: 500,
                cursor: 'pointer',
                padding: '8px',
                backgroundColor: '#252525',
                border: '1px solid #333',
                borderRadius: '4px',
              }}
            >
              View Conversation Buffer ({conversationBuffer.length} lines)
            </summary>
            <pre
              style={{
                marginTop: '8px',
                padding: '12px',
                backgroundColor: '#252525',
                border: '1px solid #333',
                borderRadius: '4px',
                fontSize: '11px',
                maxHeight: '200px',
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
              }}
            >
              {conversationBuffer.slice(-30).join('\n')}
            </pre>
          </details>

          {/* Error */}
          {error && (
            <div
              style={{
                padding: '12px',
                backgroundColor: '#ef4444',
                border: '1px solid #dc2626',
                borderRadius: '4px',
                marginBottom: '20px',
                fontSize: '13px',
              }}
            >
              {error}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              style={{
                padding: '10px 20px',
                backgroundColor: '#333',
                border: 'none',
                borderRadius: '4px',
                color: '#cccccc',
                fontSize: '14px',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.5 : 1,
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || extractedTasks.length === 0}
              style={{
                padding: '10px 20px',
                backgroundColor: isLoading || extractedTasks.length === 0 ? '#555' : '#0066cc',
                border: 'none',
                borderRadius: '4px',
                color: '#fff',
                fontSize: '14px',
                cursor: isLoading || extractedTasks.length === 0 ? 'not-allowed' : 'pointer',
              }}
            >
              {isLoading ? 'Broadcasting...' : '🚀 Broadcast to Orchestrator'}
            </button>
          </div>
        </form>

        <p style={{ marginTop: '16px', fontSize: '11px', color: '#666', textAlign: 'center' }}>
          Press Esc to close • Tasks will be executed in parallel
        </p>
      </div>
    </div>
  );
}
