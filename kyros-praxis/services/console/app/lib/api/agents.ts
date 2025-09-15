import { Agent, AgentRun, AgentFormData } from '../schemas/agent';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Generic fetch wrapper with error handling
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      credentials: 'include', // Include cookies for auth
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        message: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(error.message || `Request failed: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

// Agent API functions
export const agentApi = {
  // List agents with optional filters
  list: async (params?: {
    status?: string;
    owner?: string;
    tags?: string[];
    page?: number;
    pageSize?: number;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }): Promise<{ agents: Agent[]; total: number; page: number; pageSize: number }> => {
    const queryParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => queryParams.append(key, v));
          } else {
            queryParams.append(key, String(value));
          }
        }
      });
    }

    return fetchAPI(`/agents?${queryParams.toString()}`);
  },

  // Get single agent by ID
  get: async (id: string): Promise<Agent> => {
    return fetchAPI(`/agents/${id}`);
  },

  // Create new agent
  create: async (data: AgentFormData): Promise<Agent> => {
    const response = await fetchAPI<Agent>('/agents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    toast.success('Agent created successfully');
    return response;
  },

  // Update existing agent
  update: async (id: string, data: Partial<AgentFormData>): Promise<Agent> => {
    const response = await fetchAPI<Agent>(`/agents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    toast.success('Agent updated successfully');
    return response;
  },

  // Delete agent
  delete: async (id: string): Promise<void> => {
    await fetchAPI(`/agents/${id}`, {
      method: 'DELETE',
    });
    toast.success('Agent deleted successfully');
  },

  // Bulk operations
  bulkUpdate: async (
    ids: string[],
    update: { status?: string; tags?: string[] }
  ): Promise<Agent[]> => {
    const response = await fetchAPI<Agent[]>('/agents/bulk', {
      method: 'PATCH',
      body: JSON.stringify({ ids, update }),
    });
    toast.success(`${ids.length} agents updated`);
    return response;
  },

  bulkDelete: async (ids: string[]): Promise<void> => {
    await fetchAPI('/agents/bulk', {
      method: 'DELETE',
      body: JSON.stringify({ ids }),
    });
    toast.success(`${ids.length} agents deleted`);
  },

  // Run agent manually
  run: async (id: string, input?: Record<string, any>): Promise<AgentRun> => {
    const response = await fetchAPI<AgentRun>(`/agents/${id}/run`, {
      method: 'POST',
      body: JSON.stringify({ input }),
    });
    toast.success('Agent run started');
    return response;
  },

  // Get agent runs
  getRuns: async (
    agentId: string,
    params?: {
      page?: number;
      pageSize?: number;
      status?: string;
    }
  ): Promise<{ runs: AgentRun[]; total: number }> => {
    const queryParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }

    return fetchAPI(`/agents/${agentId}/runs?${queryParams.toString()}`);
  },

  // Get single run details
  getRun: async (agentId: string, runId: string): Promise<AgentRun> => {
    return fetchAPI(`/agents/${agentId}/runs/${runId}`);
  },

  // Stop running agent
  stop: async (agentId: string, runId: string): Promise<void> => {
    await fetchAPI(`/agents/${agentId}/runs/${runId}/stop`, {
      method: 'POST',
    });
    toast.success('Agent run stopped');
  },

  // Get agent logs (streaming)
  streamLogs: async (
    agentId: string,
    runId: string,
    onMessage: (log: any) => void
  ): Promise<() => void> => {
    const eventSource = new EventSource(
      `${API_BASE_URL}/agents/${agentId}/runs/${runId}/logs/stream`
    );

    eventSource.onmessage = (event) => {
      try {
        const log = JSON.parse(event.data);
        onMessage(log);
      } catch (error) {
        console.error('Error parsing log:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      eventSource.close();
    };

    // Return cleanup function
    return () => eventSource.close();
  },

  // Export agent configuration
  export: async (id: string): Promise<Blob> => {
    const response = await fetch(`${API_BASE_URL}/agents/${id}/export`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      throw new Error('Export failed');
    }
    
    return response.blob();
  },

  // Import agent configuration
  import: async (file: File): Promise<Agent> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/agents/import`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Import failed');
    }

    const agent = await response.json();
    toast.success('Agent imported successfully');
    return agent;
  },

  // Clone agent
  clone: async (id: string, name: string): Promise<Agent> => {
    const response = await fetchAPI<Agent>(`/agents/${id}/clone`, {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
    toast.success('Agent cloned successfully');
    return response;
  },

  // Test agent connection
  testConnection: async (id: string): Promise<{ success: boolean; message?: string }> => {
    return fetchAPI(`/agents/${id}/test-connection`, {
      method: 'POST',
    });
  },
};