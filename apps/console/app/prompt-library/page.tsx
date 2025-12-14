'use client';

import { Card } from '@shared/ui/components';

export default function PromptLibraryPage() {
  return (
    <main className="placeholder-page">
      <Card variant="muted" density="compact">
        <span className="dashboard-eyebrow">Coming Soon</span>
        <h1>Prompt Library</h1>
        <p>
          Centralized prompt management and versioning will appear here. For now, continue to store
          run prompts in the planner or your own repositories.
        </p>
      </Card>
    </main>
  );
}

