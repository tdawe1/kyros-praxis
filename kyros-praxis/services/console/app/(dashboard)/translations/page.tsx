'use client';

import { 
  Button, 
  Tile, 
  Layer,
  InlineNotification,
  StructuredListWrapper,
  StructuredListHead,
  StructuredListBody,
  StructuredListRow,
  StructuredListCell,
  Tag,
} from '@carbon/react';
import { Translate, Add, ArrowRight } from '@carbon/icons-react';
import Link from 'next/link';

export default function TranslationsPage() {
  // Mock data for demonstration
  const recentJobs = [
    {
      id: '1',
      source: 'English',
      targets: ['Spanish', 'French', 'German'],
      status: 'completed',
      progress: 100,
      date: '2024-03-10',
    },
    {
      id: '2',
      source: 'English',
      targets: ['Japanese', 'Korean'],
      status: 'in_progress',
      progress: 65,
      date: '2024-03-11',
    },
  ];

  const statusConfig = {
    completed: { type: 'green', label: 'Completed' },
    in_progress: { type: 'blue', label: 'In Progress' },
    failed: { type: 'red', label: 'Failed' },
    pending: { type: 'gray', label: 'Pending' },
  } as const;

  return (
    <div className="cds--content">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ marginBottom: '0.5rem' }}>Translations</h1>
        <p style={{ color: 'var(--cds-text-secondary)' }}>
          Manage content translation workflows and localization
        </p>
      </div>

      <InlineNotification
        kind="info"
        title="Coming Soon"
        subtitle="Translation management features are currently in development."
        hideCloseButton
        lowContrast
        style={{ marginBottom: '2rem' }}
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <Layer>
          <Tile>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>Quick Actions</h3>
              <Translate size={24} />
            </div>
            <Button renderIcon={Add} kind="primary" style={{ marginBottom: '0.5rem', width: '100%' }}>
              New Translation Job
            </Button>
            <Button renderIcon={ArrowRight} kind="tertiary" style={{ width: '100%' }}>
              Import Content
            </Button>
          </Tile>
        </Layer>

        <Layer>
          <Tile>
            <h3 style={{ marginBottom: '1rem' }}>Statistics</h3>
            <div style={{ display: 'grid', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Total Jobs:</span>
                <strong>24</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Languages:</span>
                <strong>12</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Words Translated:</span>
                <strong>45,230</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Avg. Turnaround:</span>
                <strong>2.3 hrs</strong>
              </div>
            </div>
          </Tile>
        </Layer>

        <Layer>
          <Tile>
            <h3 style={{ marginBottom: '1rem' }}>Supported Languages</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
              <Tag type="blue">English</Tag>
              <Tag type="gray">Spanish</Tag>
              <Tag type="gray">French</Tag>
              <Tag type="gray">German</Tag>
              <Tag type="gray">Japanese</Tag>
              <Tag type="gray">Korean</Tag>
              <Tag type="gray">Chinese</Tag>
              <Tag type="gray">Arabic</Tag>
            </div>
          </Tile>
        </Layer>
      </div>

      <Layer>
        <Tile>
          <h3 style={{ marginBottom: '1rem' }}>Recent Translation Jobs</h3>
          <StructuredListWrapper>
            <StructuredListHead>
              <StructuredListRow head>
                <StructuredListCell head>Source</StructuredListCell>
                <StructuredListCell head>Target Languages</StructuredListCell>
                <StructuredListCell head>Status</StructuredListCell>
                <StructuredListCell head>Progress</StructuredListCell>
                <StructuredListCell head>Date</StructuredListCell>
              </StructuredListRow>
            </StructuredListHead>
            <StructuredListBody>
              {recentJobs.map((job) => (
                <StructuredListRow key={job.id}>
                  <StructuredListCell>{job.source}</StructuredListCell>
                  <StructuredListCell>
                    {job.targets.map((lang) => (
                      <Tag key={lang} type="outline" size="sm" style={{ marginRight: '0.25rem' }}>
                        {lang}
                      </Tag>
                    ))}
                  </StructuredListCell>
                  <StructuredListCell>
                    <Tag type={statusConfig[job.status as keyof typeof statusConfig].type}>
                      {statusConfig[job.status as keyof typeof statusConfig].label}
                    </Tag>
                  </StructuredListCell>
                  <StructuredListCell>{job.progress}%</StructuredListCell>
                  <StructuredListCell>{job.date}</StructuredListCell>
                </StructuredListRow>
              ))}
            </StructuredListBody>
          </StructuredListWrapper>
        </Tile>
      </Layer>
    </div>
  );
}