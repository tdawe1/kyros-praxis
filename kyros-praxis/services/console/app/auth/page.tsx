"use client";

import { FormEvent, useState, useEffect } from "react";
import { signIn, getSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { auditAuth, AuditEventType } from "../lib/audit";

export default function AuthPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attemptCount, setAttemptCount] = useState(0);

  // Log page visit
  useEffect(() => {
    auditAuth(
      AuditEventType.PAGE_VIEW,
      undefined,
      undefined,
      true,
      undefined,
      { page: 'auth', action: 'view' }
    );
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    const newAttemptCount = attemptCount + 1;
    setAttemptCount(newAttemptCount);

    try {
      // Log login attempt
      await auditAuth(
        AuditEventType.LOGIN_ATTEMPT,
        undefined,
        email,
        true,
        undefined,
        { 
          attemptNumber: newAttemptCount,
          timestamp: new Date().toISOString(),
        }
      );

      const res = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (!res || res.error) {
        // Log failed login
        await auditAuth(
          AuditEventType.LOGIN_FAILURE,
          undefined,
          email,
          false,
          "Invalid credentials",
          { 
            attemptNumber: newAttemptCount,
            errorType: 'invalid_credentials',
            timestamp: new Date().toISOString(),
          }
        );
        
        setError("Invalid email or password");
        return;
      }

      // Load session and persist token for API fallback
      const session = await getSession();
      if (session && 'accessToken' in session && session.accessToken) {
        try { localStorage.setItem('token', String(session.accessToken)); } catch {}
      }

      // Log successful login
      await auditAuth(
        AuditEventType.LOGIN_SUCCESS,
        session?.user?.id || session?.user?.email || undefined,
        email,
        true,
        undefined,
        { 
          attemptNumber: newAttemptCount,
          sessionId: session?.user?.id || session?.user?.email,
          timestamp: new Date().toISOString(),
        }
      );

      const target = process.env.NEXT_PUBLIC_POST_LOGIN_ROUTE || "/agents";
      router.replace(target);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Sign in failed";
      
      // Log login error
      await auditAuth(
        AuditEventType.LOGIN_FAILURE,
        undefined,
        email,
        false,
        errorMessage,
        { 
          attemptNumber: newAttemptCount,
          errorType: 'system_error',
          timestamp: new Date().toISOString(),
        }
      );
      
      setError("Sign in failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm border rounded-md p-6 shadow-sm">
        <h1 className="text-xl font-semibold mb-4">Sign in</h1>
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="flex flex-col gap-1">
            <label htmlFor="email" className="text-sm">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="border rounded px-3 py-2"
              placeholder="you@example.com"
              required
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="password" className="text-sm">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="border rounded px-3 py-2"
              placeholder="••••••••"
              required
            />
          </div>
          {error && (
            <p className="text-red-600 text-sm" role="alert">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-black text-white rounded py-2 disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </main>
  );
}
