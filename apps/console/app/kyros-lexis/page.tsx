'use client';

import { Card } from '@shared/ui/components';

export default function KyrosLexisPage() {
  return (
    <main className="placeholder-page">
      <div className="placeholder-grid">
        <Card variant="muted" density="compact" className="placeholder-card">
          <span className="dashboard-eyebrow">Kyros Lexis</span>
          <h2>Translation Workspace</h2>
          <p>
            Coordinate localisation projects, translation memories, and automated QA flows here once the
            Lexis module rolls out.
          </p>
        </Card>
        <Card variant="muted" density="compact" className="placeholder-card">
          <h2>In the meantime</h2>
          <p>
            Continue launching crews via the planner or configure the terminal for translation feeds while
            the dedicated interface is in development.
          </p>
        </Card>
      </div>
    </main>
  );
}
