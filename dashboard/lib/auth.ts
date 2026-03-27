import { type NextAuthOptions } from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import GithubProvider from 'next-auth/providers/github'
import { type Provider } from 'next-auth/providers'

const providers: Provider[] = [
  // OpenAI Codex Custom Provider
  {
    id: 'openai',
    name: 'OpenAI Codex',
    type: 'oauth',
    authorization: {
      url: "https://auth.openai.com/oauth/authorize",
      params: { 
        scope: "openid profile email offline_access",
        codex_cli_simplified_flow: "true",
        originator: "bianceclawbot"
      }
    },
    token: "https://auth.openai.com/oauth/token",
    userinfo: "https://api.openai.com/v1/me", // Dummy or actual me endpoint if available
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
  }
]

if (process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET) {
  providers.push(
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    })
  )
}

if (process.env.GITHUB_CLIENT_ID && process.env.GITHUB_CLIENT_SECRET) {
  providers.push(
    GithubProvider({
      clientId: process.env.GITHUB_CLIENT_ID,
      clientSecret: process.env.GITHUB_CLIENT_SECRET,
    })
  )
}

export const authOptions: NextAuthOptions = {
  providers,
  callbacks: {
    async session({ session, token }: any) {
      if (session.user) (session.user as any).id = token.sub
      return session
    },
  },
  pages: {
    signIn: '/login',
  },
  secret: process.env.NEXTAUTH_SECRET || 'development-fallback-secret-12345',
}
