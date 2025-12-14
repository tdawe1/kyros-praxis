'use client';

import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { forwardRef } from 'react';

import styles from './button.module.css';

type ButtonVariant = 'solid' | 'ghost' | 'danger';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  leadingIcon?: ReactNode;
  trailingIcon?: ReactNode;
  loading?: boolean;
  loadingLabel?: string;
};

const joinClassName = (...tokens: Array<string | false | null | undefined>) =>
  tokens.filter(Boolean).join(' ');

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'solid',
      leadingIcon,
      trailingIcon,
      loading = false,
      className,
      children,
      disabled,
      loadingLabel,
      ...rest
    },
    ref,
  ) => {
    const composedClassName = joinClassName(
      styles.root,
      styles[variant],
      loading && styles.loading,
      className,
    );

    return (
      <button ref={ref} className={composedClassName} disabled={disabled || loading} {...rest}>
        {leadingIcon ? <span aria-hidden>{leadingIcon}</span> : null}
        <span>{loading ? loadingLabel ?? 'Loading…' : children}</span>
        {trailingIcon ? <span aria-hidden>{trailingIcon}</span> : null}
      </button>
    );
  },
);

Button.displayName = 'Button';
