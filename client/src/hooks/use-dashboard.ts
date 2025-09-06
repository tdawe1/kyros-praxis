import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useDashboardStats() {
  return useQuery({
    queryKey: ['/api/dashboard/stats'],
    queryFn: api.getDashboardStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useRecentRuns() {
  return useQuery({
    queryKey: ['/api/runs/recent'],
    queryFn: api.getRecentRuns,
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

export function useAgents() {
  return useQuery({
    queryKey: ['/api/agents'],
    queryFn: api.getAgents,
    refetchInterval: 15000, // Refresh every 15 seconds
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: ['/api/system/health'],
    queryFn: api.getSystemHealth,
    refetchInterval: 20000, // Refresh every 20 seconds
  });
}

export function useOrchestratorHealth() {
  return useQuery({
    queryKey: ['/api/orchestrator/health'],
    queryFn: api.getOrchestratorHealth,
    refetchInterval: 30000,
  });
}
