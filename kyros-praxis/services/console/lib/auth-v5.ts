import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import * as jwt from "jsonwebtoken";

// Extend NextAuth types
declare module "next-auth" {
  interface Session {
    accessToken?: string;
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
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
          const rawApi = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
          const authBase = process.env.NEXT_PUBLIC_AUTH_URL || rawApi.replace(/\/api\/v1\/?$/, '');

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
  session: { strategy: "jwt" },
  secret: process.env.NEXTAUTH_SECRET,
  jwt: {
    encode: async ({ secret, token }) => {
      return jwt.sign(token!, secret as string, { algorithm: 'HS512' });
    },
    decode: async ({ secret, token }) => {
      return jwt.verify(token!, secret as string, { algorithms: ['HS512'] }) as any;
    },
  },
  pages: {
    signIn: "/auth/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = (user as any).accessToken;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      return session;
    },
  },
});
