import { http, HttpResponse } from 'msw';

export const handlers = [
  // Mock for /collab/state/agents
  http.get('/collab/state/agents', () => {
    return HttpResponse.json({
      status: 'success',
      data: [
        { id: 'agent1', name: 'Agent 1', status: 'active' },
        { id: 'agent2', name: 'Agent 2', status: 'idle' },
      ],
    });
  }),
  // Mock for /collab/state/tasks
  http.get('/collab/state/tasks', () => {
    return HttpResponse.json({
      status: 'success',
      data: [
        { id: 'task1', title: 'Task 1', status: 'pending' },
        { id: 'task2', title: 'Task 2', status: 'in-progress' },
      ],
    });
  }),
];