export type ViewerFile = {
  id: string;
  name: string;
  content: string;
  metadata?: {
    description?: string;
    generated_by?: string;
  };
  created_at?: string;
};

export type FileTreeNode = {
  id: string;
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileTreeNode[];
};

