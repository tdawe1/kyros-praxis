'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';

type NavLinkProps = {
  href: string;
  children: ReactNode;
  className: string;
  activeClassName?: string;
  exact?: boolean;
};

export function NavLink({
  href,
  children,
  className,
  activeClassName = '',
  exact = false,
}: NavLinkProps) {
  const pathname = usePathname();
  const isActive = exact ? pathname === href : pathname.startsWith(href);
  const composedClassName = [className, isActive ? activeClassName : null]
    .filter(Boolean)
    .join(' ');

  return (
    <Link href={href} className={composedClassName}>
      {children}
    </Link>
  );
}

