'use client';

import { Button, Card } from '@shared/ui/components';
import type { Specification } from '../lib/workflow-types';

type SpecReviewProps = {
  specification: Specification;
  validationScore?: number;
  iteration?: number;
  isSubmitting?: boolean;
  onApprove: () => void;
  onRefine: () => void;
};

const renderList = (items?: string[]) => {
  if (!items || items.length === 0) {
    return <p className="text-sm text-neutral-500">Not provided.</p>;
  }
  return (
    <ul className="list-disc space-y-2 pl-5 text-sm text-neutral-200">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
};

const renderRecord = (record?: Record<string, unknown>) => {
  if (!record || Object.keys(record).length === 0) {
    return <p className="text-sm text-neutral-500">Not provided.</p>;
  }

  return (
    <dl className="grid gap-3 text-sm text-neutral-200 md:grid-cols-2">
      {Object.entries(record).map(([key, value]) => (
        <div key={key} className="flex flex-col gap-1 rounded-lg border border-neutral-800/70 bg-neutral-950/60 p-3">
          <dt className="text-xs font-semibold uppercase tracking-wide text-neutral-500">{key}</dt>
          <dd className="text-sm text-neutral-200">{formatValue(value)}</dd>
        </div>
      ))}
    </dl>
  );
};

const formatValue = (value: unknown): string => {
  if (typeof value === 'string') {
    return value;
  }
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (value && typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  return String(value ?? '');
};

export function SpecReview({ specification, validationScore, iteration, isSubmitting, onApprove, onRefine }: SpecReviewProps) {
  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <span className="text-xs font-semibold uppercase tracking-[0.25em] text-neutral-500">
          Specification Review {typeof iteration === 'number' ? `• Iteration ${iteration}` : ''}
        </span>
        <h2 className="text-2xl font-semibold text-neutral-50">Review the Proposed Build Plan</h2>
        <p className="max-w-3xl text-sm text-neutral-400">
          Validate that the planner captured the intended goals, features, and technical approach. Approve to continue to code generation or refine with additional guidance.
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card header="Purpose" density="compact">
          <p className="text-sm leading-6 text-neutral-200">{specification.purpose}</p>
        </Card>

        <Card header="Validation Score" density="compact">
          <p className="text-sm text-neutral-200">
            {typeof validationScore === 'number'
              ? `Readiness score: ${validationScore}/100`
              : 'Planner did not return a validation score.'}
          </p>
          <p className="text-xs text-neutral-500">
            Scores above 70 indicate the planner is confident about scope clarity.
          </p>
        </Card>

        <Card header="Components" density="compact">
          {renderList(specification.components)}
        </Card>

        <Card header="Dependencies" density="compact">
          {renderList(specification.dependencies)}
        </Card>

        <Card header="Technology Stack" density="compact">
          {renderRecord(specification.technology)}
        </Card>

        <Card header="File Structure" density="compact">
          {renderRecord(specification.file_structure)}
        </Card>

        {specification.data_models ? (
          <Card header="Data Models" density="compact">
            {renderRecord(specification.data_models)}
          </Card>
        ) : null}

        {specification.implementation_plan ? (
          <Card header="Implementation Plan" density="compact">
            {renderList(specification.implementation_plan)}
          </Card>
        ) : null}

        {specification.testing_considerations ? (
          <Card header="Testing Considerations" density="compact">
            {renderList(specification.testing_considerations)}
          </Card>
        ) : null}

        {specification.challenges ? (
          <Card header="Risks & Challenges" density="compact">
            {renderList(specification.challenges)}
          </Card>
        ) : null}
      </div>

      <footer className="flex flex-col gap-3 rounded-xl border border-neutral-800 bg-neutral-950/60 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1 text-sm text-neutral-400">
          <span>Approve when the proposed solution aligns with expectations.</span>
          <span className="text-xs text-neutral-500">
            Need adjustments? Add refinement notes to iterate with the planner.
          </span>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <Button type="button" variant="ghost" onClick={onRefine} disabled={isSubmitting}>
            Refine Prompt
          </Button>
          <Button type="button" onClick={onApprove} loading={isSubmitting} loadingLabel="Approving…">
            Approve Specification
          </Button>
        </div>
      </footer>
    </section>
  );
}

