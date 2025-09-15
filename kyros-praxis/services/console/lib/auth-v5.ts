import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

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
          // Dev bypass: allow local login without backend when enabled
          if (
            process.env.NEXT_PUBLIC_ALLOW_DEV_LOGIN === 'true' ||
            process.env.ALLOW_DEV_LOGIN === '1'
          ) {
            return {
              id: credentials.email,
              name: credentials.email,
              email: credentials.email,
              accessToken: 'dev-token-' + Math.random().toString(36).slice(2),
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
  session: { strategy: "jwt" },
  secret: process.env.NEXTAUTH_SECRET,
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
