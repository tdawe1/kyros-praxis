'use client';

import { useEffect, useMemo, useState } from 'react';
import Highlight, { defaultProps, Language } from 'prism-react-renderer';
import theme from 'prism-react-renderer/themes/nightOwl';

import type { ViewerFile } from './types';

type CodeDisplayProps = {
  file: ViewerFile | null;
};

const languageByExtension: Record<string, Language> = {
  ts: 'tsx',
  tsx: 'tsx',
  js: 'jsx',
  jsx: 'jsx',
  json: 'json',
  md: 'markdown',
  css: 'css',
  scss: 'css',
  py: 'python',
  rs: 'rust',
  go: 'go',
  sh: 'bash',
  yml: 'yaml',
  yaml: 'yaml',
};

const detectLanguage = (fileName: string): Language => {
  const extension = fileName.split('.').pop()?.toLowerCase() ?? '';
  return languageByExtension[extension] ?? 'tsx';
};

export function CodeDisplay({ file }: CodeDisplayProps) {
  const [copied, setCopied] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    setQuery('');
  }, [file?.id]);

  useEffect(() => {
    if (!copied) {
      return;
    }
    const handle = setTimeout(() => setCopied(false), 1500);
    return () => clearTimeout(handle);
  }, [copied]);

  const filteredContent = useMemo(() => {
    if (!file) {
      return '';
    }
    if (!query) {
      return file.content;
    }
    const lines = file.content.split('\n');
    return lines
      .filter((line) => line.toLowerCase().includes(query.toLowerCase()))
      .join('\n');
  }, [file, query]);

  if (!file) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-neutral-800 text-sm text-neutral-500">
        <p>Select a file to inspect generated code.</p>
      </div>
    );
  }

  const language = detectLanguage(file.name);

  const handleCopy = () => {
    if (!file?.content) {
      return;
    }
    navigator.clipboard
      .writeText(file.content)
      .then(() => setCopied(true))
      .catch(() => setCopied(false));
  };

  return (
    <section className="flex h-full flex-col overflow-hidden rounded-xl border border-neutral-800 bg-neutral-950/80">
      <header className="flex flex-col gap-2 border-b border-neutral-900/60 bg-neutral-950/60 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1">
          <h3 className="font-mono text-sm text-neutral-200">{file.name}</h3>
          {file.metadata?.description ? (
            <p className="text-xs text-neutral-500">{file.metadata.description}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search in file…"
            className="w-44 rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-1.5 text-xs text-neutral-200 focus:outline focus:outline-2 focus:outline-emerald-500"
          />
          <button
            type="button"
            onClick={handleCopy}
            className="rounded-lg border border-neutral-800 px-3 py-1.5 text-xs text-neutral-300 transition hover:border-neutral-600 hover:text-neutral-50"
          >
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </header>

      <div className="relative flex-1 overflow-auto">
        <Highlight
          {...defaultProps}
          theme={theme}
          code={filteredContent}
          language={language}
        >
          {({ className, style, tokens, getLineProps, getTokenProps }) => (
            <pre className={`${className} m-0 min-h-full bg-transparent p-6 text-sm`} style={style}>
              {tokens.map((line, index) => {
                const lineNumber = index + 1;
                return (
                  <div key={lineNumber} className="flex gap-6">
                    <span className="w-10 shrink-0 text-right text-xs text-neutral-600">{lineNumber}</span>
                    <span className="flex-1">
                      {line.map((token, key) => (
                        <span key={key} {...getTokenProps({ token })} />
                      ))}
                    </span>
                  </div>
                );
              })}
            </pre>
          )}
        </Highlight>
      </div>
    </section>
  );
}

