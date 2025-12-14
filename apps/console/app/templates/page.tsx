'use client';

import { Card } from '@shared/ui/components';

export default function TemplatesPage() {
  return (
    <main className="placeholder-page">
      <Card variant="muted" density="compact">
        <span className="dashboard-eyebrow">Coming Soon</span>
        <h1>Templates</h1>
        <p>
          Saved run templates and reusable orchestrations will be available here. Keep an eye on the
          release notes for updates.
        </p>
      </Card>
    </main>
  );
}

