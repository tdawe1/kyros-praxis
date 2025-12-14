'use client';

import { useEffect, useMemo, useState } from 'react';

import { Button } from '@shared/ui/components';

import { CodeViewer } from '../components/CodeViewer';
import { DiffViewer } from '../components/DiffViewer';
import { ProjectSelector } from '../components/ProjectSelector';
import { SpecReview } from '../components/SpecReview';
import {
  approveSpecification,
  generateProject,
  getProjectCode,
  getProjectSpecification,
  getWorkflowStatus,
  regenerateProject,
  APIError,
} from '../lib/api-client';
import type {
  CodeFile,
  Specification,
  WorkflowResult,
  WorkflowStatusResponse,
} from '../lib/workflow-types';
import { PromptInput } from './components/PromptInput';
import { PromptSection } from './components/PromptSection';
import { TemplateLibrary } from './components/TemplateLibrary';
import {
  EMPTY_DRAFT,
  SECTION_CONFIGS,
  SECTION_LOOKUP,
  buildValidationMap,
  computeValidation,
  isDraftReady,
} from './config';
import { templates } from './templates';
import type { PromptDraft, PromptSectionKey, PromptValidationMap, PromptTemplate } from './types';

type FlowState = 'input' | 'planning' | 'review' | 'coding' | 'complete' | 'error';

const INITIAL_PROJECT_ID = '';

const buildPromptFromDraft = (draft: PromptDraft) => {
  const segments = SECTION_CONFIGS.map((config) => {
    const value = draft[config.key].trim();
    if (!value) {
      return null;
    }
    return `${config.title}:\n${value}`;
  }).filter(Boolean);

  return segments.join('\n\n');
};

const formatError = (error: unknown): { message: string; correlationId?: string } => {
  if (error instanceof APIError) {
    return {
      message: error.message,
      correlationId: error.correlationId,
    };
  }

  if (error instanceof Error) {
    return { message: error.message };
  }

  return { message: 'Unexpected error occurred. Please try again.' };
};

const formatSpecificationForDiff = (spec: Specification) => {
  const sections: string[] = [];
  sections.push(`Purpose:\n${spec.purpose}`);

  if (spec.components?.length) {
    sections.push(`Components:\n${spec.components.map((item) => `- ${item}`).join('\n')}`);
  }

  if (spec.dependencies?.length) {
    sections.push(`Dependencies:\n${spec.dependencies.map((item) => `- ${item}`).join('\n')}`);
  }

  if (spec.technology && Object.keys(spec.technology).length > 0) {
    sections.push(`Technology:\n${JSON.stringify(spec.technology, null, 2)}`);
  }

  if (spec.file_structure && Object.keys(spec.file_structure).length > 0) {
    sections.push(`File Structure:\n${JSON.stringify(spec.file_structure, null, 2)}`);
  }

  if (spec.implementation_plan?.length) {
    sections.push(`Implementation Plan:\n${spec.implementation_plan.map((item) => `- ${item}`).join('\n')}`);
  }

  if (spec.testing_considerations?.length) {
    sections.push(`Testing Considerations:\n${spec.testing_considerations.map((item) => `- ${item}`).join('\n')}`);
  }

  if (spec.challenges?.length) {
    sections.push(`Risks & Challenges:\n${spec.challenges.map((item) => `- ${item}`).join('\n')}`);
  }

  return sections.join('\n\n');
};

