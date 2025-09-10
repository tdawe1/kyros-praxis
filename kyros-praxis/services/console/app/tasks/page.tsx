'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { create } from 'zustand';
import { useEffect, useState } from 'react';

interface Task {
  id: string;
  title: string;
  status: string;
}

interface TasksStore {
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
}

const useTasksStore = create<TasksStore>((set) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
}));

export default function TasksPage() {
  const queryClient = useQueryClient();
  const { tasks, setTasks } = useTasksStore();
  const { data: tasksData } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const res = await fetch('/api/tasks');
      if (!res.ok) throw new Error('Failed to fetch tasks');
      return res.json();
    },
  });

  useEffect(() => {
    if (tasksData) {
      setTasks(tasksData);
    }
  }, [tasksData, setTasks]);

  const transitionMutation = useMutation({
    mutationFn: async ({ taskId, newStatus }: { taskId: string; newStatus: string }) => {
      const res = await fetch(`/api/tasks/${taskId}/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error('Failed to transition task');
      return res.json();
    },
    onMutate: async ({ taskId, newStatus }) => {
      await queryClient.cancelQueries({ queryKey: ['tasks'] });
      const previousTasks = tasks;
      setTasks(
        tasks.map((task: Task) =>
          task.id === taskId ? { ...task, status: newStatus } : task
        )
      );
      return { previousTasks };
    },
    onError: (err, variables, context) => {
      if (context?.previousTasks) {
        setTasks(context.previousTasks);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  const handleTransition = () => {
    if (selectedTaskId && selectedStatus) {
      transitionMutation.mutate({ taskId: selectedTaskId, newStatus: selectedStatus });
      setSelectedTaskId(null);
      setSelectedStatus('');
    }
  };

  if (tasks.length > 0) {
    return (
      <div className="kanban">
        <h1>Tasks</h1>
        <div className="kanban-board">
          <div className="kanban-column">
            <h2>Pending</h2>
            {tasks.filter((task: Task) => task.status === 'pending').map((task: Task) => (
              <div key={task.id}>
                <div>{task.title}</div>
                <select
                  value={selectedTaskId === task.id ? selectedStatus : task.status}
                  onChange={(e) => {
                    setSelectedTaskId(task.id);
                    setSelectedStatus(e.target.value);
                  }}
                >
                  <option value="pending">Pending</option>
                  <option value="in-progress">In Progress</option>
                  <option value="done">Done</option>
                </select>
                {selectedTaskId === task.id && (
                  <button onClick={handleTransition}>Transition</button>
                )}
              </div>
            ))}
          </div>
          <div className="kanban-column">
            <h2>In Progress</h2>
            {tasks.filter((task: Task) => task.status === 'in-progress').map((task: Task) => (
              <div key={task.id}>
                <div>{task.title}</div>
                <select
                  value={selectedTaskId === task.id ? selectedStatus : task.status}
                  onChange={(e) => {
                    setSelectedTaskId(task.id);
                    setSelectedStatus(e.target.value);
                  }}
                >
                  <option value="pending">Pending</option>
                  <option value="in-progress">In Progress</option>
                  <option value="done">Done</option>
                </select>
                {selectedTaskId === task.id && (
                  <button onClick={handleTransition}>Transition</button>
                )}
              </div>
            ))}
          </div>
          <div className="kanban-column">
            <h2>Done</h2>
            {tasks.filter((task: Task) => task.status === 'done').map((task: Task) => (
              <div key={task.id}>
                <div>{task.title}</div>
                <select
                  value={selectedTaskId === task.id ? selectedStatus : task.status}
                  onChange={(e) => {
                    setSelectedTaskId(task.id);
                    setSelectedStatus(e.target.value);
                  }}
                >
                  <option value="pending">Pending</option>
                  <option value="in-progress">In Progress</option>
                  <option value="done">Done</option>
                </select>
                {selectedTaskId === task.id && (
                  <button onClick={handleTransition}>Transition</button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return <div>Loading...</div>;
}