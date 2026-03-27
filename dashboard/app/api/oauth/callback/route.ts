/**
 * OAuth Callback Handler
 * Called by provider after user authenticates
 * Exchanges code for token, stores in httpOnly cookie, redirects to dashboard
 */
import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'

const TOKEN_URLS: Record<string, string> = {
  openai: 'https://auth.openai.com/oauth/token',
  gemini: 'https://oauth2.googleapis.com/token',
  antigravity: 'https://oauth2.googleapis.com/token',
}

const CLIENT_IDS: Record<string, string> = {
  openai: 'app_EMoamEEZ73f0CkXaXp7hrann',
  gemini: process.env.GEMINI_OAUTH_CLIENT_ID || '',
  antigravity: process.env.ANTIGRAVITY_OAUTH_CLIENT_ID || process.env.GEMINI_OAUTH_CLIENT_ID || '',
}

const CLIENT_SECRETS: Record<string, string> = {
  openai: '', // No secret — public PKCE client
  gemini: process.env.GEMINI_OAUTH_CLIENT_SECRET || '',
  antigravity: process.env.ANTIGRAVITY_OAUTH_CLIENT_SECRET || process.env.GEMINI_OAUTH_CLIENT_SECRET || '',
}

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl
  const provider = searchParams.get('provider')
  const code = searchParams.get('code')
  const state = searchParams.get('state')
  const error = searchParams.get('error')

  const dashboardUrl = `${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/settings`

  if (error || !code || !provider) {
    return NextResponse.redirect(`${dashboardUrl}?oauth_error=${error || 'missing_code'}&provider=${provider}`)
  }

  const cookieStore = cookies()
  const savedVerifier = cookieStore.get(`pkce_verifier_${provider}`)?.value
  const savedState = cookieStore.get(`pkce_state_${provider}`)?.value

  // Validate state
  if (!savedState || savedState !== state) {
    return NextResponse.redirect(`${dashboardUrl}?oauth_error=state_mismatch&provider=${provider}`)
  }
  if (!savedVerifier) {
    return NextResponse.redirect(`${dashboardUrl}?oauth_error=missing_verifier&provider=${provider}`)
  }

  // Build redirect_uri to match what was used in /start
  const base = process.env.NEXTAUTH_URL || `${req.nextUrl.protocol}//${req.nextUrl.host}`
  const redirectUri = `${base}/api/oauth/callback?provider=${provider}`

  // Exchange code for token
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: redirectUri,
    client_id: CLIENT_IDS[provider] || '',
    code_verifier: savedVerifier,
  })
  if (CLIENT_SECRETS[provider]) {
    body.set('client_secret', CLIENT_SECRETS[provider])
  }

  try {
    const tokenRes = await fetch(TOKEN_URLS[provider], {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    })
    const token = await tokenRes.json()

    if (!tokenRes.ok || token.error) {
      return NextResponse.redirect(`${dashboardUrl}?oauth_error=${token.error || 'token_failed'}&provider=${provider}`)
    }

    token.expires_at = Math.floor(Date.now() / 1000) + (token.expires_in || 3600)
    token.provider = provider

    // Store token in httpOnly cookie (7 days)
    const res = NextResponse.redirect(`${dashboardUrl}?oauth_success=${provider}`)
    res.cookies.set(`oauth_token_${provider}`, JSON.stringify(token), {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 60 * 60 * 24 * 7,
      path: '/',
    })
    // Clear PKCE cookies
    res.cookies.delete(`pkce_verifier_${provider}`)
    res.cookies.delete(`pkce_state_${provider}`)
    return res

  } catch (err: any) {
    return NextResponse.redirect(`${dashboardUrl}?oauth_error=network_error&provider=${provider}`)
  }
}
