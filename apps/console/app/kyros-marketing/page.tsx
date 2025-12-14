'use client';

import { Card } from '@shared/ui/components';

export default function KyrosMarketingPage() {
  return (
    <main className="placeholder-page">
      <div className="placeholder-grid">
        <Card variant="muted" density="compact" className="placeholder-card">
          <span className="dashboard-eyebrow">Kyros Marketing</span>
          <h2>Analytics & Attribution</h2>
          <p>
            Track campaign health, attribution models, and experiment performance across channels. This
            dashboard will centralise marketing ops once launched.
          </p>
        </Card>
        <Card variant="muted" density="compact" className="placeholder-card">
          <h2>Roadmap</h2>
          <p>
            Until the marketing suite is live, use existing BI tooling or integrate analytics agents via
            the planner to gather insights.\n          </p>
        </Card>
      </div>
    </main>
  );
}
