import { create } from 'zustand';

interface Agent {
  id: string;
  role: string;
  status: string;
  last_seen: string;
}

interface Task {
  id: string;
  title: string;
  status: string;
}

interface Lease {
  id: string;
  resource: string;
  holder: string;
  ttl_seconds: number;
}

interface Event {
  id: string;
  type: string;
  ts: string;
}

interface Job {
  id: string;
  status: string;
}

interface Schedule {
  id: string;
  cron: string;
}

interface Preset {
  id: string;
  name: string;
}

export const useAgentsStore = create((set) => ({
  agents: [] as Agent[],
  setAgents: (agents: Agent[]) => set({ agents }),
}));

export const useTasksStore = create((set) => ({
  tasks: [] as Task[],
  setTasks: (tasks: Task[]) => set({ tasks }),
}));

export const useLeasesStore = create((set) => ({
  leases: [] as Lease[],
  setLeases: (leases: Lease[]) => set({ leases }),
}));

export const useEventsStore = create((set) => ({
  events: [] as Event[],
  setEvents: (events: Event[]) => set({ events }),
}));

export const useJobsStore = create((set) => ({
  jobs: [] as Job[],
  setJobs: (jobs: Job[]) => set({ jobs }),
}));

export const useSchedulesStore = create((set) => ({
  schedules: [] as Schedule[],
  setSchedules: (schedules: Schedule[]) => set({ schedules }),
}));

export const usePresetsStore = create((set) => ({
  presets: [] as Preset[],
  setPresets: (presets: Preset[]) => set({ presets }),
}));