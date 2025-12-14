'use client';

import { useEffect, useMemo, useState } from 'react';

import { Button, Field, TextInput } from '@shared/ui/components';

import { createProject, listProjects, APIError } from '../lib/api-client';
import type { ProjectSummary } from '../lib/workflow-types';

type ProjectSelectorProps = {
  projectId: string;
  onSelect: (projectId: string) => void;
};

export function ProjectSelector({ projectId, onSelect }: ProjectSelectorProps) {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createName, setCreateName] = useState('');
  const [createDescription, setCreateDescription] = useState('');

  const sortedProjects = useMemo(
    () =>
      [...projects].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()),
    [projects],
  );

  const loadProjects = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await listProjects();
      setProjects(data);
      if (!projectId && data.length > 0) {
        onSelect(data[0].id);
      }
    } catch (err) {
      const message = err instanceof APIError ? err.message : err instanceof Error ? err.message : 'Unable to load projects';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProjects().catch(() => {
      /* handled above */
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreate = async () => {
    if (!createName.trim()) {
      setError('Project name is required.');
      return;
    }

    setIsCreating(true);
    setError(null);
    try {
      const project = await createProject({
        name: createName.trim(),
        description: createDescription.trim() || undefined,
      });
      setProjects((prev) => [project, ...prev]);
      onSelect(project.id);
      setCreateName('');
      setCreateDescription('');
    } catch (err) {
      const message = err instanceof APIError ? err.message : err instanceof Error ? err.message : 'Unable to create project';
      setError(message);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-neutral-800 bg-neutral-950/70 p-4 sm:p-6">
      <header className="flex flex-col gap-2">
        <h2 className="text-xl font-semibold text-neutral-100">Project</h2>
        <p className="text-sm text-neutral-400">
          Select an existing project or create a new one. The planner and coder operate in the context of this project ID.
        </p>
      </header>

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-neutral-500" htmlFor="project-select">
            Existing Projects
          </label>
          <Button type="button" variant="ghost" onClick={loadProjects} disabled={isLoading} loading={isLoading} loadingLabel="Refreshing…">
            Refresh
          </Button>
        </div>
        <select
          id="project-select"
          value={projectId}
          onChange={(event) => onSelect(event.target.value)}
          disabled={isLoading || sortedProjects.length === 0}
          className="rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm text-neutral-200 focus:outline focus:outline-2 focus:outline-emerald-500"
        >
          {sortedProjects.length === 0 ? (
            <option value="">No projects available</option>
          ) : null}
          {sortedProjects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name} • {project.workflow_status}
            </option>
          ))}
        </select>
        {isLoading ? <span className="text-xs text-neutral-500">Loading projects…</span> : null}
      </div>

      <div className="flex flex-col gap-3">
        <Field label="Create New Project" helpText="Name is required; description is optional.">
          <TextInput
            value={createName}
            onChange={(event) => setCreateName(event.target.value)}
            placeholder="Workspace Planner"
          />
        </Field>
        <textarea
          value={createDescription}
          onChange={(event) => setCreateDescription(event.target.value)}
          placeholder="Optional: describe the project goals or context"
          className="min-h-[96px] rounded-lg border border-neutral-800 bg-neutral-950 p-3 text-sm text-neutral-200 focus:outline focus:outline-2 focus:outline-emerald-500"
        />
        <div className="flex justify-end">
          <Button type="button" onClick={handleCreate} loading={isCreating} loadingLabel="Creating…">
            Create Project
          </Button>
        </div>
      </div>

      {error ? <p className="text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}
