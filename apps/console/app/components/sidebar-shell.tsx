'use client';

import { useState } from 'react';
import type { ReactNode } from 'react';

import { SidebarNavLink } from './navigation-tabs';

export function SidebarShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`shell-body ${collapsed ? 'shell-body--collapsed' : ''}`}>
      <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`} aria-label="Workspace navigation">
        <div className="sidebar-header">
          <button
            type="button"
            className="sidebar-toggle"
            aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
            onClick={() => setCollapsed((value) => !value)}
          >
            <span aria-hidden>{collapsed ? '»' : '«'}</span>
          </button>
        </div>

        <div className="sidebar-section">
          {!collapsed ? <p className="sidebar-heading">Workspace</p> : null}
          <nav>
            <SidebarNavLink href="/landing" collapsed={collapsed}>
              kyros.Nexus
            </SidebarNavLink>
            <SidebarNavLink href="/" exact collapsed={collapsed}>
              Dashboard
            </SidebarNavLink>
            <SidebarNavLink href="/planner" collapsed={collapsed}>
              Planner
            </SidebarNavLink>
            <SidebarNavLink href="/terminal" collapsed={collapsed}>
              Terminal
            </SidebarNavLink>
            <SidebarNavLink href="/agent-builder" collapsed={collapsed}>
              Agent Builder
            </SidebarNavLink>
            <SidebarNavLink href="/prompt-library" collapsed={collapsed}>
              Prompt Library
            </SidebarNavLink>
            <SidebarNavLink href="/templates" collapsed={collapsed}>
              Templates
            </SidebarNavLink>
          </nav>
        </div>

        <div className="sidebar-section">
          {!collapsed ? <p className="sidebar-heading">Tools</p> : null}
          <nav>
            <SidebarNavLink href="/" exact collapsed={collapsed}>
              kyros.Praxis
            </SidebarNavLink>
            <SidebarNavLink href="/kyros-lexis" collapsed={collapsed}>
              kyros.Lexis
            </SidebarNavLink>
            <SidebarNavLink href="/kyros-executive-assistant" collapsed={collapsed}>
              kyros.ExecutiveAssistant
            </SidebarNavLink>
            <SidebarNavLink href="/kyros-marketing" collapsed={collapsed}>
              kyros.Marketing
            </SidebarNavLink>
            <SidebarNavLink href="/gengowatcher" collapsed={collapsed}>
              GengoWatcher
            </SidebarNavLink>
            <SidebarNavLink href="/kyros-content-repurposer" collapsed={collapsed}>
              kyros.ContentRepurposer
            </SidebarNavLink>
          </nav>
        </div>

        <div className="sidebar-footer">
          <button type="button" disabled={collapsed}>
            Invite teammates
          </button>
          <button type="button" disabled={collapsed}>
            Create Space
          </button>
        </div>
      </aside>

      <div className="main-region">{children}</div>
    </div>
  );
}
