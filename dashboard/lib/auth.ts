import { type NextAuthOptions } from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import GithubProvider from 'next-auth/providers/github'

export const authOptions: NextAuthOptions = {
  providers: [
    {
      id: 'openai',
      name: 'OpenAI Codex',
      type: 'oauth',
      authorization: {
        url: "https://auth.openai.com/oauth/authorize",
        params: { 
          scope: "openid profile email offline_access",
          prompt: "login",
          response_type: "code"
        }
      },
      token: "https://auth.openai.com/oauth/token",
      userinfo: "https://api.openai.com/v1/me",
      // Real OpenAI OAuth integration using PKCE
      clientId: process.env.OPENAI_CLIENT_ID || 'app_EMoamEEZ73f0CkXaXp7hrann', 
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
    {
      id: 'gemini',
      name: 'Google Gemini',
      type: 'oauth',
      authorization: {
        url: "https://accounts.google.com/o/oauth2/v2/auth",
        params: { 
          scope: "openid profile email https://www.googleapis.com/auth/generative-language",
          access_type: "offline",
          prompt: "consent"
        }
      },
      token: "https://oauth2.googleapis.com/token",
      userinfo: "https://www.googleapis.com/oauth2/v3/userinfo",
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      profile(profile: any) {
        return {
          id: profile.sub,
          name: profile.name,
          email: profile.email,
          image: profile.picture,
        }
      },
    },
    {
      id: 'antigravity',
      name: 'Antigravity (DeepMind)',
      type: 'oauth',
      authorization: {
        url: "https://accounts.google.com/o/oauth2/v2/auth",
        params: { 
          scope: "openid profile email https://www.googleapis.com/auth/generative-language.retrieval",
          access_type: "offline",
          prompt: "consent"
        }
      },
      token: "https://oauth2.googleapis.com/token",
      userinfo: "https://www.googleapis.com/oauth2/v3/userinfo",
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      profile(profile: any) {
        return {
          id: profile.sub,
          name: profile.name || "Antigravity User",
          email: profile.email,
          image: profile.picture,
        }
      },
    },
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
  secret: process.env.NEXTAUTH_SECRET || 'development-secret-at-least-32-chars-long',
}
