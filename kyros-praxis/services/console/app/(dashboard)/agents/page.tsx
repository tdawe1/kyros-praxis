'use client';

import { useState, useMemo, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
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
  TableToolbarMenu,
  TableToolbarAction,
  TableBatchActions,
  TableBatchAction,
  TableSelectAll,
  TableSelectRow,
  Button,
  Tag,
  OverflowMenu,
  OverflowMenuItem,
  Modal,
  InlineNotification,
  Pagination,
  Dropdown,
  MultiSelect,
  Layer,
  Tile,
  SkeletonPlaceholder,
} from '@carbon/react';
import {
  Add,
  Play,
  Pause,
  Delete,
  Download,
  Upload,
  Copy,
  Edit,
  View,
  Settings,
  Chemistry,
} from '@carbon/icons-react';
import { useAgents, useBulkUpdateAgents, useBulkDeleteAgents, useRunAgent } from '../../hooks/useAgents';
import { Agent } from '../../lib/schemas/agent';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';

const statusConfig = {
  active: { type: 'green', label: 'Active' },
  paused: { type: 'gray', label: 'Paused' },
  error: { type: 'red', label: 'Error' },
  pending: { type: 'blue', label: 'Pending' },
} as const;

function AgentsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // URL state
  const page = Number(searchParams.get('page')) || 1;
  const pageSize = Number(searchParams.get('pageSize')) || 20;
  const status = searchParams.get('status') || undefined;
  const sortBy = searchParams.get('sortBy') || 'updatedAt';
  const sortOrder = (searchParams.get('sortOrder') || 'desc') as 'asc' | 'desc';
  const searchTerm = searchParams.get('search') || '';

  // Local state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedRows, setSelectedRows] = useState<string[]>([]);
  const [importModalOpen, setImportModalOpen] = useState(false);

  // Queries and mutations
  const { data, isLoading, error } = useAgents({
    page,
    pageSize,
    status,
    sortBy,
    sortOrder,
  });
  const bulkUpdate = useBulkUpdateAgents();
  const bulkDelete = useBulkDeleteAgents();
  const runAgent = useRunAgent();

  // Filter agents by search term
  const filteredAgents = useMemo(() => {
    if (!data?.agents) return [];
    if (!searchTerm) return data.agents;
    
    const term = searchTerm.toLowerCase();
    return data.agents.filter(agent =>
      agent.name.toLowerCase().includes(term) ||
      agent.description?.toLowerCase().includes(term) ||
      agent.tags.some(tag => tag.toLowerCase().includes(term))
    );
  }, [data?.agents, searchTerm]);

  // Table headers
  const headers = [
    { key: 'name', header: 'Name' },
    { key: 'status', header: 'Status' },
    { key: 'model', header: 'Model' },
    { key: 'lastRun', header: 'Last Run' },
    { key: 'owner', header: 'Owner' },
    { key: 'capabilities', header: 'Capabilities' },
    { key: 'successRate', header: 'Success Rate' },
    { key: 'actions', header: '' },
  ];

  // Transform agents for DataTable
  const rows = useMemo(() => {
    return filteredAgents.map(agent => ({
      id: agent.id,
      name: agent.name,
      status: agent.status,
      model: agent.model,
      lastRun: agent.lastRunAt 
        ? formatDistanceToNow(new Date(agent.lastRunAt), { addSuffix: true })
        : 'Never',
      owner: agent.owner,
      capabilities: agent.capabilities.length,
      successRate: agent.successRate 
        ? `${agent.successRate.toFixed(1)}%`
        : 'N/A',
      agent, // Keep full agent object for actions
    }));
  }, [filteredAgents]);

  // Handle bulk actions
  const handleBulkPause = () => {
    bulkUpdate.mutate({
      ids: selectedRows,
      update: { status: 'paused' },
    });
    setSelectedRows([]);
  };

  const handleBulkResume = () => {
    bulkUpdate.mutate({
      ids: selectedRows,
      update: { status: 'active' },
    });
    setSelectedRows([]);
  };

  const handleBulkDelete = () => {
    bulkDelete.mutate(selectedRows);
    setDeleteModalOpen(false);
    setSelectedRows([]);
  };

  // Handle pagination
  const handlePaginationChange = ({ page, pageSize }: { page: number; pageSize: number }) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('page', page.toString());
    params.set('pageSize', pageSize.toString());
    router.push(`/agents?${params.toString()}`);
  };

  if (error) {
    return (
      <div className="cds--content" data-testid="agents-page">
        <InlineNotification
          kind="error"
          title="Error loading agents"
          subtitle={error.message}
          hideCloseButton
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="cds--content" data-testid="agents-page">
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

  // Empty state
  if (!data?.agents.length && !searchTerm) {
    return (
      <div className="cds--content" data-testid="agents-page">
        <Layer>
          <Tile className="empty-state" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <Chemistry size={64} style={{ marginBottom: '1rem' }} />
            <h3 style={{ marginBottom: '0.5rem' }}>No agents yet</h3>
            <p style={{ marginBottom: '2rem', color: 'var(--cds-text-secondary)' }}>
              Create your first AI agent to get started with automation
            </p>
            <Button
              as={Link}
              href="/agents/new"
              renderIcon={Add}
              kind="primary"
              data-testid="add-agent"
            >
              Create Agent
            </Button>
          </Tile>
        </Layer>
      </div>
    );
  }

  return (
    <div className="cds--content" data-testid="agents-page">
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
          getSelectionProps,
          getTableProps,
          getTableContainerProps,
          getBatchActionProps,
          selectedRows,
        }) => {
          const batchActionProps = getBatchActionProps();

          return (
            <TableContainer
              title="Agents"
              description="Manage your AI agents and their configurations"
              {...getTableContainerProps()}
              data-testid="agents-table"
            >
              <TableToolbar>
                <TableBatchActions {...batchActionProps}>
                  <TableBatchAction
                    renderIcon={Play}
                    onClick={handleBulkResume}
                  >
                    Resume
                  </TableBatchAction>
                  <TableBatchAction
                    renderIcon={Pause}
                    onClick={handleBulkPause}
                  >
                    Pause
                  </TableBatchAction>
                  <TableBatchAction
                    renderIcon={Delete}
                    onClick={() => setDeleteModalOpen(true)}
                  >
                    Delete
                  </TableBatchAction>
                </TableBatchActions>
                <TableToolbarContent>
                  <TableToolbarSearch
                    placeholder="Search agents..."
                    persistent
                    onChange={(evt: any) => {
                      const params = new URLSearchParams(searchParams.toString());
                      if (evt.target.value) {
                        params.set('search', evt.target.value);
                      } else {
                        params.delete('search');
                      }
                      router.push(`/agents?${params.toString()}`);
                    }}
                  />
                  <TableToolbarMenu>
                    <TableToolbarAction onClick={() => setImportModalOpen(true)}>
                      <Upload /> Import
                    </TableToolbarAction>
                    <TableToolbarAction onClick={() => {/* Export all */}}>
                      <Download /> Export All
                    </TableToolbarAction>
                  </TableToolbarMenu>
                  <Button
                    as={Link}
                    href="/agents/new"
                    renderIcon={Add}
                    kind="primary"
                    data-testid="add-agent"
                  >
                    Create Agent
                  </Button>
                </TableToolbarContent>
              </TableToolbar>
              <Table {...getTableProps()}>
                <TableHead>
                  <TableRow>
                    <TableSelectAll {...getSelectionProps()} />
                     {headers.map((header) => {
                       const { key, ...headerProps } = getHeaderProps({ header, isSortable: header.key !== 'actions' });
                       return (
                         <TableHeader
                           key={header.key}
                           {...headerProps}
                         >
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
                         <TableSelectRow {...getSelectionProps({ row })} />
                         <TableCell>
                           <Link
                             href={`/agents/${row.cells[0].value}`}
                             style={{ color: 'var(--cds-link-primary)', textDecoration: 'none' }}
                           >
                             {row.cells[0].value}
                           </Link>
                         </TableCell>
                         <TableCell>
                           <Tag type={statusConfig[row.cells[1].value as keyof typeof statusConfig]?.type}>
                             {statusConfig[row.cells[1].value as keyof typeof statusConfig]?.label}
                           </Tag>
                         </TableCell>
                         <TableCell>{row.cells[2].value}</TableCell>
                         <TableCell>{row.cells[3].value}</TableCell>
                         <TableCell>{row.cells[4].value}</TableCell>
                         <TableCell>{row.cells[5].value}</TableCell>
                         <TableCell>{row.cells[6].value}</TableCell>
                         <TableCell>
                           <OverflowMenu size="sm" flipped>
                             <OverflowMenuItem
                               itemText="View"
                               onClick={() => router.push(`/agents/${row.id}`)}
                             />
                             <OverflowMenuItem
                               itemText="Edit"
                               onClick={() => router.push(`/agents/${row.id}/edit`)}
                             />
                             <OverflowMenuItem
                               itemText="Playground"
                               onClick={() => router.push(`/agents/${row.id}/playground`)}
                             />
                             <OverflowMenuItem
                               itemText="Run Now"
                               onClick={() => runAgent.mutate({ id: row.id })}
                             />
                             <OverflowMenuItem
                               itemText="Clone"
                               onClick={() => router.push(`/agents/${row.id}/clone`)}
                             />
                             <OverflowMenuItem
                               itemText="Export"
                               hasDivider
                             />
                             <OverflowMenuItem
                               itemText="Delete"
                               isDelete
                             />
                           </OverflowMenu>
                         </TableCell>
                       </TableRow>
                     );
                   })}
                </TableBody>
              </Table>
              <Pagination
                backwardText="Previous page"
                forwardText="Next page"
                itemsPerPageText="Items per page:"
                page={page}
                pageSize={pageSize}
                pageSizes={[10, 20, 50, 100]}
                totalItems={data?.total || 0}
                onChange={handlePaginationChange}
              />
            </TableContainer>
          );
        }}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        open={deleteModalOpen}
        danger
        modalHeading="Delete agents"
        modalLabel="Confirmation"
        primaryButtonText="Delete"
        secondaryButtonText="Cancel"
        onRequestClose={() => setDeleteModalOpen(false)}
        onRequestSubmit={handleBulkDelete}
      >
        <p>
          Are you sure you want to delete {selectedRows.length} agent(s)? 
          This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
}

export default function AgentsPage() {
  return (
    <Suspense fallback={
      <div className="cds--content">
        <DataTableSkeleton
          columnCount={8}
          rowCount={10}
          showHeader
          showToolbar
        />
      </div>
    }>
      <AgentsPageContent />
    </Suspense>
  );
}
