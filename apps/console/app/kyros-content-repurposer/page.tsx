'use client';

import { Card } from '@shared/ui/components';

export default function KyrosContentRepurposerPage() {
  return (
    <main className="placeholder-page">
      <div className="placeholder-grid">
        <Card variant="muted" density="compact" className="placeholder-card">
          <span className="dashboard-eyebrow">Kyros Content Repurposer</span>
          <h2>Multichannel Prompt Repurposing</h2>
          <p>
            Generate tailored prompt variants for each social platform and tone. This workspace will
            streamline marketing campaign reuse.
          </p>
        </Card>
        <Card variant="muted" density="compact" className="placeholder-card">
          <h2>Preview</h2>
          <p>
            Repurpose prompts manually today or lean on planner crews while this dedicated interface
            ships in an upcoming milestone.
          </p>
        </Card>
      </div>
    </main>
  );
}
