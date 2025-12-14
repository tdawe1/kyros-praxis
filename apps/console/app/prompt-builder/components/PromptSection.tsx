'use client';

import type { ReactNode } from 'react';

type PromptSectionProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
};

export function PromptSection({ title, description, action, children }: PromptSectionProps) {
  return (
    <section className="flex flex-col gap-4 rounded-xl border border-neutral-800 bg-neutral-950/70 p-6 shadow-sm backdrop-blur">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex flex-col gap-1">
          <h2 className="text-lg font-semibold text-neutral-100">{title}</h2>
          {description ? <p className="text-sm text-neutral-400">{description}</p> : null}
        </div>
        {action ? <div className="flex shrink-0 items-center gap-2">{action}</div> : null}
      </header>
      <div className="flex flex-col gap-4">{children}</div>
    </section>
  );
}

