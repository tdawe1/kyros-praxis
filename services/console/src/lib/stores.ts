import { create } from 'zustand';

export const useAgentsStore = create((set) => ({
  agents: [],
  setAgents: (agents) => set({ agents }),
}));

export const useTasksStore = create((set) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
}));

export const useLeasesStore = create((set) => ({
  leases: [],
  setLeases: (leases) => set({ leases }),
}));

export const useEventsStore = create((set) => ({
  events: [],
  setEvents: (events) => set({ events }),
}));

export const useJobsStore = create((set) => ({
  jobs: [],
  setJobs: (jobs) => set({ jobs }),
}));

export const useSchedulesStore = create((set) => ({
  schedules: [],
  setSchedules: (schedules) => set({ schedules }),
}));

export const usePresetsStore = create((set) => ({
  presets: [],
  setPresets: (presets) => set({ presets }),
}));