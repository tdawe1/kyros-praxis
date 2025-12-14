import { act, render, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { API_BASE } from '../lib/api';
import { AuthProvider, useAuth } from './auth-context';

const mockUser = {
  id: 'user-1',
  username: 'ops-lead',
  email: 'ops@example.com',
  role: 'operator',
  active: true,
  created_at: '2024-01-01T00:00:00Z',
};

const renderAuth = () => {
  let context: ReturnType<typeof useAuth> | null = null;

  const Consumer = () => {
    context = useAuth();
    return null;
  };

  render(
    <AuthProvider>
      <Consumer />
    </AuthProvider>,
  );

  if (!context) {
    throw new Error('Auth context failed to initialise');
  }

  return () => context!;
};

describe('AuthProvider', () => {
  const cookieStore = new Map<string, string>();

  const serialiseCookies = () =>
    Array.from(cookieStore.entries())
      .map(([name, value]) => `${name}=${value}`)
      .join('; ');

  const resetCookieMock = () => {
    cookieStore.clear();
    delete (document as { cookie?: string }).cookie;
    Object.defineProperty(document, 'cookie', {
      configurable: true,
      get: () => serialiseCookies(),
      set: (value: string) => {
        if (!value) {
          return;
        }
        const [cookiePair] = value.split(';');
        const [rawName, ...rest] = cookiePair.split('=');
        if (!rawName) {
          return;
        }
        const name = rawName.trim();
        const cookieValue = rest.join('=').trim();
        cookieStore.set(name, cookieValue);
      },
    });
  };

  const setServerCookie = (name: string, value: string) => {
    cookieStore.set(name, value);
  };

  const clearServerCookie = (name: string) => {
    cookieStore.delete(name);
  };

  const originalLocation = window.location;
  let replaceSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    resetCookieMock();
    replaceSpy = vi.fn();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ancestorOrigins: originalLocation.ancestorOrigins,
        assign: vi.fn(),
        hash: originalLocation.hash,
        host: originalLocation.host,
        hostname: originalLocation.hostname,
        href: originalLocation.href,
        origin: originalLocation.origin,
        pathname: originalLocation.pathname,
        port: originalLocation.port,
        protocol: originalLocation.protocol,
        reload: vi.fn(),
        replace: replaceSpy,
        search: originalLocation.search,
        toString: () => originalLocation.toString(),
      } as unknown as Location,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    cookieStore.clear();
    delete (document as { cookie?: string }).cookie;
  });

  it('fetches the current user when a session cookie is present', async () => {
    setServerCookie('session', 'existing-session');

    const fetchMock = vi.fn<typeof fetch>();
    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (input === `${API_BASE}/auth/me`) {
        expect(init?.credentials).toBe('include');
        return new Response(JSON.stringify(mockUser), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      throw new Error(`Unexpected fetch call: ${String(input)}`);
    });

    vi.stubGlobal('fetch', fetchMock);

    const getContext = renderAuth();

    await waitFor(() => {
      expect(getContext().user).toEqual(mockUser);
      expect(getContext().token).toBe('cookie-auth');
      expect(getContext().isAuthenticated).toBe(true);
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('logs in using cookie-based auth and fetches the user profile', async () => {
    let sessionActive = false;

    const fetchMock = vi.fn<typeof fetch>();
    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (input === `${API_BASE}/auth/me`) {
        if (!sessionActive) {
          expect(init?.credentials).toBe('include');
          return new Response(null, { status: 401 });
        }

        return new Response(JSON.stringify(mockUser), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      if (input === `${API_BASE}/auth/login`) {
        expect(init?.credentials).toBe('include');
        expect(init?.method).toBe('POST');
        const parsedBody = JSON.parse(init?.body as string);
        expect(parsedBody).toEqual({
          email: 'ops@example.com',
          password: 'super-secret',
        });

        sessionActive = true;
        setServerCookie('session', 'new-session');

        return new Response(null, { status: 200 });
      }

      throw new Error(`Unexpected fetch call: ${String(input)}`);
    });

    vi.stubGlobal('fetch', fetchMock);

    const getContext = renderAuth();

    await waitFor(() => {
      const loginCall = fetchMock.mock.calls.find(([url]) => url === `${API_BASE}/auth/me`);
      expect(loginCall?.[1]?.credentials).toBe('include');
    });

    await act(async () => {
      await getContext().login('ops@example.com', 'super-secret');
    });

    await waitFor(() => {
      expect(getContext().user).toEqual(mockUser);
      expect(getContext().isAuthenticated).toBe(true);
    });

    expect(document.cookie).toContain('session=new-session');
    expect(replaceSpy).toHaveBeenCalledWith('/landing');

    const profileCall = fetchMock.mock.calls
      .filter(([url]) => url === `${API_BASE}/auth/me`)
      .pop();
    expect(profileCall?.[1]?.credentials).toBe('include');
  });

  it('logs out and clears the session', async () => {
    let sessionActive = true;
    setServerCookie('session', 'existing-session');

    const fetchMock = vi.fn<typeof fetch>();
    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (input === `${API_BASE}/auth/me`) {
        if (!sessionActive) {
          return new Response(null, { status: 401 });
        }

        return new Response(JSON.stringify(mockUser), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      if (input === `${API_BASE}/auth/logout`) {
        expect(init?.credentials).toBe('include');
        expect(init?.method).toBe('POST');
        sessionActive = false;
        clearServerCookie('session');
        return new Response(null, { status: 200 });
      }

      throw new Error(`Unexpected fetch call: ${String(input)}`);
    });

    vi.stubGlobal('fetch', fetchMock);

    const getContext = renderAuth();

    await waitFor(() => {
      expect(getContext().user).toEqual(mockUser);
      expect(getContext().isAuthenticated).toBe(true);
    });

    await act(async () => {
      await getContext().logout();
    });

    await waitFor(() => {
      expect(getContext().user).toBeNull();
      expect(getContext().token).toBeNull();
      expect(getContext().isAuthenticated).toBe(false);
    });

    expect(document.cookie).not.toContain('session=');

    const logoutCall = fetchMock.mock.calls.find(([url]) => url === `${API_BASE}/auth/logout`);
    expect(logoutCall?.[1]?.credentials).toBe('include');
  });

  it('surfaces API validation errors on failed login', async () => {
    const fetchMock = vi.fn<typeof fetch>();
    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      if (input === `${API_BASE}/auth/me`) {
        expect(init?.credentials).toBe('include');
        return new Response(null, { status: 401 });
      }

      if (input === `${API_BASE}/auth/login`) {
        expect(init?.credentials).toBe('include');
        return new Response(JSON.stringify({ detail: 'invalid credentials' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      throw new Error(`Unexpected fetch call: ${String(input)}`);
    });

    vi.stubGlobal('fetch', fetchMock);

    const getContext = renderAuth();

    await expect(
      act(async () => {
        await getContext().login('ops@example.com', 'bad-password');
      }),
    ).rejects.toThrow('invalid credentials');

    expect(getContext().user).toBeNull();
    expect(document.cookie).toBe('');
    expect(replaceSpy).not.toHaveBeenCalled();
  });
});
