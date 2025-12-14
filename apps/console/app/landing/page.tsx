'use client';

import Link from 'next/link';

import { Card } from '@shared/ui/components';

const tools = [
  {
    href: '/',
    title: 'kyros.Praxis',
    description: 'Mission control for orchestrating and monitoring Kyros crews.',
  },
  {
    href: '/kyros-lexis',
    title: 'kyros.Lexis',
    description: 'Translation management and localisation QA.',
  },
  {
    href: '/kyros-executive-assistant',
    title: 'kyros.ExecutiveAssistant',
    description: 'Personal assistant automations for daily workflows.',
  },
  {
    href: '/kyros-marketing',
    title: 'kyros.Marketing',
    description: 'Marketing analytics, attribution, and performance insights.',
  },
  {
    href: '/gengowatcher',
    title: 'GengoWatcher',
    description: 'Monitor translation job feeds with auto-accept logic.',
  },
  {
    href: '/kyros-content-repurposer',
    title: 'kyros.ContentRepurposer',
    description: 'Repurpose prompts for each social media surface.',
  },
];

export default function LandingPage() {
  return (
    <main className="landing-page">
      <section className="landing-hero">
        <span className="dashboard-eyebrow">kyros.Nexus</span>
        <h1>Choose your workspace</h1>
        <p>
          Navigate across Kyros tooling from a single hub. Explore orchestration, translation,
          marketing analytics, and more.
        </p>
      </section>

      <section className="landing-grid">
        {tools.map((tool) => (
          <Card key={tool.href} variant="muted" density="compact" className="landing-card">
            <h2>{tool.title}</h2>
            <p>{tool.description}</p>
            <Link href={tool.href} className="landing-card-link">
              Open
            </Link>
          </Card>
        ))}
      </section>
    </main>
  );
}
