'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';

import { Button, Card, Field, TextInput } from '@shared/ui/components';

import { useAuth } from '../state/auth-context';

export default function LoginPage() {
  const { login, isLoading, isAuthenticated } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to sign in.';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <Card variant="muted" density="compact" className="auth-card">
        <div className="auth-header">
          <span className="dashboard-eyebrow">kyros.Nexus</span>
          <h1>Sign in to continue</h1>
          <p>
            Authenticate with your operator credentials to access the console, planner, and terminal.
          </p>
        </div>

        {/* Auth status indicator for debugging bootstrap state */}
        <div aria-live="polite" className="auth-status" style={{ marginBottom: '0.75rem', color: '#666', fontSize: '0.9rem' }}>
          {isLoading && <span>Checking session…</span>}
          {!isLoading && isAuthenticated && <span>Session found. Redirecting…</span>}
          {!isLoading && !isAuthenticated && <span>Not signed in.</span>}
        </div>

        <form className="form" onSubmit={handleSubmit}>
          <Field label="Email">
            <TextInput
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
              autoComplete="email"
              required
            />
          </Field>

          <Field label="Password">
            <TextInput
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </Field>

          {error ? <p className="error">{error}</p> : null}

          <Button type="submit" loading={isSubmitting || isLoading} loadingLabel="Signing in…">
            Sign in
          </Button>
        </form>

        <p className="auth-footnote">
          Need access? Contact your workspace administrator or{' '}
          <Link href="/signup" className="auth-link">
            create an account
          </Link>{' '}
          if self-service is enabled.
        </p>
      </Card>
    </main>
  );
}
