import { apiRequest } from "./queryClient";
import type { DashboardStats, RunWithAgent, AgentWithStatus, SystemHealthStatus } from "@/types";

export const api = {
  // Dashboard data
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await fetch('/api/dashboard/stats');
    return response.json();
  },

  // Runs
  getRecentRuns: async (): Promise<RunWithAgent[]> => {
    const response = await fetch('/api/runs/recent');
    return response.json();
  },

  createRun: async (data: {
    pr: {
      repo: string;
      pr_number: number;
      branch: string;
      head_sha: string;
      html_url?: string;
    };
    mode: string;
    labels: string[];
    extra: Record<string, any>;
  }) => {
    return apiRequest('POST', '/api/runs', data);
  },

  // Agents
  getAgents: async (): Promise<AgentWithStatus[]> => {
    const response = await fetch('/api/agents');
    return response.json();
  },

  // System Health
  getSystemHealth: async (): Promise<SystemHealthStatus[]> => {
    const response = await fetch('/api/system/health');
    return response.json();
  },

  // Orchestrator proxy
  getOrchestratorConfig: async () => {
    const response = await fetch('/api/orchestrator/config');
    return response.json();
  },

  getOrchestratorHealth: async () => {
    const response = await fetch('/api/orchestrator/health');
    return response.json();
  },
};
