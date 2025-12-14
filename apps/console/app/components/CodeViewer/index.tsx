'use client';

import { useEffect, useMemo, useState } from 'react';

import type { CodeFile } from '../../lib/workflow-types';
import { Card } from '@shared/ui/components';
import { CodeDisplay } from './CodeDisplay';
import { FileTree } from './FileTree';
import type { ViewerFile } from './types';

type CodeViewerProps = {
  codeFiles: CodeFile[];
  testFiles?: CodeFile[];
};

const toViewerFiles = (files: CodeFile[]): ViewerFile[] =>
  files.map((file) => ({
    id: file.id,
    name: file.name,
    content: file.content,
    metadata: file.metadata,
    created_at: file.created_at,
  }));

export function CodeViewer({ codeFiles, testFiles = [] }: CodeViewerProps) {
  const allFiles = useMemo(() => [...toViewerFiles(codeFiles), ...toViewerFiles(testFiles)], [codeFiles, testFiles]);
  const [selectedPath, setSelectedPath] = useState<string | null>(allFiles[0]?.name ?? null);

  const selectedFile = useMemo(() => allFiles.find((file) => file.name === selectedPath) ?? allFiles[0] ?? null, [allFiles, selectedPath]);

  useEffect(() => {
    if (allFiles.length === 0) {
      setSelectedPath(null);
      return;
    }
    if (!selectedPath || !allFiles.some((file) => file.name === selectedPath)) {
      setSelectedPath(allFiles[0].name);
    }
  }, [allFiles, selectedPath]);

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <span className="text-xs font-semibold uppercase tracking-[0.25em] text-neutral-500">Generated Code</span>
        <h2 className="text-2xl font-semibold text-neutral-50">Inspect the generated deliverables</h2>
        <p className="max-w-3xl text-sm text-neutral-400">
          Browse the file tree to review generated source and test files. Copy snippets directly into your repo or download the project bundle when ready.
        </p>
      </header>

      <Card>
        <div className="grid gap-6 lg:grid-cols-[minmax(0,280px)_minmax(0,1fr)]">
          <div className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-4">
            <FileTree files={allFiles} selectedPath={selectedFile?.name ?? null} onSelect={setSelectedPath} />
          </div>
          <CodeDisplay file={selectedFile} />
        </div>
      </Card>
    </section>
  );
}
