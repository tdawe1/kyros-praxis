import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";

const handler = NextAuth({
  providers: [
    Credentials({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        try {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: credentials?.email,
              password: credentials?.password,
            }),
          });

          if (!response.ok) {
            return null;
          }

          const data = await response.json();
          const token = data.access_token;

          // Decode token to get user info
// Add at top of file:
import jwt from 'jsonwebtoken';

// Verify and decode token properly
const decoded = jwt.verify(token, process.env.JWT_SECRET as string) as any;
          return {
            id: decoded.sub,
            name: decoded.name || decoded.email,
            email: decoded.email,
            token: token,
          } as any;
        } catch (error) {
          console.error('Authentication error:', error);
          return null;
        }
      },
    }),
  ],
  session: { strategy: "jwt" },
  secret: process.env.NEXTAUTH_SECRET,
});

export { handler as GET, handler as POST };

