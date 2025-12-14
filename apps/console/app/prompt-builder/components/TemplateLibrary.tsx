'use client';

import type { PromptTemplate } from '../types';

type TemplateLibraryProps = {
  templates: PromptTemplate[];
  selectedTemplateId: string | null;
  onSelect: (template: PromptTemplate) => void;
};

export function TemplateLibrary({ templates, selectedTemplateId, onSelect }: TemplateLibraryProps) {
  if (templates.length === 0) {
    return <p className="text-sm text-neutral-400">No templates available yet. Create your own prompt below.</p>;
  }

  return (
    <ul className="flex flex-col gap-3">
      {templates.map((template) => {
        const isSelected = template.id === selectedTemplateId;
        return (
          <li key={template.id}>
            <button
              type="button"
              aria-pressed={isSelected}
              onClick={() => onSelect(template)}
              className={`group flex w-full flex-col gap-3 rounded-xl border border-neutral-800 bg-neutral-950/60 p-4 text-left transition hover:border-neutral-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500 ${
                isSelected ? 'border-emerald-500/70 bg-emerald-500/5 shadow-[0_0_0_1px_rgba(16,185,129,0.35)]' : ''
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-neutral-100">{template.name}</span>
                  <span className="text-xs text-neutral-400">{template.description}</span>
                </div>
                <span
                  className={`text-xs font-mono ${
                    isSelected ? 'text-emerald-400' : 'text-neutral-500 group-hover:text-neutral-300'
                  }`}
                >
                  {isSelected ? 'Selected' : 'Use template'}
                </span>
              </div>
              <p className="rounded-lg border border-neutral-900 bg-neutral-950/80 p-3 text-xs text-neutral-400">
                {template.prompt}
              </p>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
