'use client';

import type { ReactNode } from 'react';

import { NavLink } from './nav-link';

export function NavigationTabs() {
  const primaryLinks: Array<{ href: string; label: string; exact?: boolean }> = [
    { href: '/landing', label: 'kyros.Nexus' },
    { href: '/', label: 'Dashboard', exact: true },
    { href: '/planner', label: 'Planner' },
    { href: '/terminal', label: 'Terminal' },
  ];

  return (
    <>
      {primaryLinks.map(({ href, label, exact }) => (
        <NavLink key={href} href={href} className="topbar-tab" activeClassName="topbar-tab--active" exact={exact}>
          {label}
        </NavLink>
      ))}
    </>
  );
}

type SidebarNavLinkProps = {
  href: string;
  exact?: boolean;
  children: ReactNode;
  collapsed: boolean;
};

export function SidebarNavLink({ href, exact, children, collapsed }: SidebarNavLinkProps) {
  return (
    <NavLink
      href={href}
      exact={exact}
      className={`sidebar-link ${collapsed ? 'sidebar-link--icon' : ''}`}
      activeClassName="sidebar-link--active"
    >
      <span aria-hidden className="sidebar-link-indicator">
        •
      </span>
      {!collapsed ? children : <span className="sr-only">{children}</span>}
    </NavLink>
  );
}
