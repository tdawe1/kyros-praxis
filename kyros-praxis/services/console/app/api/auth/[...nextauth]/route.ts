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
      // Dev-only authorize to unblock local flows
      async authorize(credentials) {
        const email = (credentials as any)?.email || "user@example.com";
        return { id: "dev-user", name: email, email } as any;
      },
    }),
  ],
  session: { strategy: "jwt" },
  secret: process.env.NEXTAUTH_SECRET || "dev-secret",
});

export { handler as GET, handler as POST };

