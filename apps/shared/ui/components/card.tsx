'use client';

import type { HTMLAttributes, ReactNode } from 'react';
import { forwardRef } from 'react';

import styles from './card.module.css';

type CardVariant = 'default' | 'muted';
type CardDensity = 'default' | 'compact';

type CardProps = HTMLAttributes<HTMLDivElement> & {
  variant?: CardVariant;
  density?: CardDensity;
  header?: ReactNode;
  accessory?: ReactNode;
};

const joinClassName = (...tokens: Array<string | false | null | undefined>) =>
  tokens.filter(Boolean).join(' ');

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ children, className, variant = 'default', density = 'default', header, accessory, ...rest }, ref) => {
    const cardClassName = joinClassName(
      styles.root,
      variant !== 'default' && styles[variant],
      density !== 'default' && styles[density],
      className,
    );

    return (
      <section ref={ref} className={cardClassName} {...rest}>
        {header || accessory ? (
          <header className={styles.header}>
            {typeof header === 'string' ? <h2 className={styles.title}>{header}</h2> : header}
            {accessory ?? null}
          </header>
        ) : null}
        {children}
      </section>
    );
  },
);

Card.displayName = 'Card';
