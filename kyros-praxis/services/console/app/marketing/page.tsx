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
  ChartLine,
} from '@carbon/icons-react';
import Link from 'next/link';

export default function MarketingPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['marketing'],
    queryFn: async () => {
      // Placeholder API call
      const response = await fetch('/api/v1/marketing/campaigns');
      if (!response.ok) {
        throw new Error('Failed to fetch marketing data');
      }
      return response.json();
    },
  });

  if (error) {
    return (
      <div className="cds--content" data-testid="marketing-page">
        <InlineNotification
          kind="error"
          title="Error loading marketing data"
          subtitle={error.message}
          hideCloseButton
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="cds--content" data-testid="marketing-page">
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
    <div className="cds--content" data-testid="marketing-page">
      <Layer>
        <Tile className="empty-state" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <ChartLine size={64} style={{ marginBottom: '1rem' }} />
          <h3 style={{ marginBottom: '0.5rem' }}>Marketing Dashboard</h3>
          <p style={{ marginBottom: '2rem', color: 'var(--cds-text-secondary)' }}>
            Track campaigns, analytics, and marketing performance metrics
          </p>
          <Button
            as={Link}
            href="/marketing/new"
            renderIcon={Add}
            kind="primary"
            data-testid="add-campaign"
          >
            Create Campaign
          </Button>
        </Tile>
      </Layer>
    </div>
  );
}