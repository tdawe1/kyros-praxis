"use client";

import { FormEvent, useState } from "react";
import { signIn, getSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { AuthFormSchema } from "@/lib/validation";
import { sanitizeText } from "@/lib/sanitization";

export default function AuthPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // Validate and sanitize form data
      const formData = { email, password };
      const validation = AuthFormSchema.safeParse(formData);
      
      if (!validation.success) {
        const errorMessages = validation.error.errors.map(e => e.message).join(', ');
        setError(`Input validation failed: ${errorMessages}`);
        return;
      }

      const { email: sanitizedEmail, password: validatedPassword } = validation.data;
      
      const res = await signIn("credentials", {
        email: sanitizedEmail,
        password: validatedPassword,
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
              onChange={(e) => setEmail(e.target.value)} // Let validation handle sanitization
              className="border rounded px-3 py-2"
              placeholder="you@example.com"
              required
              autoComplete="email"
              maxLength={254} // RFC 5321 email length limit
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="password" className="text-sm">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)} // Don't sanitize passwords
              className="border rounded px-3 py-2"
              placeholder="••••••••"
              required
              autoComplete="current-password" 
              maxLength={128} // Reasonable password length limit
            />
          </div>
          {error && (
            <p className="text-red-600 text-sm" role="alert">{sanitizeText(error)}</p>
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
