import './globals.css';

import Link from 'next/link';
import type { Metadata } from 'next';

import { NavigationTabs } from './components/navigation-tabs';
import { SidebarShell } from './components/sidebar-shell';
import { ProtectedProviders } from './providers';

export const metadata: Metadata = {
  title: 'Kyros Praxis Console',
  description: 'Launch CrewAI runs and follow their progress.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <ProtectedProviders>
          <div className="app-shell">
            <header className="topbar">
              <div className="topbar-left">
                <Link className="topbar-logo" href="/">
                  Kyros
                </Link>
                <nav className="topbar-tabs" aria-label="Primary">
                  <NavigationTabs />
                </nav>
              </div>
              <div className="topbar-search">
                <input type="search" placeholder="Search (⌘ + K)" aria-label="Search Kyros" />
              </div>
              <div className="topbar-actions">
                <button type="button">Notifications</button>
                <button type="button">Settings</button>
                <button type="button" className="topbar-avatar" aria-label="Account menu">
                  TD
                </button>
              </div>
            </header>
            <SidebarShell>{children}</SidebarShell>
          </div>
        </ProtectedProviders>
      </body>
    </html>
  );
}
