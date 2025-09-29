'use client';

import { ReactNode, useState } from 'react';
import {
  Header,
  HeaderContainer,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
  SideNav,
  SideNavItems,
  SideNavLink,
  SideNavMenu,
  SideNavMenuItem,
  HeaderSideNavItems,
} from '@carbon/react';
import {
  Notification,
  UserAvatar,
  Switcher,
  Help,
  Search,
  Bot,
  Translate,
  Currency,
  ShoppingCart,
  ChartLine,
  Terminal,
  Settings,
  Dashboard,
} from '@carbon/icons-react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { signOut } from 'next-auth/react';
import { useUserRole, useCanAccessResource } from '../../lib/hooks/useUserRole';

interface DashboardLayoutProps {
  children: ReactNode;
}

interface NavigationItem {
  title: string;
  href: string;
  icon: any;
  resource?: string; // For permission checking
  items?: {
    title: string;
    href: string;
    resource?: string;
  }[];
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [isSideNavExpanded, setIsSideNavExpanded] = useState(false);
  const pathname = usePathname();
  const { role } = useUserRole();
  
  // Get permission checks at component level
  const canAccessAgents = useCanAccessResource('agents');
  const canAccessUsers = useCanAccessResource('users');
  const canAccessJobs = useCanAccessResource('jobs');
  const canAccessSystem = useCanAccessResource('system');

  const navigationItems: NavigationItem[] = [
    {
      title: 'Agents',
      href: '/agents',
      icon: Bot,
      resource: 'agents',
      items: [
        { title: 'All Agents', href: '/agents', resource: 'agents' },
        { title: 'Create Agent', href: '/agents/new', resource: 'agents' },
        { title: 'Templates', href: '/agents/templates', resource: 'agents' },
      ],
    },
    {
      title: 'Super',
      href: '/super',
      icon: Terminal,
      resource: 'system',
    },
    {
      title: 'Translations',
      href: '/translations',
      icon: Translate,
      resource: 'agents',
    },
    {
      title: 'Quotes',
      href: '/quotes',
      icon: Currency,
      resource: 'agents',
    },
    {
      title: 'Inventory',
      href: '/inventory',
      icon: ShoppingCart,
      resource: 'agents',
    },
    {
      title: 'Marketing',
      href: '/marketing',
      icon: ChartLine,
      resource: 'agents',
    },
    {
      title: 'Remote',
      href: '/remote',
      icon: Terminal,
      resource: 'system',
    },
    {
      title: 'Assistant',
      href: '/assistant',
      icon: Bot,
      resource: 'agents',
    },
    {
      title: 'Settings',
      href: '/settings',
      icon: Settings,
      resource: 'users',
      items: [
        { title: 'Organization', href: '/settings/organization', resource: 'users' },
        { title: 'Users & Roles', href: '/settings/users', resource: 'users' },
        { title: 'Connectors', href: '/settings/connectors', resource: 'system' },
        { title: 'Feature Flags', href: '/settings/features', resource: 'system' },
      ],
    },
    {
      title: 'System',
      href: '/system',
      icon: Dashboard,
      resource: 'system',
      items: [
        { title: 'Jobs Queue', href: '/system/jobs', resource: 'jobs' },
        { title: 'Webhooks', href: '/system/webhooks', resource: 'system' },
        { title: 'Audit Log', href: '/system/audit', resource: 'system' },
        { title: 'Review Plan', href: '/review-plan', resource: 'system' },
      ],
    },
  ];

  const isActive = (href: string) => pathname.startsWith(href);
  
  // Filter navigation items based on user permissions
  const filteredNavigationItems = navigationItems.filter(item => {
    if (!item.resource) return true;
    switch (item.resource) {
      case 'agents': return canAccessAgents;
      case 'users': return canAccessUsers;
      case 'jobs': return canAccessJobs;
      case 'system': return canAccessSystem;
      default: return true;
    }
  });

