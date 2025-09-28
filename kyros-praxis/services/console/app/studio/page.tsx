'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DataTable,
  DataTableSkeleton,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TableContainer,
  TableToolbar,
  TableToolbarContent,
  TableToolbarSearch,
  Button,
  Tag,
  OverflowMenu,
  OverflowMenuItem,
  Modal,
  InlineNotification,
  Layer,
  Tile,
} from '@carbon/react';
import {
  Add,
  Code,
  Edit,
  Delete,
} from '@carbon/icons-react';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

interface StudioProject {
  id: string;
  name: string;
  description: string;
  type: 'workflow' | 'agent' | 'integration';
  status: 'draft' | 'active' | 'archived';
  createdAt: string;
  updatedAt: string;
  author: string;
  tags: string[];
}

const fetchStudioProjects = async (): Promise<{ projects: StudioProject[]; total: number }> => {
  const response = await fetch('/api/v1/studio/projects');
  if (!response.ok) {
    throw new Error('Failed to fetch studio projects');
  }
  return response.json();
};

const deleteProject = async (id: string) => {
  const response = await fetch(`/api/v1/studio/projects/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete project');
  }
};

const statusConfig = {
  draft: { type: 'gray', label: 'Draft' },
  active: { type: 'green', label: 'Active' },
  archived: { type: 'red', label: 'Archived' },
} as const;

const typeConfig = {
  workflow: { type: 'blue', label: 'Workflow' },
  agent: { type: 'purple', label: 'Agent' },
  integration: { type: 'teal', label: 'Integration' },
} as const;

export default function StudioPage() {
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['studio-projects'],
    queryFn: fetchStudioProjects,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['studio-projects'] });
      setDeleteModalOpen(false);
      setSelectedProjectId(null);
    },
  });

  const headers = [
    { key: 'name', header: 'Project Name' },
    { key: 'type', header: 'Type' },
    { key: 'status', header: 'Status' },
    { key: 'author', header: 'Author' },
    { key: 'updated', header: 'Last Modified' },
    { key: 'actions', header: '' },
  ];

  const rows = data?.projects?.map(project => ({
    id: project.id,
    name: project.name,
    type: project.type,
    status: project.status,
    author: project.author,
    updated: formatDistanceToNow(new Date(project.updatedAt), { addSuffix: true }),
    project,
  })) || [];

  const handleDeleteProject = (projectId: string) => {
    setSelectedProjectId(projectId);
    setDeleteModalOpen(true);
  };

  if (error) {
    return (
      <div className="cds--content" data-testid="studio-page">
        <InlineNotification
          kind="error"
          title="Error loading studio"
          subtitle={error.message}
          hideCloseButton
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="cds--content" data-testid="studio-page">
        <DataTableSkeleton
          columnCount={headers.length}
          rowCount={10}
          headers={headers}
          showHeader
          showToolbar
        />
      </div>
    );
  }

  if (!data?.projects?.length) {
    return (
      <div className="cds--content" data-testid="studio-page">
        <Layer>
          <Tile className="empty-state" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <Code size={64} style={{ marginBottom: '1rem' }} />
            <h3 style={{ marginBottom: '0.5rem' }}>No projects yet</h3>
            <p style={{ marginBottom: '2rem', color: 'var(--cds-text-secondary)' }}>
              Create your first workflow, agent, or integration to get started
            </p>
            <Button
              as={Link}
              href="/studio/new"
              renderIcon={Add}
              kind="primary"
              data-testid="add-studio"
            >
              Create Project
            </Button>
          </Tile>
        </Layer>
      </div>
    );
  }

  return (
    <div className="cds--content" data-testid="studio-page">
      <DataTable
        rows={rows}
        headers={headers}
        isSortable
        useZebraStyles
        size="lg"
        render={({
          rows,
          headers,
          getHeaderProps,
          getRowProps,
          getTableProps,
          getTableContainerProps,
        }) => (
          <TableContainer
            title="Studio Projects"
            description="Manage workflows, agents, and integrations"
            {...getTableContainerProps()}
            data-testid="studio-table"
          >
            <TableToolbar>
              <TableToolbarContent>
                <TableToolbarSearch
                  placeholder="Search projects..."
                  persistent
                />
                <Button
                  as={Link}
                  href="/studio/new"
                  renderIcon={Add}
                  kind="primary"
                  data-testid="add-studio"
                >
                  Create Project
                </Button>
              </TableToolbarContent>
            </TableToolbar>
            <Table {...getTableProps()}>
              <TableHead>
                <TableRow>
                  {headers.map((header) => {
                    const { key, ...headerProps } = getHeaderProps({ 
                      header, 
                      isSortable: header.key !== 'actions' 
                    });
                    return (
                      <TableHeader key={header.key} {...headerProps}>
                        {header.header}
                      </TableHeader>
                    );
                  })}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row) => {
                  const { key, ...rowProps } = getRowProps({ row });
                  return (
                    <TableRow key={row.id} {...rowProps}>
                      <TableCell>
                        <Link
                          href={`/studio/${row.id}`}
                          style={{ color: 'var(--cds-link-primary)', textDecoration: 'none' }}
                        >
                          {row.project.name}
                        </Link>
                        {row.project.description && (
                          <div style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
                            {row.project.description}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <Tag type={typeConfig[row.project.type]?.type}>
                          {typeConfig[row.project.type]?.label}
                        </Tag>
                      </TableCell>
                      <TableCell>
                        <Tag type={statusConfig[row.project.status]?.type}>
                          {statusConfig[row.project.status]?.label}
                        </Tag>
                      </TableCell>
                      <TableCell>{row.project.author}</TableCell>
                      <TableCell>{row.updated}</TableCell>
                      <TableCell>
                        <OverflowMenu size="sm" flipped>
                          <OverflowMenuItem
                            itemText="Open"
                            onClick={() => window.location.href = `/studio/${row.id}`}
                          />
                          <OverflowMenuItem
                            itemText="Edit"
                            onClick={() => window.location.href = `/studio/${row.id}/edit`}
                          />
                          <OverflowMenuItem
                            itemText="Clone"
                            onClick={() => window.location.href = `/studio/${row.id}/clone`}
                          />
                          <OverflowMenuItem
                            itemText="Export"
                            hasDivider
                          />
                          <OverflowMenuItem
                            itemText="Delete"
                            isDelete
                            onClick={() => handleDeleteProject(row.id)}
                          />
                        </OverflowMenu>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      />

      <Modal
        open={deleteModalOpen}
        danger
        modalHeading="Delete project"
        modalLabel="Confirmation"
        primaryButtonText="Delete"
        secondaryButtonText="Cancel"
        onRequestClose={() => setDeleteModalOpen(false)}
        onRequestSubmit={() => {
          if (selectedProjectId) {
            deleteMutation.mutate(selectedProjectId);
          }
        }}
      >
        <p>
          Are you sure you want to delete this project? This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
}