'use client';

import type { PromptValidationResult } from '../types';

type ValidationFeedbackProps = {
  result: PromptValidationResult;
  currentLength: number;
  minChars: number;
  maxChars?: number;
};

export function ValidationFeedback({
  result,
  currentLength,
  minChars,
  maxChars,
}: ValidationFeedbackProps) {
  const { status, message } = result;

  const missingCharacters = Math.max(0, minChars - currentLength);
  const overLimit = maxChars ? Math.max(0, currentLength - maxChars) : 0;

  const computedMessage = (() => {
    if (status === 'error') {
      return message ?? 'Please adjust this section for clarity.';
    }

    if (status === 'valid') {
      return message ?? 'Looks good.';
    }

    if (currentLength === 0) {
      return `Aim for at least ${minChars} characters.`;
    }

    if (missingCharacters > 0) {
      return `Add ${missingCharacters} more character${missingCharacters === 1 ? '' : 's'} for clarity.`;
    }

    if (overLimit > 0) {
      return `Trim ${overLimit} character${overLimit === 1 ? '' : 's'} to stay within the limit.`;
    }

    return 'Keep refining the narrative for the planner.';
  })();

  const toneClass = (() => {
    if (status === 'error' || overLimit > 0) {
      return 'text-rose-400';
    }
    if (status === 'valid') {
      return 'text-emerald-400';
    }
    if (missingCharacters > 0) {
      return 'text-amber-400';
    }
    return 'text-neutral-400';
  })();

  const limitLabel = maxChars ? `${currentLength}/${maxChars} chars` : `${currentLength} chars`;
  const remainingLabel =
    maxChars && overLimit === 0
      ? `${Math.max(0, maxChars - currentLength)} remaining`
      : undefined;

  return (
    <footer className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
      <p className={`text-sm ${toneClass}`}>{computedMessage}</p>
      <div className="flex items-center gap-2 text-xs font-mono text-neutral-500">
        <span>{limitLabel}</span>
        {remainingLabel ? <span>• {remainingLabel}</span> : null}
      </div>
    </footer>
  );
}

