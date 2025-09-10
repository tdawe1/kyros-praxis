"use client";

import { useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { create } from "zustand";

interface Agent {
  id: string;
  name: string;
  role: string;
  status: string;
  skills: string[];
  last_seen: string;
}

interface AgentState {
  agents: Agent[];
  setAgents: (agents: Agent[]) => void;
  updateAgent: (updatedAgent: Agent) => void;
}

const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  setAgents: (agents: Agent[]) => set({ agents }),
  updateAgent: (updatedAgent: Agent) =>
    set((state) => ({
      agents: state.agents.map((a) =>
        a.id === updatedAgent.id ? updatedAgent : a
      ),
    })),
}));

export default function AgentsPage() {
  const queryClient = useQueryClient();
  const setAgents = useAgentStore((state) => state.setAgents);
  const updateAgent = useAgentStore((state) => state.updateAgent);

  const { data: agentsData } = useQuery({
    queryKey: ["agents"],
    queryFn: async () => {
      const res = await fetch("/collab/state/agents");
      if (!res.ok) throw new Error("Failed to fetch agents");
      return res.json();
    },
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ id, to }: { id: string; to: string }) => {
      const res = await fetch(`/collab/agents/${id}/transition`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to }),
      });
      if (!res.ok) throw new Error("Failed to toggle agent availability");
      return res.json();
    },
    onSuccess: (updatedAgent) => {
      updateAgent(updatedAgent);
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    },
  });

  useEffect(() => {
    if (agentsData) {
      setAgents(agentsData);
    }
  }, [agentsData, setAgents]);

  if (agentsData && agentsData.length > 0) {
    return (
      <div className="agents">
        <h1>Agents</h1>
        <div className="agents-list">
          {agentsData.map((agent: Agent) => {
            const newStatus =
              agent.status === "available" ? "unavailable" : "available";
            return (
              <div key={agent.id} className="agent-item">
                <span>{agent.name}</span>
                <span>{agent.role}</span>
                <span>{agent.status}</span>
                <span>{agent.skills.join(", ")}</span>
                <span>{agent.last_seen}</span>
                <button
                  data-testid={`agent-toggle-${agent.id}`}
                  onClick={() =>
                    toggleMutation.mutate({ id: agent.id, to: newStatus })
                  }
                  disabled={toggleMutation.isPending}
                >
                  Toggle {newStatus}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return <div>Loading...</div>;
}
