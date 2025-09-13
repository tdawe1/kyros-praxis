import { http, HttpResponse } from 'msw';
import { Agent, AgentRun } from '../lib/schemas/agent';

// Mock data
const mockAgents: Agent[] = [
  {
    id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Customer Support Agent',
    description: 'Handles customer inquiries and provides support',
    status: 'active',
    model: 'gpt-4-turbo',
    customModel: undefined,
    temperature: 0.7,
    maxTokens: 4096,
    topP: 1,
    frequencyPenalty: 0,
    presencePenalty: 0,
    systemPrompt: 'You are a helpful customer support agent.',
    capabilities: [
      {
        id: 'cap-001',
        name: 'Email Handler',
        type: 'tool',
        description: 'Process and respond to customer emails',
        config: {},
        dependencies: [],
        version: '1.0.0',
        enabled: true,
      },
      {
        id: 'cap-002',
        name: 'Knowledge Base Search',
        type: 'knowledge',
        description: 'Search company knowledge base',
        config: {},
        dependencies: [],
        version: '1.0.0',
        enabled: true,
      },
    ],
    policies: [
      {
        id: 'pol-001',
        name: 'PII Protection',
        type: 'pii',
        description: 'Protect customer personal information',
        rules: [],
        enabled: true,
        priority: 1,
      },
    ],
    connectors: [],
    schedule: undefined,
    tags: ['support', 'customer-facing'],
    owner: 'john.doe@example.com',
    collaborators: ['jane.smith@example.com'],
    createdAt: new Date('2024-01-15'),
    updatedAt: new Date('2024-03-10'),
    lastRunAt: new Date('2024-03-10T14:30:00'),
    runCount: 156,
    successRate: 94.2,
    averageLatency: 2340,
    totalTokensUsed: 1250000,
    estimatedCost: 125.50,
    version: '1.2.0',
    parentId: undefined,
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440001',
    name: 'Data Analysis Agent',
    description: 'Analyzes data and generates reports',
    status: 'paused',
    model: 'claude-3-opus',
    customModel: undefined,
    temperature: 0.3,
    maxTokens: 8192,
    topP: 0.95,
    frequencyPenalty: 0,
    presencePenalty: 0,
    systemPrompt: 'You are a data analysis expert.',
    capabilities: [
      {
        id: 'cap-003',
        name: 'SQL Query',
        type: 'function',
        description: 'Execute SQL queries',
        config: { database: 'analytics' },
        dependencies: [],
        version: '2.0.0',
        enabled: true,
      },
    ],
    policies: [],
    connectors: [],
    schedule: {
      id: 'sch-001',
      type: 'cron',
      expression: '0 9 * * MON',
      timezone: 'UTC',
      enabled: true,
      nextRun: new Date('2024-03-18T09:00:00'),
      lastRun: new Date('2024-03-11T09:00:00'),
    },
    tags: ['analytics', 'reporting'],
    owner: 'alice.johnson@example.com',
    collaborators: [],
    createdAt: new Date('2024-02-01'),
    updatedAt: new Date('2024-03-08'),
    lastRunAt: new Date('2024-03-08T09:00:00'),
    runCount: 45,
    successRate: 88.9,
    averageLatency: 5670,
    totalTokensUsed: 890000,
    estimatedCost: 89.00,
    version: '2.1.0',
    parentId: undefined,
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440002',
    name: 'Content Generator',
    description: 'Creates marketing content and blog posts',
    status: 'error',
    model: 'gemini-pro',
    customModel: undefined,
    temperature: 0.9,
    maxTokens: 2048,
    topP: 1,
    frequencyPenalty: 0.5,
    presencePenalty: 0.5,
    systemPrompt: 'You are a creative content writer.',
    capabilities: [],
    policies: [
      {
        id: 'pol-002',
        name: 'Brand Guidelines',
        type: 'custom',
        description: 'Ensure content follows brand guidelines',
        rules: [],
        enabled: true,
        priority: 1,
      },
    ],
    connectors: [],
    schedule: undefined,
    tags: ['marketing', 'content'],
    owner: 'bob.wilson@example.com',
    collaborators: ['carol.davis@example.com', 'david.brown@example.com'],
    createdAt: new Date('2024-01-20'),
    updatedAt: new Date('2024-03-09'),
    lastRunAt: new Date('2024-03-09T16:45:00'),
    runCount: 234,
    successRate: 76.5,
    averageLatency: 3450,
    totalTokensUsed: 567000,
    estimatedCost: 56.70,
    version: '1.0.0',
    parentId: undefined,
  },
];

const mockRuns: AgentRun[] = [
  {
    id: 'run-001',
    agentId: '550e8400-e29b-41d4-a716-446655440000',
    status: 'completed',
    trigger: 'manual',
    startedAt: new Date('2024-03-10T14:30:00'),
    completedAt: new Date('2024-03-10T14:30:05'),
    duration: 5000,
    input: { query: 'How do I reset my password?' },
    output: { response: 'To reset your password, please visit...' },
    logs: [],
    error: undefined,
    metrics: {
      tokensUsed: 450,
      cost: 0.045,
      latency: 2340,
    },
  },
];

// API base URL
const API_BASE = 'http://localhost:8000/api/v1';

