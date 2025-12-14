'use client';

import { useMemo } from 'react';

import type { FileTreeNode, ViewerFile } from './types';

type FileTreeProps = {
  files: ViewerFile[];
  selectedPath: string | null;
  onSelect: (filePath: string) => void;
};

type TreeItemProps = {
  node: FileTreeNode;
  depth: number;
  selectedPath: string | null;
  onSelect: (filePath: string) => void;
};

const iconForNode = (node: FileTreeNode) => {
  if (node.type === 'directory') {
    return '📁';
  }
  const extension = node.name.split('.').pop() ?? '';
  switch (extension) {
    case 'ts':
    case 'tsx':
      return '📄';
    case 'js':
    case 'jsx':
      return '🟨';
    case 'json':
      return '🧾';
    case 'md':
      return '📝';
    case 'css':
    case 'scss':
      return '🎨';
    case 'py':
      return '🐍';
    default:
      return '📄';
  }
};

const sortTree = (nodes: FileTreeNode[]): FileTreeNode[] =>
  [...nodes].sort((a, b) => {
    if (a.type === b.type) {
      return a.name.localeCompare(b.name);
    }
    return a.type === 'directory' ? -1 : 1;
  });

const buildTree = (files: ViewerFile[]): FileTreeNode[] => {
  const rootMap: Record<string, FileTreeNode> = {};

  const ensureDir = (pathSegments: string[], fullPath: string): FileTreeNode => {
    const key = pathSegments.join('/');
    if (rootMap[key]) {
      return rootMap[key];
    }
    const parentKey = pathSegments.slice(0, -1).join('/');
    const parentNode = parentKey ? rootMap[parentKey] : null;
    const node: FileTreeNode = {
      id: key || '/',
      name: pathSegments[pathSegments.length - 1],
      path: fullPath,
      type: 'directory',
      children: [],
    };
    rootMap[key] = node;
    if (parentNode) {
      parentNode.children = parentNode.children ?? [];
      parentNode.children.push(node);
    }
    return node;
  };

  const roots: FileTreeNode[] = [];

  files.forEach((file) => {
    const segments = file.name.split('/').filter(Boolean);
    const fileName = segments.pop() ?? file.name;
    let parent: FileTreeNode | null = null;
    let currentPath = '';

    segments.forEach((segment, index) => {
      currentPath = `${currentPath}/${segment}`;
      const dirNode = ensureDir(segments.slice(0, index + 1), currentPath);
      if (!containsNode(roots, dirNode)) {
        roots.push(dirNode);
      }
      parent = dirNode;
    });

    const fileNode: FileTreeNode = {
      id: file.id,
      name: fileName,
      path: file.name,
      type: 'file',
    };

    if (parent) {
      parent.children = parent.children ?? [];
      parent.children.push(fileNode);
    } else {
      roots.push(fileNode);
    }
  });

  const dedupeRoots = deduplicateNodes(roots);

  return sortTree(dedupeRoots).map((node) => (node.children ? sortNode(node) : node));
};

const deduplicateNodes = (nodes: FileTreeNode[]): FileTreeNode[] => {
  const seen = new Set<string>();
  return nodes.filter((node) => {
    const key = node.path || node.id;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
};

const sortNode = (node: FileTreeNode): FileTreeNode => ({
  ...node,
  children: node.children ? sortTree(node.children).map((child) => (child.children ? sortNode(child) : child)) : undefined,
});

const containsNode = (nodes: FileTreeNode[], target: FileTreeNode) =>
  nodes.some((node) => node.id === target.id || node.path === target.path);

const TreeItem = ({ node, depth, selectedPath, onSelect }: TreeItemProps) => {
  const isSelected = node.type === 'file' && node.path === selectedPath;
  const isDirectory = node.type === 'directory';
  const padding = depth * 12;

  return (
    <li>
      <button
        type="button"
        className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition ${
          isSelected ? 'bg-neutral-800 text-neutral-50' : 'text-neutral-300 hover:bg-neutral-900 hover:text-neutral-50'
        }`}
        style={{ paddingLeft: `${padding + 12}px` }}
        onClick={() => {
          if (!isDirectory) {
            onSelect(node.path);
          }
        }}
        disabled={isDirectory}
      >
        <span aria-hidden>{iconForNode(node)}</span>
        <span className="truncate">{node.name}</span>
      </button>
      {node.children && node.children.length > 0 ? (
        <ul className="ml-0">
          {node.children.map((child) => (
            <TreeItem
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
};

export function FileTree({ files, selectedPath, onSelect }: FileTreeProps) {
  const tree = useMemo(() => buildTree(files), [files]);

  if (tree.length === 0) {
    return <p className="text-sm text-neutral-500">No files generated yet.</p>;
  }

  return (
    <nav aria-label="Generated files" className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-neutral-500">Files</h3>
      <ul className="space-y-1">
        {tree.map((node) => (
          <TreeItem key={node.id} node={node} depth={0} selectedPath={selectedPath} onSelect={onSelect} />
        ))}
      </ul>
    </nav>
  );
}
