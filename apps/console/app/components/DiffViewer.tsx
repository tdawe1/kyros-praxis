'use client';

import { diffLines } from 'diff';
import { useMemo } from 'react';

type DiffViewerProps = {
  previous: string;
  current: string;
  title?: string;
};

type DiffRow = {
  left?: string;
  right?: string;
  type: 'common' | 'added' | 'removed';
};

const sanitizeLines = (value: string) =>
  value.replace(/\r\n/g, '\n').split('\n').filter((_, index, arr) => !(index === arr.length - 1 && arr[index] === ''));

const buildDiffRows = (previous: string, current: string): DiffRow[] => {
  const diff = diffLines(previous, current);
  const rows: DiffRow[] = [];

  diff.forEach((part) => {
    const lines = sanitizeLines(part.value);
    if (part.added) {
      lines.forEach((line) => {
        rows.push({ right: line, type: 'added' });
      });
    } else if (part.removed) {
      lines.forEach((line) => {
        rows.push({ left: line, type: 'removed' });
      });
    } else {
      lines.forEach((line) => {
        rows.push({ left: line, right: line, type: 'common' });
      });
    }
  });

  return rows;
};

const rowClass = (type: DiffRow['type']) => {
  if (type === 'added') {
    return 'bg-emerald-500/10 text-emerald-200';
  }
  if (type === 'removed') {
    return 'bg-rose-500/10 text-rose-200';
  }
  return 'text-neutral-200';
};

export function DiffViewer({ previous, current, title }: DiffViewerProps) {
  const rows = useMemo(() => buildDiffRows(previous, current), [previous, current]);
  const hasChanges = useMemo(() => rows.some((row) => row.type !== 'common'), [rows]);

  return (
    <section className="flex flex-col gap-4 rounded-xl border border-neutral-800 bg-neutral-950/70 p-6">
      <header className="flex flex-col gap-1">
        <h3 className="text-lg font-semibold text-neutral-100">{title ?? 'Differences from previous iteration'}</h3>
        <p className="text-sm text-neutral-400">
          {hasChanges
            ? 'Review how the specification evolved after refinement.'
            : 'No differences detected – the planner returned the same content.'}
        </p>
      </header>

      <div className="overflow-hidden rounded-lg border border-neutral-900">
        <div className="grid grid-cols-2 bg-neutral-950/80 text-xs font-semibold uppercase tracking-wide text-neutral-500">
          <div className="border-r border-neutral-900 px-4 py-2">Previous</div>
          <div className="px-4 py-2">Current</div>
        </div>
        <ol className="max-h-[360px] overflow-y-auto text-sm">
          {rows.map((row, index) => (
            <li key={`${row.type}-${index}`} className={`grid grid-cols-2 border-t border-neutral-900`}>
              <pre className={`border-r border-neutral-900 px-4 py-2 font-mono text-xs leading-6 ${rowClass(row.type === 'added' ? 'common' : row.type)}`}>
                {row.left ?? ''}
              </pre>
              <pre className={`px-4 py-2 font-mono text-xs leading-6 ${rowClass(row.type === 'removed' ? 'common' : row.type)}`}>
                {row.right ?? ''}
              </pre>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

