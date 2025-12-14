'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useMemo, useState } from 'react';

import { Button, Card, Field, TextInput } from '@shared/ui/components';

import { API_BASE } from './lib/api';
import { useRunManager } from './lib/use-run-manager';
import { resolveEventLabel } from './lib/events';
import { useAuth } from './state/auth-context';

type AuthMode = 'login' | 'register';

export default function HomePage() {
  const { user, token, isAuthenticated, isLoading: isAuthLoading, login, register, logout } =
    useAuth();

  const router = useRouter();

  const { crewId, prompt, run, status, events } = useRunManager(token);

  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authUsername, setAuthUsername] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [isAuthSubmitting, setIsAuthSubmitting] = useState(false);

  const curlSnippet = useMemo(() => {
    const payload = {
      crew_id: crewId || '<crew_id>',
      input: {
        prompt: prompt || '<prompt>',
      },
    };
    const lines = [
      `curl -X POST ${API_BASE}/crews/runs \\`,
      `  -H 'Content-Type: application/json' \\`,
    ];
    if (token) {
      lines.push(`  -H 'Authorization: Bearer <session-token>' \\`);
    }
    lines.push(`  -d '${JSON.stringify(payload, null, 2)}'`);
    return lines.join('\n');
  }, [crewId, prompt, token]);

  const lastEvent = events.length > 0 ? events[events.length - 1] : null;
  const latestMessage = lastEvent?.message ?? null;
  const latestTimestamp = lastEvent?.ts ?? null;
  const sessionMode = token ? 'Authenticated' : 'Anonymous';

  const friendlyTimestamp = useMemo(() => {
    if (!latestTimestamp) {
      return null;
    }
    const parsed = new Date(latestTimestamp);
    if (Number.isNaN(parsed.getTime())) {
      return latestTimestamp;
    }
    return parsed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }, [latestTimestamp]);

  const runStatusLabel = (status ?? 'idle').toUpperCase();

  const dashboardMetrics = useMemo(
    () => [
      {
        label: 'Session',
        value: sessionMode,
        caption: token ? 'Authenticated operator' : 'Guest session active',
      },
      {
        label: 'Run Status',
        value: runStatusLabel,
        caption: status ? `Last update ${friendlyTimestamp ?? latestTimestamp ?? ''}`.trim() : 'Awaiting first dispatch',
      },
      {
        label: 'Events Streamed',
        value: events.length.toString().padStart(2, '0'),
        caption: events.length > 0 ? 'Live telemetry captured' : 'No events received yet',
      },
      {
        label: 'Target Crew',
        value: crewId || '—',
        caption: run?.id ? `Tracking run ${run.id}` : 'Ready for launch',
      },
    ],
    [sessionMode, token, runStatusLabel, status, friendlyTimestamp, latestTimestamp, events.length, crewId, run?.id],
  );

  const activityFeed = useMemo(() => events.slice(-5).reverse(), [events]);

  const operationsSummary = useMemo(
    () => [
      {
        label: 'Current run',
        value: run?.id ?? 'No run in progress',
        description: run ? `Crew ${run.crew_id}` : 'Launch a new crew to begin tracking.',
      },
      {
        label: 'Message stream',
        value: `${events.length} events`,
        description: friendlyTimestamp
          ? `Last event at ${friendlyTimestamp}`
          : 'Awaiting the first event from the orchestrator.',
      },
      {
        label: 'Status',
        value: runStatusLabel,
        description: latestMessage ? `“${latestMessage}”` : 'No recent operator or agent messages.',
      },
    ],
    [run?.id, run?.crew_id, events.length, friendlyTimestamp, runStatusLabel, latestMessage],
  );

  const goToPlanner = useCallback(() => {
    router.push('/planner');
  }, [router]);

  const toggleAuthMode = () => {
    setAuthMode((prev) => (prev === 'login' ? 'register' : 'login'));
    setAuthError(null);
  };

  const handleAuthSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAuthError(null);
    setIsAuthSubmitting(true);

    try {
      if (authMode === 'login') {
        await login(authEmail, authPassword);
      } else {
        await register(authUsername, authEmail, authPassword);
      }

      setAuthEmail('');
      setAuthPassword('');
      setAuthUsername('');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Authentication failed.';
      setAuthError(message);
    } finally {
      setIsAuthSubmitting(false);
    }
  };

  return (
    <main className="dashboard-page">
      <section className="dashboard-header">
        <div className="dashboard-title-block">
          <span className="dashboard-eyebrow">Mission Control</span>
          <h1>Operations Dashboard</h1>
          <p>
            Monitor orchestrator throughput, inspect telemetry, and trigger new crew runs from a single
            command surface.
          </p>
          <div className="dashboard-cta">
            <Button type="button" onClick={goToPlanner}>
              Launch new run
            </Button>
            <Link className="dashboard-cta-link" href="/terminal">
              Open terminal
            </Link>
          </div>
        </div>
        <div className="dashboard-highlight">
          <span className="dashboard-highlight-label">Latest message</span>
          <p className="dashboard-highlight-value">
            {latestMessage ? `“${latestMessage}”` : 'No streaming events yet.'}
          </p>
          <span className="dashboard-highlight-meta">
            {friendlyTimestamp ? `Updated ${friendlyTimestamp}` : 'Awaiting live telemetry'}
          </span>
        </div>
      </section>

      <section className="dashboard-metrics">
        {dashboardMetrics.map((metric) => (
          <Card key={metric.label} variant="muted" density="compact" className="metric-card">
            <span className="metric-label">{metric.label}</span>
            <span className="metric-value">{metric.value}</span>
            <span className="metric-caption">{metric.caption}</span>
          </Card>
        ))}
      </section>

      <section className="dashboard-layout">
        <div className="dashboard-column dashboard-column--primary">
          <Card header="Operational Overview" variant="muted" density="compact" className="dashboard-card">
            <ul className="insights-list">
              {operationsSummary.map((insight) => (
                <li key={insight.label}>
                  <span className="insight-label">{insight.label}</span>
                  <span className="insight-value">{insight.value}</span>
                  <p className="insight-description">{insight.description}</p>
                </li>
              ))}
            </ul>
          </Card>

          <Card header="Recent Activity" className="dashboard-card" density="compact">
            {activityFeed.length === 0 ? (
              <p className="empty">No activity yet. Launch a run to start receiving events.</p>
            ) : (
              <ul className="activity-list">
                {activityFeed.map((event, index) => (
                  <li key={`${event.ts ?? index}-activity`}>
                    <div className="activity-meta">
                      <span>{resolveEventLabel(event)}</span>
                      {event.ts ? <time dateTime={event.ts}>{event.ts}</time> : null}
                    </div>
                    {event.message ? <p className="activity-message">{event.message}</p> : null}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        <aside className="dashboard-column dashboard-column--secondary">
          <Card header="Run Status" variant="muted" density="compact" className="dashboard-card">
            <div className="run-status-grid">
              <div>
                <span className="label-text">Status</span>
                <p className="run-status-value">{runStatusLabel}</p>
              </div>
              <div>
                <span className="label-text">Active Crew</span>
                <p className="run-status-meta">{(run?.crew_id ?? crewId) || '—'}</p>
              </div>
              <div>
                <span className="label-text">Run ID</span>
                <p className="run-status-meta">{run?.id ?? '—'}</p>
              </div>
              <div>
                <span className="label-text">Last Event</span>
                <p className="run-status-meta">
                  {latestMessage ? `“${latestMessage}”` : 'No recent telemetry'}
                </p>
              </div>
            </div>
            <Link href="/planner" className="run-status-link">
              Manage runs in Planner
            </Link>
          </Card>

          <Card header="Account Access" density="compact" className="dashboard-card">
            {isAuthenticated ? (
              <div className="auth-meta">
                <div>
                  <span className="label-text">Signed in as</span>
                  <p className="auth-primary">{user?.username ?? user?.email}</p>
                  <p className="auth-secondary">{user?.email}</p>
                </div>
                <div className="actions">
                  <Button type="button" variant="ghost" onClick={logout}>
                    Sign out
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <p className="auth-intro">
                  Authenticate to attribute runs to your user. Registration is optional but unlocks
                  per-user auditing.
                </p>
                <form className="form" onSubmit={handleAuthSubmit}>
                  {authMode === 'register' ? (
                    <Field label="Username">
                      <TextInput
                        value={authUsername}
                        onChange={(event) => setAuthUsername(event.target.value)}
                        placeholder="operations-lead"
                        autoComplete="username"
                        required
                      />
                    </Field>
                  ) : null}

                  <Field label="Email">
                    <TextInput
                      type="email"
                      value={authEmail}
                      onChange={(event) => setAuthEmail(event.target.value)}
                      placeholder="you@company.com"
                      autoComplete="email"
                      required
                    />
                  </Field>

                  <Field label="Password">
                    <TextInput
                      type="password"
                      value={authPassword}
                      onChange={(event) => setAuthPassword(event.target.value)}
                      placeholder="••••••••"
                      autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
                      required
                    />
                  </Field>

                  {authError ? <p className="error">{authError}</p> : null}

                  <div className="actions">
                    <Button
                      type="submit"
                      loading={isAuthSubmitting}
                      loadingLabel={authMode === 'login' ? 'Signing in…' : 'Creating account…'}
                    >
                      {authMode === 'login' ? 'Sign in' : 'Create account'}
                    </Button>
                    <Button type="button" variant="ghost" onClick={toggleAuthMode}>
                      {authMode === 'login' ? 'Create account' : 'Use existing account'}
                    </Button>
                  </div>
                </form>
                <p className="auth-helper">
                  {isAuthLoading ? 'Checking session…' : 'Tokens persist in local storage until you sign out.'}
                </p>
              </>
            )}
          </Card>

        <Card header="Quick Tools" variant="muted" density="compact" className="dashboard-card">
          <div className="quick-links">
            <div className="quick-link">
              <div>
                <span className="quick-link-title">Open planner</span>
                <p className="quick-link-description">Launch and monitor runs from the dedicated planner workspace.</p>
              </div>
              <Link href="/planner" className="quick-link-action">
                Open
              </Link>
            </div>
            <div className="quick-link">
              <div>
                <span className="quick-link-title">Open terminal</span>
                <p className="quick-link-description">Interact with the multi-agent terminal interface.</p>
              </div>
              <Link href="/terminal" className="quick-link-action">
                Launch
              </Link>
            </div>
              <div className="quick-link">
                <div>
                  <span className="quick-link-title">View API reference</span>
                  <p className="quick-link-description">Review CrewAI endpoints, parameters, and authentication.</p>
                </div>
                <a
                  href="https://factory.ai"
                  target="_blank"
                  rel="noreferrer"
                  className="quick-link-action"
                >
                  Docs
                </a>
              </div>
            </div>
            <div className="quick-snippet">
              <span className="quick-link-title">Sample API call</span>
              <pre>{curlSnippet}</pre>
            </div>
          </Card>

          <Card header="How it works" variant="muted" density="compact" className="dashboard-card support-card">
            <div className="info">
              <ol>
                <li>
                  Start the orchestrator API: <code>cd api && uvicorn app.main:app --reload --port 8001</code>.
                </li>
                <li>
                  Optional: configure <code>NEXT_PUBLIC_API_BASE_URL</code> if the API runs on a different host or port.
                </li>
                <li>
                  Run the console locally: <code>cd console && npm install && npm run dev</code>.
                </li>
              </ol>
            </div>
          </Card>
        </aside>
      </section>
    </main>
  );
}