  const filterSubItems = (items: NavigationItem['items']) => {
    if (!items) return [];
    return items.filter(item => {
      if (!item.resource) return true;
      switch (item.resource) {
        case 'agents': return canAccessAgents;
        case 'users': return canAccessUsers;
        case 'jobs': return canAccessJobs;
        case 'system': return canAccessSystem;
        default: return true;
      }
    });
  };

  return (
    <>
      <HeaderContainer
        render={({ isSideNavExpanded, onClickSideNavExpand }: any) => (
          <Header aria-label="Kyros Praxis">
            <SkipToContent />
            <HeaderName 
              as={Link} 
              href="/" 
              prefix="Kyros"
            >
              Praxis
            </HeaderName>
            <HeaderNavigation aria-label="Main navigation">
              <HeaderMenuItem as={Link} href="/jobs" isActive={isActive('/jobs')}>
                Jobs
              </HeaderMenuItem>
              {canAccessAgents && (
                <HeaderMenuItem as={Link} href="/agents" isActive={isActive('/agents')}>
                  Agents
                </HeaderMenuItem>
              )}
              {canAccessAgents && (
                <HeaderMenuItem as={Link} href="/translations" isActive={isActive('/translations')}>
                  Translations
                </HeaderMenuItem>
              )}
              {canAccessAgents && (
                <HeaderMenuItem as={Link} href="/inventory" isActive={isActive('/inventory')}>
                  Inventory
                </HeaderMenuItem>
              )}
            </HeaderNavigation>
            <HeaderGlobalBar>
              <HeaderGlobalAction
                aria-label="Search"
                tooltipAlignment="center"
                onClick={() => {
                  // Trigger search modal
                  document.dispatchEvent(new KeyboardEvent('keydown', { key: '/' }));
                }}
              >
                <Search size={20} />
              </HeaderGlobalAction>
              <HeaderGlobalAction
                aria-label="Notifications"
                tooltipAlignment="center"
              >
                <Notification size={20} />
              </HeaderGlobalAction>
              <HeaderGlobalAction
                aria-label="Help"
                tooltipAlignment="center"
              >
                <Help size={20} />
              </HeaderGlobalAction>
              <HeaderGlobalAction
                aria-label="App Switcher"
                tooltipAlignment="center"
              >
                <Switcher size={20} />
              </HeaderGlobalAction>
              <HeaderGlobalAction
                aria-label="Sign out"
                tooltipAlignment="end"
                onClick={() => signOut({ callbackUrl: '/auth/login' })}
                title={`Current role: ${role}`}
              >
                <UserAvatar size={20} />
              </HeaderGlobalAction>
            </HeaderGlobalBar>
            <SideNav
              aria-label="Side navigation"
              expanded={isSideNavExpanded}
              isPersistent={false}
              onOverlayClick={onClickSideNavExpand}
            >
              <SideNavItems>
                <HeaderSideNavItems>
                  {filteredNavigationItems.map((item) => {
                    const Icon = item.icon;
                    const filteredSubItems = filterSubItems(item.items);
                    
                    if (filteredSubItems.length > 0) {
                      return (
                        <SideNavMenu
                          key={item.href}
                          renderIcon={Icon}
                          title={item.title}
                          isActive={isActive(item.href)}
                        >
                          {filteredSubItems.map((subItem) => (
                            <SideNavMenuItem
                              key={subItem.href}
                              as={Link}
                              href={subItem.href}
                              isActive={pathname === subItem.href}
                            >
                              {subItem.title}
                            </SideNavMenuItem>
                          ))}
                        </SideNavMenu>
                      );
                    }
                    
                    return (
                      <SideNavLink
                        key={item.href}
                        renderIcon={Icon}
                        as={Link}
                        href={item.href}
                        isActive={isActive(item.href)}
                      >
                        {item.title}
                      </SideNavLink>
                    );
                  })}
                </HeaderSideNavItems>
              </SideNavItems>
            </SideNav>
          </Header>
        )}
      />
      <main className="cds--content">
        {children}
      </main>
    </>
  );
}
