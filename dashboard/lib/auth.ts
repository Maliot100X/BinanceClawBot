import { type NextAuthOptions } from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import GithubProvider from 'next-auth/providers/github'

export const authOptions: NextAuthOptions = {
  providers: [
    // OpenAI Codex Custom Provider
    {
      id: 'openai',
      name: 'OpenAI Codex',
      type: 'oauth',
      authorization: {
        url: "https://auth.openai.com/oauth/authorize",
        params: { 
          scope: "openid profile email offline_access",
          prompt: "login"
        }
      },
      token: "https://auth.openai.com/oauth/token",
      userinfo: "https://api.openai.com/v1/me",
      clientId: 'app_EMoamEEZ73f0CkXaXp7hrann',
      checks: ['pkce', 'state'],
      profile(profile: any) {
        return {
          id: profile.id || profile.sub,
          name: profile.name || profile.email,
          email: profile.email,
          image: profile.picture,
        }
      },
    },
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? [
          GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID,
            clientSecret: process.env.GOOGLE_CLIENT_SECRET,
          }),
        ]
      : []),
    ...(process.env.GITHUB_CLIENT_ID && process.env.GITHUB_CLIENT_SECRET
      ? [
          GithubProvider({
            clientId: process.env.GITHUB_CLIENT_ID,
            clientSecret: process.env.GITHUB_CLIENT_SECRET,
          }),
        ]
      : []),
  ],
  callbacks: {
    async session({ session, token }: any) {
      if (session.user) (session.user as any).id = token.sub
      return session
    },
  },
  pages: {
    signIn: '/login',
  },
  secret: process.env.NEXTAUTH_SECRET || 'dev-secret-at-least-32-chars-long-for-production',
}
