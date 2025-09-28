'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  DataTable,
  DataTableSkeleton,
  Button,
  Layer,
  Tile,
  InlineNotification,
} from '@carbon/react';
import {
  Add,
  Currency,
} from '@carbon/icons-react';
import Link from 'next/link';

export default function QuotesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['quotes'],
    queryFn: async () => {
      // Placeholder API call
      const response = await fetch('/api/v1/quotes');
      if (!response.ok) {
        throw new Error('Failed to fetch quotes');
      }
      return response.json();
    },
  });

  if (error) {
    return (
      <div className="cds--content" data-testid="quotes-page">
        <InlineNotification
          kind="error"
          title="Error loading quotes"
          subtitle={error.message}
          hideCloseButton
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="cds--content" data-testid="quotes-page">
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
    <div className="cds--content" data-testid="quotes-page">
      <Layer>
        <Tile className="empty-state" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <Currency size={64} style={{ marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>Quotes Management</h3>
          <p style={{ marginBottom: '2rem', color: 'var(--cds-text-secondary)' }}>
            Manage pricing quotes and proposals for your projects
          </p>
          <Button
            as={Link}
            href="/quotes/new"
            renderIcon={Add}
            kind="primary"
            data-testid="add-quote"
          >
            Create Quote
          </Button>
        </Tile>
      </Layer>
    </div>
  );
}