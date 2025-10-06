'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DataTable,
  DataTableSkeleton,
  Button,
  Layer,
  Tile,
  InlineNotification,
  CodeSnippet,
} from '@carbon/react';
import {
  Add,
  Terminal,
} from '@carbon/icons-react';
import Link from 'next/link';

export default function RemotePage() {
  const [connections, setConnections] = useState([]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['remote-connections'],
    queryFn: async () => {
      // Placeholder API call
      const response = await fetch('/api/v1/remote/connections');
      if (!response.ok) {
        throw new Error('Failed to fetch remote connections');
      }
      return response.json();
    },
  });

  if (error) {
    return (
      <div className="cds--content" data-testid="remote-page">
        <InlineNotification
          kind="error"
          title="Error loading remote connections"
          subtitle={error.message}
          hideCloseButton
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="cds--content" data-testid="remote-page">
        <DataTableSkeleton
          columnCount={6}
          rowCount={10}
          showHeader
          showToolbar
        />
      </div>
    );
  }

  return (
    <div className="cds--content" data-testid="remote-page">
      <Layer>
        <Tile className="empty-state" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <Terminal size={64} style={{ marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>Remote Access</h3>
          <p style={{ marginBottom: '2rem', color: 'var(--cds-text-secondary)' }}>
            Manage remote connections, SSH tunnels, and terminal sessions
          </p>
          <Button
            as={Link}
            href="/remote/new"
            renderIcon={Add}
            kind="primary"
            data-testid="add-connection"
          >
            New Connection
          </Button>
        </Tile>
      </Layer>
    </div>
  );
}