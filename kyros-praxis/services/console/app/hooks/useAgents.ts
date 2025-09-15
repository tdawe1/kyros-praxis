import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { agentApi } from '../lib/api/agents';
import { Agent, AgentFormData, AgentRun } from '../lib/schemas/agent';
import toast from 'react-hot-toast';

// Query keys
export const agentKeys = {
  all: ['agents'] as const,
  lists: () => [...agentKeys.all, 'list'] as const,
  list: (params?: any) => [...agentKeys.lists(), params] as const,
  details: () => [...agentKeys.all, 'detail'] as const,
  detail: (id: string) => [...agentKeys.details(), id] as const,
  runs: (agentId: string) => [...agentKeys.all, 'runs', agentId] as const,
  run: (agentId: string, runId: string) => [...agentKeys.runs(agentId), runId] as const,
};

// List agents hook
export function useAgents(params?: {
  status?: string;
  owner?: string;
  tags?: string[];
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}) {
  return useQuery({
    queryKey: agentKeys.list(params),
    queryFn: () => agentApi.list(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// Get single agent hook
export function useAgent(id: string) {
  return useQuery({
    queryKey: agentKeys.detail(id),
    queryFn: () => agentApi.get(id),
    enabled: !!id,
  });
}

// Create agent mutation
export function useCreateAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: AgentFormData) => agentApi.create(data),
    onSuccess: (newAgent) => {
      // Invalidate and refetch agent lists
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
      // Add the new agent to the cache
      queryClient.setQueryData(agentKeys.detail(newAgent.id), newAgent);
    },
    onError: (error: Error) => {
      toast.error(`Failed to create agent: ${error.message}`);
    },
  });
}

// Update agent mutation
export function useUpdateAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<AgentFormData> }) =>
      agentApi.update(id, data),
    onSuccess: (updatedAgent) => {
      // Update the agent in cache
      queryClient.setQueryData(agentKeys.detail(updatedAgent.id), updatedAgent);
      // Invalidate lists to ensure consistency
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(`Failed to update agent: ${error.message}`);
    },
  });
}

// Delete agent mutation
export function useDeleteAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => agentApi.delete(id),
    onSuccess: (_, deletedId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: agentKeys.detail(deletedId) });
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete agent: ${error.message}`);
    },
  });
}

// Bulk update mutation
export function useBulkUpdateAgents() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ ids, update }: { ids: string[]; update: { status?: string; tags?: string[] } }) =>
      agentApi.bulkUpdate(ids, update),
    onSuccess: (updatedAgents) => {
      // Update each agent in cache
      updatedAgents.forEach(agent => {
        queryClient.setQueryData(agentKeys.detail(agent.id), agent);
      });
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(`Failed to update agents: ${error.message}`);
    },
  });
}

// Bulk delete mutation
export function useBulkDeleteAgents() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (ids: string[]) => agentApi.bulkDelete(ids),
    onSuccess: (_, deletedIds) => {
      // Remove from cache
      deletedIds.forEach(id => {
        queryClient.removeQueries({ queryKey: agentKeys.detail(id) });
      });
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete agents: ${error.message}`);
    },
  });
}

// Run agent mutation
export function useRunAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input?: Record<string, any> }) =>
      agentApi.run(id, input),
    onSuccess: (run, { id }) => {
      // Invalidate runs list for this agent
      queryClient.invalidateQueries({ queryKey: agentKeys.runs(id) });
      // Update agent's lastRunAt
      queryClient.setQueryData<Agent>(agentKeys.detail(id), (old) => {
        if (old) {
          return { ...old, lastRunAt: new Date() };
        }
        return old;
      });
    },
    onError: (error: Error) => {
      toast.error(`Failed to run agent: ${error.message}`);
    },
  });
}

// Get agent runs hook
export function useAgentRuns(
  agentId: string,
  params?: {
    page?: number;
    pageSize?: number;
    status?: string;
  }
) {
  return useQuery({
    queryKey: agentKeys.runs(agentId),
    queryFn: () => agentApi.getRuns(agentId, params),
    enabled: !!agentId,
  });
}

// Get single run hook
export function useAgentRun(agentId: string, runId: string) {
  return useQuery({
    queryKey: agentKeys.run(agentId, runId),
    queryFn: () => agentApi.getRun(agentId, runId),
    enabled: !!agentId && !!runId,
    refetchInterval: (query) => {
      // Poll while running
      if ((query.state.data as any)?.status === 'running') {
        return 2000; // Poll every 2 seconds
      }
      return false;
    },
  });
}

// Clone agent mutation
export function useCloneAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      agentApi.clone(id, name),
    onSuccess: (newAgent) => {
      // Add to cache
      queryClient.setQueryData(agentKeys.detail(newAgent.id), newAgent);
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(`Failed to clone agent: ${error.message}`);
    },
  });
}

// Export agent mutation
export function useExportAgent() {
  return useMutation({
    mutationFn: (id: string) => agentApi.export(id),
    onSuccess: (blob, id) => {
      // Download the exported file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `agent-${id}-${new Date().toISOString()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Agent exported successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to export agent: ${error.message}`);
    },
  });
}

// Import agent mutation
export function useImportAgent() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (file: File) => agentApi.import(file),
    onSuccess: (newAgent) => {
      // Add to cache
      queryClient.setQueryData(agentKeys.detail(newAgent.id), newAgent);
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: agentKeys.lists() });
    },
    onError: (error: Error) => {
      toast.error(`Failed to import agent: ${error.message}`);
    },
  });
}

// Test connection mutation
export function useTestConnection() {
  return useMutation({
    mutationFn: (id: string) => agentApi.testConnection(id),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(result.message || 'Connection successful');
      } else {
        toast.error(result.message || 'Connection failed');
      }
    },
    onError: (error: Error) => {
      toast.error(`Connection test failed: ${error.message}`);
    },
  });
}