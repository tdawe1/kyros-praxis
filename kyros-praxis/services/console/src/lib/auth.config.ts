import type { NextAuthOptions } from 'next-auth'
import { env } from './env'

export const authOptions: NextAuthOptions = {
  session: {
    strategy: 'jwt',
  },
  cookies: {
    sessionToken: {
      name: `__Secure-next-auth.session-token`,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV === 'production',
      },
    },
  },
  // For PKCE: when adding OAuth providers, set pkce: true in provider config
  providers: [
    // Placeholder providers, e.g.,
    // CredentialsProvider({
    //   ...,
    // }),
  ],
  secret: env.NEXTAUTH_SECRET,
  // Use getServerSession(authOptions) for server-side sessions
}