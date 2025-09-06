export interface DashboardStats {
  activeRuns: number;
  agentsOnline: number;
  successRate: number;
  avgDuration: string;
}

export interface RunWithAgent {
  id: string;
  mode: string;
  status: string;
  prRepo: string;
  prNumber: number;
  prBranch: string;
  notes?: string;
  duration?: number;
  startedAt: string;
  agentId?: string;
  agentName?: string;
}

export interface AgentWithStatus {
  id: string;
  name: string;
  model?: string;
  runner: string;
  status: string;
  queueCount: number;
}

export interface SystemHealthStatus {
  service: string;
  status: string;
  lastCheck: string;
  details?: string;
}

export interface TerminalSession {
  id: string;
  active: boolean;
  lastActivity: string;
}
