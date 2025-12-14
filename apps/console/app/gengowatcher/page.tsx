'use client';

import { Card } from '@shared/ui/components';

export default function GengoWatcherPage() {
  return (
    <main className="placeholder-page">
      <div className="placeholder-grid">
        <Card variant="muted" density="compact" className="placeholder-card">
          <span className="dashboard-eyebrow">GengoWatcher</span>
          <h2>Job Feed Monitor</h2>
          <p>
            Review job queues, configure auto-accept rules, and manage translators. Integration work is
            underway to surface live data in this console.
          </p>
        </Card>
        <Card variant="muted" density="compact" className="placeholder-card">
          <h2>Current status</h2>
          <p>
            Use the terminal module for manual job commands until the dedicated monitoring UI is ready.
          </p>
        </Card>
      </div>
    </main>
  );
}
