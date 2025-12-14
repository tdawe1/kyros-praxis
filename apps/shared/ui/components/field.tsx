'use client';

import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react';
import { forwardRef } from 'react';

import styles from './field.module.css';

const joinClassName = (...tokens: Array<string | false | null | undefined>) =>
  tokens.filter(Boolean).join(' ');

type FieldProps = {
  label: string;
  htmlFor?: string;
  helpText?: string;
  className?: string;
  children: ReactNode;
};

export function Field({ label, htmlFor, helpText, className, children }: FieldProps) {
  return (
    <div className={joinClassName(styles.root, className)}>
      <label className={styles.label} htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {helpText ? <p className={styles.help}>{helpText}</p> : null}
    </div>
  );
}

type TextInputProps = InputHTMLAttributes<HTMLInputElement> & {
  invalid?: boolean;
};

export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(
  ({ className, invalid = false, ...rest }, ref) => (
    <input
      ref={ref}
      className={joinClassName(styles.input, invalid && styles.invalid, className)}
      {...rest}
    />
  ),
);

TextInput.displayName = 'TextInput';

type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  invalid?: boolean;
};

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ className, invalid = false, ...rest }, ref) => (
    <textarea
      ref={ref}
      className={joinClassName(styles.input, invalid && styles.invalid, className)}
      {...rest}
    />
  ),
);

TextArea.displayName = 'TextArea';
