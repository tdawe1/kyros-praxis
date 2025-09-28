"use client";

import { FormEvent, useState } from "react";
import { signIn, getSession } from "next-auth/react";
import { useRouter } from "next/navigation";

export default function AuthPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (!res || res.error) {
        setError("Invalid email or password");
        return;
      }
      // Load session and persist token for API fallback
      const session = await getSession();
      if (session?.accessToken) {
        try { localStorage.setItem('token', String(session.accessToken)); } catch {}
      }

      const target = process.env.NEXT_PUBLIC_POST_LOGIN_ROUTE || "/agents";
      router.replace(target);
    } catch (err) {
      setError("Sign in failed");
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthSignIn = async (provider: string) => {
    setOauthLoading(provider);
    setError(null);
    try {
      await signIn(provider, {
        callbackUrl: process.env.NEXT_PUBLIC_POST_LOGIN_ROUTE || "/agents",
      });
    } catch (err) {
      setError(`${provider} sign in failed`);
    } finally {
      setOauthLoading(null);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-sm border rounded-md p-6 shadow-sm">
        <h1 className="text-xl font-semibold mb-4">Sign in</h1>
        
        {/* OAuth Login Options */}
        <div className="space-y-3 mb-6">
          <button
            onClick={() => handleOAuthSignIn("google")}
            disabled={oauthLoading !== null}
            className="w-full flex items-center justify-center gap-3 bg-white border border-gray-300 rounded py-2 px-4 hover:bg-gray-50 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {oauthLoading === "google" ? (
              <span className="text-sm">Signing in...</span>
            ) : (
              <>
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span className="text-sm font-medium text-gray-700">Continue with Google</span>
              </>
            )}
          </button>

          <button
            onClick={() => handleOAuthSignIn("github")}
            disabled={oauthLoading !== null}
            className="w-full flex items-center justify-center gap-3 bg-gray-900 text-white rounded py-2 px-4 hover:bg-gray-800 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {oauthLoading === "github" ? (
              <span className="text-sm">Signing in...</span>
            ) : (
              <>
                <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                <span className="text-sm font-medium">Continue with GitHub</span>
              </>
            )}
          </button>
        </div>

        {/* Divider */}
        <div className="relative mb-6">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-gray-500">Or continue with email</span>
          </div>
        </div>

        {/* Credentials Form */}
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
            disabled={loading || oauthLoading !== null}
            className="w-full bg-black text-white rounded py-2 disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </main>
  );
}
