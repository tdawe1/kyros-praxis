import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import GitHub from "next-auth/providers/github";

const rawApi = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const authBase = process.env.NEXT_PUBLIC_AUTH_URL || rawApi.replace(/\/api\/v1\/?$/, '');

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    GitHub({
      clientId: process.env.GITHUB_CLIENT_ID,
      clientSecret: process.env.GITHUB_CLIENT_SECRET,
    }),
    Credentials({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      // Real authentication against orchestrator API
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          // Dev bypass: authenticate with orchestrator in dev mode
          if (
            process.env.NEXT_PUBLIC_ALLOW_DEV_LOGIN === 'true' ||
            process.env.ALLOW_DEV_LOGIN === '1'
          ) {
            // For dev mode, use a test user account
            const devCredentials = {
              username: 'user@example.com',
              password: 'password'
            };

            const res = await fetch(`${authBase}/auth/login`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(devCredentials),
            });

            if (!res.ok) {
              console.error('Dev login failed:', await res.text());
              return null;
            }

            const data = await res.json();
            if (!data.access_token) {
              console.error('No access token in dev login response');
              return null;
            }

            return {
              id: devCredentials.username,
              name: devCredentials.username,
              email: devCredentials.username,
              accessToken: data.access_token
            } as any;
          }

          const rawApi = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
          const authBase = process.env.NEXT_PUBLIC_AUTH_URL || rawApi.replace(/\/api\/v1\/?$/, '');
          const res = await fetch(`${authBase}/auth/login`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              username: credentials.email,
              password: credentials.password,
            }),
          });

          if (!res.ok) {
            return null;
          }

          const data = await res.json();
          if (!data.access_token) {
            return null;
          }

          // Store the token in the session
          return { 
            id: credentials.email, 
            name: credentials.email, 
            email: credentials.email,
            accessToken: data.access_token
          } as any;
        } catch (error) {
          console.error("Authentication error:", error);
          return null;
        }
      },
    }),
  ],
  session: { 
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET,
  cookies: {
    sessionToken: {
      name: process.env.NODE_ENV === "production" ? '__Secure-next-auth.session-token' : 'next-auth.session-token',
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === "production",
      },
    },
  },
  pages: {
    signIn: "/auth/login",
  },
  callbacks: {
    async jwt({ token, user, account }) {
      if (user) {
        token.accessToken = (user as any).accessToken;
        if (account?.provider === "google" || account?.provider === "github") {
          // For OAuth providers, use the provider's access token
          token.accessToken = account.access_token;
          token.provider = account.provider;
        }
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      session.provider = token.provider as string;
      return session;
    },
    async signIn({ user, account, profile }) {
      // Allow OAuth sign-ins and credential sign-ins
      return true;
    },
  },
});
