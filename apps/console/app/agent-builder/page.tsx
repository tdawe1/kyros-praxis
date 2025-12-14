'use client';

import { Card } from '@shared/ui/components';

export default function AgentBuilderPage() {
  return (
    <main className="placeholder-page">
      <div className="placeholder-grid">
        <Card variant="muted" density="compact" className="placeholder-card">
          <span className="dashboard-eyebrow">Kyros Agent Builder</span>
          <h2>Blueprint Designer</h2>
          <p>
            Configure multi-agent crews, route tool access, and stage deployment bundles from a single
            visual workspace. This module will unlock end-to-end agent lifecycle management.
          </p>
        </Card>
        <Card variant="muted" density="compact" className="placeholder-card">
          <h2>Get ready</h2>
          <p>
            Use the planner to launch existing crews today, or review the roadmap to see when live
            editing and agent versioning land in this space.
          </p>
        </Card>
      </div>
    </main>
  );
}
