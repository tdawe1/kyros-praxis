import { type User, type InsertUser, type Run, type InsertRun, type Agent, type InsertAgent, type SystemHealth, type InsertSystemHealth } from "@shared/schema";
import { randomUUID } from "crypto";
import type { DashboardStats, RunWithAgent, AgentWithStatus, SystemHealthStatus } from "@/types";
import { toRunWithAgent } from "../apps/console/lib/normalizeRuns";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Dashboard
  getDashboardStats(): Promise<DashboardStats>;
  
  // Runs
  getRecentRuns(limit?: number): Promise<RunWithAgent[]>;
  getAllRuns(): Promise<RunWithAgent[]>;
  createRun(run: InsertRun): Promise<Run>;
  
  // Agents
  getAgents(): Promise<AgentWithStatus[]>;
  
  // System Health
  getSystemHealth(): Promise<SystemHealthStatus[]>;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private runs: Map<string, Run>;
  private agents: Map<string, Agent>;
  private systemHealth: Map<string, SystemHealth>;

  constructor() {
    this.users = new Map();
    this.runs = new Map();
    this.agents = new Map();
    this.systemHealth = new Map();
    
    // Initialize with some default agents and health checks
    this.initializeDefaultData();
  }

  private initializeDefaultData() {
    // Default agents
    const defaultAgents: Agent[] = [
      {
        id: "planner",
        name: "Planner",
        runner: "sdk",
        model: "gpt-5-high",
        cmd: null,
        attachable: false,
        version: 1,
        status: "active",
        queueCount: 2,
      },
      {
        id: "impl-default",
        name: "Implementer (Default)",
        runner: "sdk",
        model: "gemini-2.5-pro",
        cmd: null,
        attachable: false,
        version: 1,
        status: "ready",
        queueCount: 0,
      },
      {
        id: "impl-deep",
        name: "Implementer (Deep)",
        runner: "sdk",
        model: "claude-4-sonnet",
        cmd: null,
        attachable: false,
        version: 1,
        status: "busy",
        queueCount: 1,
      },
      {
        id: "impl-claude-cli",
        name: "Claude Code CLI",
        runner: "cli",
        model: null,
        cmd: ["claude-code"],
        attachable: true,
        version: 1,
        status: "standby",
        queueCount: 0,
      },
    ];

    defaultAgents.forEach(agent => this.agents.set(agent.id, agent));

    // Default system health
    const defaultHealth: SystemHealth[] = [
      {
        id: "orchestrator",
        service: "Orchestrator",
        status: "healthy",
        lastCheck: new Date(),
        details: null,
      },
      {
        id: "console",
        service: "Console",
        status: "healthy",
        lastCheck: new Date(),
        details: null,
      },
      {
        id: "terminal-daemon",
        service: "Terminal Daemon",
        status: "healthy",
        lastCheck: new Date(),
        details: null,
      },
      {
        id: "event-bus",
        service: "Event Bus",
        status: "warning",
        lastCheck: new Date(),
        details: "High memory usage",
      },
    ];

    defaultHealth.forEach(health => this.systemHealth.set(health.id, health));

    // Add some sample runs
    const sampleRuns: Run[] = [
      {
        id: "run-abc123",
        mode: "plan",
        status: "completed",
        prRepo: "owner/repo",
        prNumber: 42,
        prBranch: "feature-branch",
        prHeadSha: "deadbeef123456",
        prHtmlUrl: "https://github.com/owner/repo/pull/42",
        labels: [],
        extra: {},
        notes: "owner/repo#42 (feature-branch) planner=gpt-5-high impl=gemini-2.5-pro",
        startedAt: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
        completedAt: new Date(Date.now() - 8000), // 8 seconds ago
        duration: 134, // 2m 14s
        agentId: "planner",
      },
      {
        id: "run-def456",
        mode: "implement",
        status: "running",
        prRepo: "backend/api",
        prNumber: 18,
        prBranch: "optimization",
        prHeadSha: "abcdef789012",
        prHtmlUrl: "https://github.com/backend/api/pull/18",
        labels: ["needs:deep-refactor"],
        extra: {},
        notes: "backend/api#18 (optimization) planner=gpt-5-high impl=claude-4-sonnet",
        startedAt: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
        completedAt: null,
        duration: null,
        agentId: "impl-deep",
      },
      {
        id: "run-ghi789",
        mode: "critic",
        status: "completed",
        prRepo: "frontend/ui",
        prNumber: 33,
        prBranch: "refactor",
        prHeadSha: "123456abcdef",
        prHtmlUrl: "https://github.com/frontend/ui/pull/33",
        labels: [],
        extra: {},
        notes: "frontend/ui#33 (refactor) planner=gpt-5-high impl=gemini-2.5-pro",
        startedAt: new Date(Date.now() - 12 * 60 * 1000), // 12 minutes ago
        completedAt: new Date(Date.now() - 10 * 60 * 1000 + 15000),
        duration: 105, // 1m 45s
        agentId: "planner",
      },
    ];

    sampleRuns.forEach(run => this.runs.set(run.id, run));
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  async getDashboardStats(): Promise<DashboardStats> {
    const runs = Array.from(this.runs.values());
    const agents = Array.from(this.agents.values());
    
    const activeRuns = runs.filter(run => run.status === 'running').length;
    const agentsOnline = agents.filter(agent => agent.status !== 'offline').length;
    
    const completedRuns = runs.filter(run => run.status === 'completed');
    const successRate = completedRuns.length > 0 ? 
      Math.round((completedRuns.length / (completedRuns.length + runs.filter(run => run.status === 'failed').length)) * 100) : 
      94.2;
    
    const durations = completedRuns.map(run => run.duration).filter(d => d !== null) as number[];
    const avgDurationSeconds = durations.length > 0 ? 
      Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : 
      144; // 2m 24s default
    
    const avgDuration = `${Math.floor(avgDurationSeconds / 60)}m ${avgDurationSeconds % 60}s`;
    
    return {
      activeRuns,
      agentsOnline,
      successRate,
      avgDuration,
    };
  }

  async getRecentRuns(limit = 10): Promise<RunWithAgent[]> {
    const runs = Array.from(this.runs.values())
      .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
      .slice(0, limit);
    
    return runs.map(run =>
      toRunWithAgent({
        id: run.id,
        mode: run.mode,
        status: run.status,
        prRepo: run.prRepo,
        prNumber: run.prNumber,
        prBranch: run.prBranch,
        prHeadSha: run.prHeadSha,
        prHtmlUrl: run.prHtmlUrl,
        labels: run.labels,
        extra: run.extra ?? {},
        notes: run.notes,
        startedAt: run.startedAt.toISOString(),
        completedAt: run.completedAt ? run.completedAt.toISOString() : null,
        duration: run.duration,
        agentId: run.agentId,
        agentName: run.agentId ? this.agents.get(run.agentId)?.name ?? null : null,
      })
    );
  }

  async getAllRuns(): Promise<RunWithAgent[]> {
    const runs = Array.from(this.runs.values())
      .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime());
    
    return runs.map(run =>
      toRunWithAgent({
        id: run.id,
        mode: run.mode,
        status: run.status,
        prRepo: run.prRepo,
        prNumber: run.prNumber,
        prBranch: run.prBranch,
        prHeadSha: run.prHeadSha,
        prHtmlUrl: run.prHtmlUrl,
        labels: run.labels,
        extra: run.extra ?? {},
        notes: run.notes,
        startedAt: run.startedAt.toISOString(),
        completedAt: run.completedAt ? run.completedAt.toISOString() : null,
        duration: run.duration,
        agentId: run.agentId,
        agentName: run.agentId ? this.agents.get(run.agentId)?.name ?? null : null,
      })
    );
  }

  async createRun(insertRun: InsertRun): Promise<Run> {
    const id = `run-${randomUUID().substring(0, 8)}`;
      const run: Run = {
        id,
        mode: insertRun.mode,
        status: insertRun.status,
        prRepo: insertRun.prRepo,
        prNumber: insertRun.prNumber,
        prBranch: insertRun.prBranch,
        prHeadSha: insertRun.prHeadSha,
        prHtmlUrl: insertRun.prHtmlUrl ?? null,
        labels: (insertRun.labels ?? []) as string[],
        extra: insertRun.extra ?? {},
        notes: insertRun.notes ?? null,
        startedAt: new Date(),
        completedAt: null,
        duration: null,
        agentId: null,
      };
    this.runs.set(id, run);
    return run;
  }

  async getAgents(): Promise<AgentWithStatus[]> {
    return Array.from(this.agents.values()).map(agent => ({
      id: agent.id,
      name: agent.name,
      model: agent.model ?? undefined,
      runner: agent.runner,
      status: agent.status,
      queueCount: agent.queueCount,
    }));
  }

  async getSystemHealth(): Promise<SystemHealthStatus[]> {
    return Array.from(this.systemHealth.values()).map(health => ({
      service: health.service,
      status: health.status,
      lastCheck: health.lastCheck.toISOString(),
      details: health.details ?? undefined,
    }));
  }
}

export const storage = new MemStorage();
