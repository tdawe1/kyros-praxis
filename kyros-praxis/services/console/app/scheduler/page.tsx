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
  CodeSnippet,
} from '@carbon/react';
import {
  Add,
  Calendar,
  Play,
  Pause,
  Edit,
  Delete,
  Time,
} from '@carbon/icons-react';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

interface ScheduledJob {
  id: string;
  name: string;
  description: string;
  cron: string;
  enabled: boolean;
  nextRun: string;
  lastRun?: string;
  status: 'active' | 'paused' | 'failed';
  jobType: string;
  createdAt: string;
  updatedAt: string;
}

const fetchScheduledJobs = async (): Promise<{ jobs: ScheduledJob[]; total: number }> => {
  const response = await fetch('/api/v1/scheduler/jobs');
  if (!response.ok) {
    throw new Error('Failed to fetch scheduled jobs');
  }
  return response.json();
};

const toggleJob = async ({ id, enabled }: { id: string; enabled: boolean }) => {
  const response = await fetch(`/api/v1/scheduler/jobs/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) {
    throw new Error('Failed to update job');
  }
  return response.json();
};

const deleteJob = async (id: string) => {
  const response = await fetch(`/api/v1/scheduler/jobs/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete job');
  }
};

const statusConfig = {
  active: { type: 'green', label: 'Active' },
  paused: { type: 'gray', label: 'Paused' },
  failed: { type: 'red', label: 'Failed' },
} as const;

export default function SchedulerPage() {
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['scheduled-jobs'],
    queryFn: fetchScheduledJobs,
  });

  const toggleMutation = useMutation({
    mutationFn: toggleJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-jobs'] });
      setDeleteModalOpen(false);
      setSelectedJobId(null);
    },
  });

  const headers = [
    { key: 'name', header: 'Job Name' },
    { key: 'cron', header: 'Schedule' },
    { key: 'status', header: 'Status' },
    { key: 'nextRun', header: 'Next Run' },
    { key: 'lastRun', header: 'Last Run' },
    { key: 'jobType', header: 'Type' },
    { key: 'actions', header: '' },
  ];

  const rows = data?.jobs?.map(job => ({
    id: job.id,
    name: job.name,
    cron: job.cron,
    status: job.status,
    nextRun: formatDistanceToNow(new Date(job.nextRun), { addSuffix: true }),
    lastRun: job.lastRun 
      ? formatDistanceToNow(new Date(job.lastRun), { addSuffix: true })
      : 'Never',
    jobType: job.jobType,
    job,
  })) || [];

  const handleDeleteJob = (jobId: string) => {
    setSelectedJobId(jobId);
    setDeleteModalOpen(true);
  };

  const handleToggleJob = (job: ScheduledJob) => {
    toggleMutation.mutate({ id: job.id, enabled: !job.enabled });
  };

  if (error) {
    return (
      <div className="cds--content" data-testid="scheduler-page">
        <InlineNotification
          kind="error"
          title="Error loading scheduler"
          subtitle={error.message}
          hideCloseButton
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="cds--content" data-testid="scheduler-page">
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

  if (!data?.jobs?.length) {
    return (
      <div className="cds--content" data-testid="scheduler-page">
        <Layer>
          <Tile className="empty-state" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <Calendar size={64} style={{ marginBottom: '1rem' }} />
            <h3 style={{ marginBottom: '0.5rem' }}>No scheduled jobs yet</h3>
            <p style={{ marginBottom: '2rem', color: 'var(--cds-text-secondary)' }}>
              Create your first scheduled job to automate recurring tasks
            </p>
            <Button
              as={Link}
              href="/scheduler/new"
              renderIcon={Add}
              kind="primary"
              data-testid="add-scheduler"
            >
              Create Schedule
            </Button>
          </Tile>
        </Layer>
      </div>
    );
  }

  return (
    <div className="cds--content" data-testid="scheduler-page">
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
            title="Scheduled Jobs"
            description="Manage automated job scheduling and cron tasks"
            {...getTableContainerProps()}
            data-testid="scheduler-table"
          >
            <TableToolbar>
              <TableToolbarContent>
                <TableToolbarSearch
                  placeholder="Search scheduled jobs..."
                  persistent
                />
                <Button
                  as={Link}
                  href="/scheduler/new"
                  renderIcon={Add}
                  kind="primary"
                  data-testid="add-scheduler"
                >
                  Create Schedule
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
                          href={`/scheduler/${row.id}`}
                          style={{ color: 'var(--cds-link-primary)', textDecoration: 'none' }}
                        >
                          {row.job.name}
                        </Link>
                        {row.job.description && (
                          <div style={{ fontSize: '0.875rem', color: 'var(--cds-text-secondary)' }}>
                            {row.job.description}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <CodeSnippet type="inline" feedback="Copied">
                          {row.job.cron}
                        </CodeSnippet>
                      </TableCell>
                      <TableCell>
                        <Tag type={statusConfig[row.job.status]?.type}>
                          {statusConfig[row.job.status]?.label}
                        </Tag>
                      </TableCell>
                      <TableCell>{row.nextRun}</TableCell>
                      <TableCell>{row.lastRun}</TableCell>
                      <TableCell>{row.job.jobType}</TableCell>
                      <TableCell>
                        <OverflowMenu size="sm" flipped>
                          <OverflowMenuItem
                            itemText="View"
                            onClick={() => window.location.href = `/scheduler/${row.id}`}
                          />
                          <OverflowMenuItem
                            itemText="Edit"
                            onClick={() => window.location.href = `/scheduler/${row.id}/edit`}
                          />
                          <OverflowMenuItem
                            itemText={row.job.enabled ? "Pause" : "Resume"}
                            onClick={() => handleToggleJob(row.job)}
                          />
                          <OverflowMenuItem
                            itemText="Run Now"
                            onClick={() => {/* trigger immediate run */}}
                          />
                          <OverflowMenuItem
                            itemText="Clone"
                            onClick={() => window.location.href = `/scheduler/${row.id}/clone`}
                          />
                          <OverflowMenuItem
                            itemText="Delete"
                            isDelete
                            hasDivider
                            onClick={() => handleDeleteJob(row.id)}
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
        modalHeading="Delete scheduled job"
        modalLabel="Confirmation"
        primaryButtonText="Delete"
        secondaryButtonText="Cancel"
        onRequestClose={() => setDeleteModalOpen(false)}
        onRequestSubmit={() => {
          if (selectedJobId) {
            deleteMutation.mutate(selectedJobId);
          }
        }}
      >
        <p>
          Are you sure you want to delete this scheduled job? This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
}