export function PromptBuilderWorkspace() {
  const [projectId, setProjectId] = useState(INITIAL_PROJECT_ID);
  const [draft, setDraft] = useState<PromptDraft>(EMPTY_DRAFT);
  const [validation, setValidation] = useState<PromptValidationMap>(() => buildValidationMap(EMPTY_DRAFT));
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);

  const [flowState, setFlowState] = useState<FlowState>('input');
  const [workflow, setWorkflow] = useState<WorkflowResult | null>(null);
  const [specification, setSpecification] = useState<Specification | null>(null);
  const [previousSpecification, setPreviousSpecification] = useState<Specification | null>(null);
  const [codeFiles, setCodeFiles] = useState<CodeFile[]>([]);
  const [testFiles, setTestFiles] = useState<CodeFile[]>([]);
  const [refinementNotes, setRefinementNotes] = useState('');
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatusResponse | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRefining, setIsRefining] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [correlationId, setCorrelationId] = useState<string | null>(null);

  const preview = useMemo(() => buildPromptFromDraft(draft), [draft]);

  const canSubmit = isDraftReady(draft, validation) && Boolean(projectId.trim());

  const iterationCount =
    workflow?.iteration ?? (previousSpecification ? 2 : specification ? 1 : undefined);

  const handleFieldChange = (key: PromptSectionKey, value: string) => {
    setDraft((prev) => ({
      ...prev,
      [key]: value,
    }));
    setValidation((prev) => ({
      ...prev,
      [key]: computeValidation(value, SECTION_LOOKUP[key]),
    }));
  };

  const handleTemplateSelect = (template: PromptTemplate) => {
    const nextDraft: PromptDraft = {
      purpose: template.sections.purpose ?? '',
      features: template.sections.features ?? '',
      techStack: template.sections.techStack ?? '',
    };

    setDraft(nextDraft);
    setValidation(buildValidationMap(nextDraft));
    setSelectedTemplateId(template.id);
  };

  const resetErrors = () => {
    setError(null);
    setCorrelationId(null);
  };

  const applySpecification = (next: Specification | null) => {
    if (!next) {
      return;
    }
    if (specification) {
      setPreviousSpecification(specification);
    }
    setSpecification(next);
  };

  const applyCodeFiles = (code: CodeFile[] | undefined, tests: CodeFile[] | undefined) => {
    if (code) {
      setCodeFiles(code);
    }
    if (tests) {
      setTestFiles(tests);
    }
  };

  const fetchLatestSpecification = async () => {
    if (!projectId.trim()) {
      return null;
    }
    try {
      const response = await getProjectSpecification(projectId.trim());
      applySpecification(response.specification);
      return response.specification;
    } catch (err) {
      const formatted = formatError(err);
      setError(formatted.message);
      setCorrelationId(formatted.correlationId ?? null);
      return null;
    }
  };

  const fetchLatestCode = async () => {
    if (!projectId.trim()) {
      return;
    }
    try {
      const response = await getProjectCode(projectId.trim());
      applyCodeFiles(response.code_files, response.test_files);
      setFlowState('complete');
    } catch (err) {
      const formatted = formatError(err);
      setError(formatted.message);
      setCorrelationId(formatted.correlationId ?? null);
    }
  };

  const handleGenerate = async () => {
    const nextValidation = buildValidationMap(draft);
    setValidation(nextValidation);

    if (!isDraftReady(draft, nextValidation)) {
      setError('Complete each section before generating a specification.');
      return;
    }

    if (!projectId.trim()) {
      setError('Provide a project ID to generate a specification.');
      return;
    }

    resetErrors();
    setIsSubmitting(true);
    setFlowState('planning');
    setWorkflowStatus(null);

    try {
      const result = await generateProject(projectId.trim(), {
        prompt: buildPromptFromDraft(draft),
      });

      setWorkflow(result);
      if (result.specification) {
        applySpecification(result.specification);
        setFlowState('review');
      } else {
        const spec = await fetchLatestSpecification();
        if (spec) {
          setFlowState('review');
        } else {
          setFlowState('error');
          setError('Planner did not return a specification. Try refining the prompt.');
        }
      }
    } catch (err) {
      const formatted = formatError(err);
      setError(formatted.message);
      setCorrelationId(formatted.correlationId ?? null);
      setFlowState('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApprove = async () => {
    if (!specification || !projectId.trim()) {
      return;
    }

    resetErrors();
    setIsApproving(true);
    setFlowState('coding');
    setWorkflowStatus(null);

    try {
      const result = await approveSpecification(projectId.trim(), {
        approved: true,
        specification,
      });

      setWorkflow(result);
      if (result.code_files?.length || result.test_files?.length) {
        applyCodeFiles(result.code_files, result.test_files);
      }

      if (result.status === 'completed') {
        if (result.code_files?.length || result.test_files?.length) {
          setFlowState('complete');
        } else {
          await fetchLatestCode();
        }
      } else if (result.status === 'needs_refinement') {
        if (result.specification) {
          applySpecification(result.specification);
          setFlowState('review');
        } else {
          const nextSpec = await fetchLatestSpecification();
          if (nextSpec) {
            setFlowState('review');
          } else {
            setFlowState('error');
            setError(result.message ?? 'Code generation failed.');
          }
        }
      } else {
        setFlowState('error');
        setError(result.message ?? 'Code generation failed.');
      }
    } catch (err) {
      const formatted = formatError(err);
      setError(formatted.message);
      setCorrelationId(formatted.correlationId ?? null);
      setFlowState('error');
    } finally {
      setIsApproving(false);
    }
  };

  const handleSubmitRefinement = async () => {
    if (!projectId.trim()) {
      return;
    }

    if (!refinementNotes.trim()) {
      setError('Add refinement notes before requesting another iteration.');
      return;
    }

    resetErrors();
    setIsRefining(true);
    setFlowState('planning');
    setWorkflowStatus(null);

    try {
      const result = await regenerateProject(projectId.trim(), {
        refinement_notes: refinementNotes.trim(),
      });

      setWorkflow(result);

      if (result.status === 'awaiting_approval') {
        if (result.specification) {
          applySpecification(result.specification);
          setFlowState('review');
        } else {
          const spec = await fetchLatestSpecification();
          if (spec) {
            setFlowState('review');
          } else {
            setFlowState('error');
            setError('Planner did not return a specification for refinement.');
          }
        }
      } else if (result.status === 'completed') {
        if (result.code_files?.length || result.test_files?.length) {
          applyCodeFiles(result.code_files, result.test_files);
          setFlowState('complete');
        } else {
          await fetchLatestCode();
        }
      } else {
        setFlowState('error');
        setError(result.message ?? 'Refinement failed.');
      }
    } catch (err) {
      const formatted = formatError(err);
      setError(formatted.message);
      setCorrelationId(formatted.correlationId ?? null);
      setFlowState('error');
    } finally {
      setIsRefining(false);
      setRefinementNotes('');
    }
  };

  const handleRefineRequest = () => {
    setFlowState('review');
    if (typeof window !== 'undefined') {
      window.setTimeout(() => {
        const element = document.getElementById('refinement-notes');
        if (element instanceof HTMLTextAreaElement) {
          element.focus();
        }
      }, 0);
    }
  };

  useEffect(() => {
    if (!projectId.trim()) {
      return;
    }

    if (flowState !== 'planning' && flowState !== 'coding') {
      return;
    }

    let isActive = true;

    const pollStatus = async () => {
      try {
        const status = await getWorkflowStatus(projectId.trim());
        if (isActive) {
          setWorkflowStatus(status);
        }
      } catch (statusError) {
        console.debug('Workflow status poll failed', statusError);
      }
    };

    pollStatus();
    const intervalId = window.setInterval(pollStatus, 4000);

    return () => {
      isActive = false;
      window.clearInterval(intervalId);
    };
  }, [projectId, flowState]);

  useEffect(() => {
    if (!workflowStatus) {
      return;
    }

    const plannerStage = workflowStatus.stages.find((stage) => stage.stage === 'planner');
    const coderStage = workflowStatus.stages.find((stage) => stage.stage === 'coder');

    if (!specification && plannerStage?.status === 'completed') {
      fetchLatestSpecification().catch(() => {
        /* error handled inside */
      });
    }

    if (workflowStatus.project_status === 'completed') {
      if (codeFiles.length === 0 && testFiles.length === 0) {
        fetchLatestCode().catch(() => {
          /* error handled inside */
        });
      } else if (flowState !== 'complete') {
        setFlowState('complete');
      }
    } else if (
      workflowStatus.project_status === 'generating' &&
      coderStage?.status === 'active' &&
      flowState === 'planning'
    ) {
      setFlowState('coding');
    }
  }, [workflowStatus, specification, codeFiles.length, testFiles.length, flowState]);

  const statusLabel = (() => {
    switch (flowState) {
      case 'planning':
        return 'Planner is generating a specification…';
      case 'coding':
        return 'Coder and tester agents are generating deliverables…';
      case 'complete':
        return 'Generation complete!';
      case 'error':
        return 'Encountered an error during generation.';
      default:
        return 'Ready to submit prompt data.';
    }
  })();

  const stageSummary = useMemo(() => {
    if (!workflowStatus) {
      return null;
    }
    const stageLines = workflowStatus.stages.map(
      (stage) => `${stage.stage}: ${stage.status}`,
    );

    return `Status: ${workflowStatus.project_status}${stageLines.length > 0 ? ` • ${stageLines.join(' • ')}` : ''}`;
  }, [workflowStatus]);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-10">
      <header className="flex flex-col gap-3">
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-neutral-500">
          Prompt Builder
        </span>
        <h1 className="text-3xl font-semibold text-neutral-50">Describe what we should build</h1>
        <p className="max-w-3xl text-sm text-neutral-400">
          Capture the problem, the capabilities you expect, and the technical boundaries. The planner uses this structured input to produce specifications, run plans, and final code.
        </p>
      </header>

      <ProjectSelector projectId={projectId} onSelect={setProjectId} />

      <div className="grid gap-8 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="flex flex-col gap-6">
          <PromptInput
            sections={SECTION_CONFIGS}
            values={draft}
            validation={validation}
            onChange={handleFieldChange}
          />

          <div className="flex flex-col gap-3 rounded-xl border border-neutral-800 bg-neutral-950/70 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col gap-1 text-sm text-neutral-400">
              <span>{statusLabel}</span>
              {workflow?.message ? (
                <span className="text-xs text-neutral-500">{workflow.message}</span>
              ) : null}
              {stageSummary ? (
                <span className="text-xs text-neutral-500">{stageSummary}</span>
              ) : null}
              {correlationId ? (
                <span className="text-xs text-amber-500">Correlation ID: {correlationId}</span>
              ) : null}
            </div>
            <Button
              type="button"
              onClick={handleGenerate}
              loading={isSubmitting}
              loadingLabel="Generating…"
              disabled={!canSubmit || flowState === 'planning' || flowState === 'coding'}
            >
              Generate Specification
            </Button>
          </div>

          {error ? (
            <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-4 text-sm text-rose-200">
              {error}
            </div>
          ) : null}
        </div>

        <aside className="flex flex-col gap-6">
          <PromptSection
            title="Template Library"
            description="Kick-start with a curated template, then customise the details."
          >
            <TemplateLibrary
              templates={templates}
              selectedTemplateId={selectedTemplateId}
              onSelect={handleTemplateSelect}
            />
          </PromptSection>

          <PromptSection
            title="Prompt Preview"
            description="Combined prompt that will be sent to the planner and crew agents."
          >
            {preview ? (
              <pre className="max-h-[320px] overflow-y-auto rounded-lg border border-neutral-900 bg-neutral-950/80 p-4 text-xs leading-6 text-neutral-200">
                {preview}
              </pre>
            ) : (
              <p className="text-sm text-neutral-500">
                Start filling in the sections on the left to see a live preview of the generated prompt.
              </p>
            )}
          </PromptSection>
        </aside>
      </div>

      {specification && flowState !== 'complete' ? (
        <SpecReview
          specification={specification}
          validationScore={workflow?.validation_score}
          iteration={iterationCount}
          isSubmitting={isApproving || isRefining}
          onApprove={handleApprove}
          onRefine={handleRefineRequest}
        />
      ) : null}

      {flowState === 'review' && specification ? (
        <section className="flex flex-col gap-4 rounded-xl border border-neutral-800 bg-neutral-950/70 p-6">
          <header className="flex flex-col gap-1">
            <h3 className="text-lg font-semibold text-neutral-100">Refinement Notes</h3>
            <p className="text-sm text-neutral-400">
              Share updates or clarifications for the planner. These notes are appended to the existing context.
            </p>
          </header>
          <textarea
            id="refinement-notes"
            className="min-h-[120px] rounded-lg border border-neutral-800 bg-neutral-950 p-4 text-sm text-neutral-200 focus:outline focus:outline-2 focus:outline-emerald-500"
            placeholder="Clarify requirements, add constraints, or emphasise features to adjust the spec."
            value={refinementNotes}
            onChange={(event) => setRefinementNotes(event.target.value)}
          />
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setRefinementNotes('')}
              disabled={isRefining}
            >
              Clear Notes
            </Button>
            <Button
              type="button"
              onClick={handleSubmitRefinement}
              loading={isRefining}
              loadingLabel="Submitting…"
            >
              Submit Refinement
            </Button>
          </div>
        </section>
      ) : null}

      {specification && previousSpecification ? (
        <DiffViewer
          previous={formatSpecificationForDiff(previousSpecification)}
          current={formatSpecificationForDiff(specification)}
        />
      ) : null}

      {flowState === 'complete' ? (
        <CodeViewer codeFiles={codeFiles} testFiles={testFiles} />
      ) : null}
    </main>
  );
}
