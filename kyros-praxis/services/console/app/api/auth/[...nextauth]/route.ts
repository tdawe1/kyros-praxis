import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import jwt, { JwtPayload } from "jsonwebtoken";

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
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/auth/login`, {
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
          const token = data.access_token as string;

          const jwtSecret = process.env.JWT_SECRET;
          if (!jwtSecret) {
            throw new Error("JWT_SECRET environment variable is not set");
          }

          try {
            const decoded = jwt.verify(token, jwtSecret, {
              algorithms: ["HS512", "HS256"],
            }) as JwtPayload & {
              id?: string;
              name?: string;
              email?: string;
            };

            const email = decoded.email ?? credentials?.email;
            if (!email) {
              return null;
            }

            return {
              id: decoded.sub ?? decoded.id ?? email,
              name: decoded.name ?? email,
              email,
              token,
            } as any;
          } catch (error) {
            console.error("Authentication error: invalid token", error);
            return null;
          }
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

