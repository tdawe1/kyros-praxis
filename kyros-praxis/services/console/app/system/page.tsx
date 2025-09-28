'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Grid,
  Column,
  Tile,
  ClickableTile,
  InlineNotification,
  SkeletonPlaceholder,
  ProgressBar,
} from '@carbon/react';
import {
  Dashboard,
  Activity,
  DataBase,
  Security,
  Settings,
} from '@carbon/icons-react';
import Link from 'next/link';

interface SystemStats {
  uptime: string;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  activeJobs: number;
  totalRequests: number;
}

export default function SystemPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['system-stats'],
    queryFn: async (): Promise<SystemStats> => {
      const response = await fetch('/api/v1/system/stats');
      if (!response.ok) {
        throw new Error('Failed to fetch system stats');
      }
      return response.json();
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  if (error) {
    return (
      <div className="cds--content" data-testid="system-page">
        <InlineNotification
          kind="error"
          title="Error loading system information"
          subtitle={error.message}
          hideCloseButton
        />
      </div>
    );
  }

  const systemItems = [
    {
      title: 'Jobs Queue',
      description: 'Monitor and manage background jobs',
      href: '/system/jobs',
      icon: Dashboard,
      count: stats?.activeJobs || 0,
    },
    {
      title: 'Webhooks',
      description: 'Configure webhook endpoints',
      href: '/system/webhooks',
      icon: Activity,
    },
    {
      title: 'Database',
      description: 'Database health and migrations',
      href: '/system/database',
      icon: DataBase,
    },
    {
      title: 'Audit Log',
      description: 'View system activity logs',
      href: '/system/audit',
      icon: Security,
    },
    {
      title: 'Configuration',
      description: 'System settings and config',
      href: '/system/config',
      icon: Settings,
    },
  ];

  return (
    <div className="cds--content" data-testid="system-page">
      <div style={{ marginBottom: '2rem' }}>
        <h1>System Dashboard</h1>
        <p style={{ color: 'var(--cds-text-secondary)' }}>
          Monitor system health, performance, and configuration
        </p>
      </div>

      {/* System Stats */}
      <Grid style={{ marginBottom: '2rem' }}>
        <Column sm={4} md={2} lg={3}>
          <Tile style={{ height: '120px', padding: '1rem' }}>
            <h4>System Uptime</h4>
            {isLoading ? (
              <SkeletonPlaceholder style={{ height: '1.5rem', marginTop: '0.5rem' }} />
            ) : (
              <p style={{ fontSize: '1.25rem', fontWeight: 'bold', marginTop: '0.5rem' }}>
                {stats?.uptime || 'N/A'}
              </p>
            )}
          </Tile>
        </Column>
        <Column sm={4} md={2} lg={3}>
          <Tile style={{ height: '120px', padding: '1rem' }}>
            <h4>CPU Usage</h4>
            {isLoading ? (
              <SkeletonPlaceholder style={{ height: '1.5rem', marginTop: '0.5rem' }} />
            ) : (
              <>
                <p style={{ fontSize: '1.25rem', fontWeight: 'bold', marginTop: '0.5rem' }}>
                  {stats?.cpuUsage || 0}%
                </p>
                <ProgressBar 
                  value={stats?.cpuUsage || 0} 
                  max={100} 
                  size="sm"
                  style={{ marginTop: '0.5rem' }}
                />
              </>
            )}
          </Tile>
        </Column>
        <Column sm={4} md={2} lg={3}>
          <Tile style={{ height: '120px', padding: '1rem' }}>
            <h4>Memory Usage</h4>
            {isLoading ? (
              <SkeletonPlaceholder style={{ height: '1.5rem', marginTop: '0.5rem' }} />
            ) : (
              <>
                <p style={{ fontSize: '1.25rem', fontWeight: 'bold', marginTop: '0.5rem' }}>
                  {stats?.memoryUsage || 0}%
                </p>
                <ProgressBar 
                  value={stats?.memoryUsage || 0} 
                  max={100} 
                  size="sm"
                  style={{ marginTop: '0.5rem' }}
                />
              </>
            )}
          </Tile>
        </Column>
        <Column sm={4} md={2} lg={3}>
          <Tile style={{ height: '120px', padding: '1rem' }}>
            <h4>Active Jobs</h4>
            {isLoading ? (
              <SkeletonPlaceholder style={{ height: '1.5rem', marginTop: '0.5rem' }} />
            ) : (
              <p style={{ fontSize: '1.25rem', fontWeight: 'bold', marginTop: '0.5rem' }}>
                {stats?.activeJobs || 0}
              </p>
            )}
          </Tile>
        </Column>
      </Grid>

      {/* System Components */}
      <Grid>
        {systemItems.map((item) => {
          const Icon = item.icon;
          return (
            <Column key={item.href} sm={4} md={4} lg={8}>
              <ClickableTile
                href={item.href}
                style={{ height: '120px', padding: '1rem' }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                  <div>
                    <h4 style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Icon size={20} />
                      {item.title}
                    </h4>
                    <p style={{ color: 'var(--cds-text-secondary)', fontSize: '0.875rem' }}>
                      {item.description}
                    </p>
                  </div>
                  {item.count !== undefined && (
                    <div style={{ 
                      backgroundColor: 'var(--cds-interactive-01)', 
                      color: 'white',
                      borderRadius: '12px',
                      padding: '0.25rem 0.5rem',
                      fontSize: '0.75rem',
                      fontWeight: 'bold'
                    }}>
                      {item.count}
                    </div>
                  )}
                </div>
              </ClickableTile>
            </Column>
          );
        })}
      </Grid>
    </div>
  );
}