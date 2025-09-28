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

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [isSideNavExpanded, setIsSideNavExpanded] = useState(false);
  const pathname = usePathname();

  const navigationItems = [
    {
      title: 'Agents',
      href: '/agents',
      icon: Bot,
      items: [
        { title: 'All Agents', href: '/agents' },
        { title: 'Create Agent', href: '/agents/new' },
        { title: 'Templates', href: '/agents/templates' },
      ],
    },
    {
      title: 'Super',
      href: '/super',
      icon: Terminal,
    },
    {
      title: 'Translations',
      href: '/translations',
      icon: Translate,
    },
    {
      title: 'Quotes',
      href: '/quotes',
      icon: Currency,
    },
    {
      title: 'Inventory',
      href: '/inventory',
      icon: ShoppingCart,
    },
    {
      title: 'Marketing',
      href: '/marketing',
      icon: ChartLine,
    },
    {
      title: 'Remote',
      href: '/remote',
      icon: Terminal,
    },
    {
      title: 'Assistant',
      href: '/assistant',
      icon: Bot,
    },
    {
      title: 'Settings',
      href: '/settings',
      icon: Settings,
      items: [
        { title: 'Organization', href: '/settings/organization' },
        { title: 'Users & Roles', href: '/settings/users' },
        { title: 'Connectors', href: '/settings/connectors' },
        { title: 'Feature Flags', href: '/settings/features' },
      ],
    },
    {
      title: 'System',
      href: '/system',
      icon: Dashboard,
      items: [
        { title: 'Jobs Queue', href: '/system/jobs' },
        { title: 'Webhooks', href: '/system/webhooks' },
        { title: 'Audit Log', href: '/system/audit' },
        { title: 'Review Plan', href: '/review-plan' },
      ],
    },
  ];

  const isActive = (href: string) => pathname.startsWith(href);

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
              <HeaderMenuItem as={Link} href="/agents" isActive={isActive('/agents')}>
                Agents
              </HeaderMenuItem>
              <HeaderMenuItem as={Link} href="/translations" isActive={isActive('/translations')}>
                Translations
              </HeaderMenuItem>
              <HeaderMenuItem as={Link} href="/inventory" isActive={isActive('/inventory')}>
                Inventory
              </HeaderMenuItem>
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
                  {navigationItems.map((item) => {
                    const Icon = item.icon;
                    if (item.items) {
                      return (
                        <SideNavMenu
                          key={item.href}
                          renderIcon={Icon}
                          title={item.title}
                          isActive={isActive(item.href)}
                        >
                          {item.items.map((subItem) => (
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
