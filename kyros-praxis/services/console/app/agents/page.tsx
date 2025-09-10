'use client';

import { useQuery } from '@tanstack/react-query';
import { create } from 'zustand';

interface Agent {
  id: string;
  name: string;
  role: string;
  skills: string[];
  status: 'active' | 'inactive';
}

interface AgentState {
  agents: Agent[];
  toggleStatus: (id: string, status: 'active' | 'inactive') => void;
}

const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  toggleStatus: (id: string, status: 'active' | 'inactive') => set((state) => ({
    agents: state.agents.map((agent) =>
      agent.id === id ? { ...agent, status } : agent
    ),
  })),
});

export default function AgentsPage() {
  const { data: agents = [], isLoading } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: async () => {
      const res = await fetch('/api/agents');
      if (!res.ok) throw new Error('Failed to fetch agents');
      return res.json();
    },
  });

  const toggleStatus = useAgentStore((state) => state.toggleStatus);

  if (isLoading) return <div data-testid="agents-loading">Loading agents...</div>;

  return (
    <div data-testid="agents-page">
      <h1>Agents</h1>
      <ul>
        {agents.map((agent) => (
          <li key={agent.id} data-testid={`agent-${agent.id}`}>
            <span>{agent.name}</span>
            <button onClick={() => toggleStatus(agent.id, agent.status === 'active' ? 'inactive' : 'active')}>
              Toggle Status: {agent.status}
            </button>
            <p>Role: {agent.role}</p>
            <ul>
              {agent.skills.map((skill, index) => (
                <li key={index}>{skill}</li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
}