export const handlers = [
  // List agents
  http.get(`${API_BASE}/agents`, ({ request }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get('page')) || 1;
    const pageSize = Number(url.searchParams.get('pageSize')) || 20;
    const status = url.searchParams.get('status');
    
    let filteredAgents = [...mockAgents];
    
    if (status) {
      filteredAgents = filteredAgents.filter(agent => agent.status === status);
    }
    
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedAgents = filteredAgents.slice(startIndex, endIndex);
    
    return HttpResponse.json({
      agents: paginatedAgents,
      total: filteredAgents.length,
      page,
      pageSize,
    });
  }),

  // Get single agent
  http.get(`${API_BASE}/agents/:id`, ({ params }) => {
    const agent = mockAgents.find(a => a.id === params.id);
    
    if (!agent) {
      return new HttpResponse(null, { status: 404 });
    }
    
    return HttpResponse.json(agent);
  }),

  // Create agent
  http.post(`${API_BASE}/agents`, async ({ request }) => {
    const data = await request.json();
    const newAgent: Agent = {
      id: `agent-${Date.now()}`,
      ...data as any,
      status: 'pending',
      capabilities: [],
      policies: [],
      connectors: [],
      owner: 'current.user@example.com',
      collaborators: [],
      createdAt: new Date(),
      updatedAt: new Date(),
      runCount: 0,
      totalTokensUsed: 0,
      estimatedCost: 0,
      version: '1.0.0',
    };
    
    mockAgents.push(newAgent);
    return HttpResponse.json(newAgent, { status: 201 });
  }),

  // Update agent
  http.patch(`${API_BASE}/agents/:id`, async ({ params, request }) => {
    const agentIndex = mockAgents.findIndex(a => a.id === params.id);
    
    if (agentIndex === -1) {
      return new HttpResponse(null, { status: 404 });
    }
    
    const updates = await request.json();
    mockAgents[agentIndex] = {
      ...mockAgents[agentIndex],
      ...updates as any,
      updatedAt: new Date(),
    };
    
    return HttpResponse.json(mockAgents[agentIndex]);
  }),

  // Delete agent
  http.delete(`${API_BASE}/agents/:id`, ({ params }) => {
    const agentIndex = mockAgents.findIndex(a => a.id === params.id);
    
    if (agentIndex === -1) {
      return new HttpResponse(null, { status: 404 });
    }
    
    mockAgents.splice(agentIndex, 1);
    return new HttpResponse(null, { status: 204 });
  }),

  // Bulk update agents
  http.patch(`${API_BASE}/agents/bulk`, async ({ request }) => {
    const { ids, update } = await request.json() as any;
    
    const updatedAgents = mockAgents
      .filter(agent => ids.includes(agent.id))
      .map(agent => ({
        ...agent,
        ...update,
        updatedAt: new Date(),
      }));
    
    // Update in place
    updatedAgents.forEach(updated => {
      const index = mockAgents.findIndex(a => a.id === updated.id);
      if (index !== -1) {
        mockAgents[index] = updated;
      }
    });
    
    return HttpResponse.json(updatedAgents);
  }),

  // Bulk delete agents
  http.delete(`${API_BASE}/agents/bulk`, async ({ request }) => {
    const { ids } = await request.json() as any;
    
    ids.forEach((id: string) => {
      const index = mockAgents.findIndex(a => a.id === id);
      if (index !== -1) {
        mockAgents.splice(index, 1);
      }
    });
    
    return new HttpResponse(null, { status: 204 });
  }),

  // Run agent
  http.post(`${API_BASE}/agents/:id/run`, async ({ params, request }) => {
    const agent = mockAgents.find(a => a.id === params.id);
    
    if (!agent) {
      return new HttpResponse(null, { status: 404 });
    }
    
    const { input } = await request.json() as any;
    
    const newRun: AgentRun = {
      id: `run-${Date.now()}`,
      agentId: params.id as string,
      status: 'running',
      trigger: 'manual',
      startedAt: new Date(),
      input,
      logs: [],
    };
    
    mockRuns.push(newRun);
    
    // Update agent's lastRunAt
    const agentIndex = mockAgents.findIndex(a => a.id === params.id);
    if (agentIndex !== -1) {
      mockAgents[agentIndex].lastRunAt = new Date();
      mockAgents[agentIndex].runCount++;
    }
    
    return HttpResponse.json(newRun, { status: 201 });
  }),

  // Get agent runs
  http.get(`${API_BASE}/agents/:agentId/runs`, ({ params }) => {
    const agentRuns = mockRuns.filter(run => run.agentId === params.agentId);
    
    return HttpResponse.json({
      runs: agentRuns,
      total: agentRuns.length,
    });
  }),

  // Get single run
  http.get(`${API_BASE}/agents/:agentId/runs/:runId`, ({ params }) => {
    const run = mockRuns.find(r => 
      r.agentId === params.agentId && r.id === params.runId
    );
    
    if (!run) {
      return new HttpResponse(null, { status: 404 });
    }
    
    return HttpResponse.json(run);
  }),

  // Clone agent
  http.post(`${API_BASE}/agents/:id/clone`, async ({ params, request }) => {
    const agent = mockAgents.find(a => a.id === params.id);
    
    if (!agent) {
      return new HttpResponse(null, { status: 404 });
    }
    
    const { name } = await request.json() as any;
    
    const clonedAgent: Agent = {
      ...agent,
      id: `agent-${Date.now()}`,
      name,
      parentId: agent.id,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastRunAt: undefined,
      runCount: 0,
      successRate: undefined,
      totalTokensUsed: 0,
      estimatedCost: 0,
    };
    
    mockAgents.push(clonedAgent);
    return HttpResponse.json(clonedAgent, { status: 201 });
  }),

  // Test connection
  http.post(`${API_BASE}/agents/:id/test-connection`, ({ params }) => {
    const agent = mockAgents.find(a => a.id === params.id);
    
    if (!agent) {
      return new HttpResponse(null, { status: 404 });
    }
    
    // Simulate connection test
    const success = Math.random() > 0.2; // 80% success rate
    
    return HttpResponse.json({
      success,
      message: success 
        ? 'Connection successful' 
        : 'Failed to establish connection',
    });
  }),
];