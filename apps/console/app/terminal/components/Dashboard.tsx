'use client';

import { useEffect, useState } from 'react';

import { ACCESS_TOKEN_STORAGE_KEY, withTokenQuery } from '@/app/lib/api';
import { APIError, apiFetch } from '@/app/lib/api-client';

interface Project {
  id: string;
  name: string;
  status: string;
  created_at: string;
}

interface Task {
  id: string;
  title: string;
  status: string;
  priority: string;
}

interface DashboardData {
  projects: Project[];
  activeTasks: Task[];
  recentEvents: any[];
}

interface DashboardProps {
  apiBase: string;
  token?: string | null;
}

export function Dashboard({ apiBase, token }: DashboardProps) {
  const [data, setData] = useState<DashboardData>({
    projects: [],
    activeTasks: [],
    recentEvents: [],
  });
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch projects
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const projects = await apiFetch<Project[]>('/projects');
        setData((prev) => ({ ...prev, projects }));
        setLoading(false);

        // Auto-select first project
        if (projects.length > 0 && !selectedProject) {
          setSelectedProject(projects[0].id);
        }
      } catch (err) {
        setError(
          err instanceof APIError
            ? `${err.message}${err.correlationId ? ` (Correlation ID: ${err.correlationId})` : ''}`
            : err instanceof Error
              ? err.message
              : 'Failed to load projects',
        );
        setLoading(false);
      }
    };

    fetchProjects();
    const interval = setInterval(fetchProjects, 5000); // Refresh every 5s

    return () => clearInterval(interval);
  }, [apiBase, token, selectedProject]);

  // Fetch tasks for selected project
  useEffect(() => {
    if (!selectedProject) return;

    const fetchTasks = async () => {
      try {
        const tasks = await apiFetch<Task[]>(`/projects/${selectedProject}/tasks`);
        setData((prev) => ({ ...prev, activeTasks: tasks }));
      } catch (err) {
        console.error('Failed to fetch tasks:', err);
      }
    };

    fetchTasks();
    const interval = setInterval(fetchTasks, 3000); // Refresh every 3s

    return () => clearInterval(interval);
  }, [apiBase, token, selectedProject]);

  // Subscribe to events for selected project
  useEffect(() => {
    if (!selectedProject) return;

    const storedToken = (() => {
      if (typeof window === 'undefined') {
        return token ?? null;
      }
      try {
        return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) ?? token ?? null;
      } catch {
        return token ?? null;
      }
    })();

    const eventUrl = storedToken
      ? withTokenQuery(`${apiBase}/memory/${selectedProject}/events`, storedToken)
      : `${apiBase}/memory/${selectedProject}/events`;

    const eventSource = new EventSource(eventUrl);

    eventSource.onmessage = (event) => {
      try {
        const eventData = JSON.parse(event.data);
        setData((prev) => ({
          ...prev,
          recentEvents: [eventData, ...prev.recentEvents].slice(0, 10),
        }));
      } catch (err) {
        console.error('Failed to parse event:', err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [apiBase, token, selectedProject]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'succeeded':
        return '#10b981';
      case 'running':
      case 'executing':
        return '#3b82f6';
      case 'failed':
        return '#ef4444';
      case 'queued':
      case 'planning':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '20px', color: '#ccc' }}>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: '#ef4444' }}>
        <p>Error: {error}</p>
      </div>
    );
  }

  return (
    <div
      style={{
        height: '100%',
        backgroundColor: '#1e1e1e',
        color: '#cccccc',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid #333',
          backgroundColor: '#252525',
        }}
      >
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>
          Agent Dashboard
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#999' }}>
          Multi-Agent Orchestration Status
        </p>
      </div>

      {/* Projects */}
      <div style={{ padding: '16px', borderBottom: '1px solid #333' }}>
        <h3 style={{ margin: '0 0 12px', fontSize: '14px', fontWeight: 600 }}>
          Projects ({data.projects.length})
        </h3>
        {data.projects.length === 0 ? (
          <p style={{ fontSize: '12px', color: '#999' }}>
            No projects yet. Create one via API or press Ctrl+B.
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {data.projects.map((project) => (
              <div
                key={project.id}
                onClick={() => setSelectedProject(project.id)}
                style={{
                  padding: '12px',
                  backgroundColor:
                    selectedProject === project.id ? '#333' : '#252525',
                  border: '1px solid #333',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontSize: '13px', fontWeight: 500 }}>
                    {project.name}
                  </span>
                  <span
                    style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      backgroundColor: getStatusColor(project.status),
                      color: '#fff',
                    }}
                  >
                    {project.status}
                  </span>
                </div>
                <p style={{ margin: '4px 0 0', fontSize: '11px', color: '#999' }}>
                  {new Date(project.created_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Active Tasks */}
      {selectedProject && (
        <div style={{ padding: '16px', borderBottom: '1px solid #333', flex: 1, overflow: 'auto' }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '14px', fontWeight: 600 }}>
            Active Tasks ({data.activeTasks.length})
          </h3>
          {data.activeTasks.length === 0 ? (
            <p style={{ fontSize: '12px', color: '#999' }}>
              No tasks yet. Broadcast a plan to create tasks.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {data.activeTasks.map((task) => (
                <div
                  key={task.id}
                  style={{
                    padding: '12px',
                    backgroundColor: '#252525',
                    border: '1px solid #333',
                    borderRadius: '4px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'start',
                      gap: '8px',
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '13px', fontWeight: 500, marginBottom: '4px' }}>
                        {task.title}
                      </div>
                      <div style={{ fontSize: '11px', color: '#999' }}>
                        Priority: {task.priority}
                      </div>
                    </div>
                    <span
                      style={{
                        fontSize: '11px',
                        padding: '2px 8px',
                        borderRadius: '10px',
                        backgroundColor: getStatusColor(task.status),
                        color: '#fff',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {task.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Recent Events */}
      <div style={{ padding: '16px', maxHeight: '200px', overflow: 'auto' }}>
        <h3 style={{ margin: '0 0 12px', fontSize: '14px', fontWeight: 600 }}>
          Recent Events ({data.recentEvents.length})
        </h3>
        {data.recentEvents.length === 0 ? (
          <p style={{ fontSize: '12px', color: '#999' }}>No events yet</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {data.recentEvents.map((event, idx) => (
              <div
                key={idx}
                style={{
                  padding: '8px',
                  backgroundColor: '#252525',
                  border: '1px solid #333',
                  borderRadius: '4px',
                  fontSize: '11px',
                }}
              >
                <div style={{ color: '#3b82f6', fontWeight: 500 }}>
                  {event.event_type}
                </div>
                {event.payload && (
                  <div style={{ marginTop: '4px', color: '#999' }}>
                    {JSON.stringify(event.payload).slice(0, 80)}...
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
