/**
 * Web OAuth API Routes for BinanceClawBot
 * Handles PKCE OAuth flow for web users (Vercel deployment)
 *
 * Flow:
 * 1. GET  /api/oauth/start?provider=openai  → redirect to provider
 * 2. GET  /api/oauth/callback?code=...&state=... → exchange code, store token
 * 3. GET  /api/oauth/status → check all provider connections
 * 4. POST /api/oauth/disconnect?provider=openai → remove token
 */
import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import crypto from 'crypto'

// ── Provider Config (mirrors oauth_connect.py) ───────────────────────────────
const PROVIDERS: Record<string, {
  clientId: string
  clientSecret?: string
  authUrl: string
  tokenUrl: string
  scopes: string
  extraParams?: Record<string, string>
}> = {
  openai: {
    // Public client — no secret needed (PKCE only)
    clientId: 'app_EMoamEEZ73f0CkXaXp7hrann',
    authUrl: 'https://auth.openai.com/oauth/authorize',
    tokenUrl: 'https://auth.openai.com/oauth/token',
    scopes: 'openid profile email offline_access',
    extraParams: {
      codex_cli_simplified_flow: 'true',
      id_token_add_organizations: 'true',
      originator: 'bianceclawbot',
    },
  },
  gemini: {
    clientId: process.env.GEMINI_OAUTH_CLIENT_ID || '',
    clientSecret: process.env.GEMINI_OAUTH_CLIENT_SECRET || '',
    authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl: 'https://oauth2.googleapis.com/token',
    scopes: 'openid email profile https://www.googleapis.com/auth/generative-language',
    extraParams: { access_type: 'offline', prompt: 'consent' },
  },
  antigravity: {
    clientId: process.env.ANTIGRAVITY_OAUTH_CLIENT_ID || process.env.GEMINI_OAUTH_CLIENT_ID || '',
    clientSecret: process.env.ANTIGRAVITY_OAUTH_CLIENT_SECRET || process.env.GEMINI_OAUTH_CLIENT_SECRET || '',
    authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl: 'https://oauth2.googleapis.com/token',
    scopes: 'openid email profile https://www.googleapis.com/auth/cloud-platform',
    extraParams: { access_type: 'offline', prompt: 'consent' },
  },
}

// ── PKCE helpers ─────────────────────────────────────────────────────────────
function pkceVerifier() {
  return crypto.randomBytes(32).toString('base64url')
}
function pkceChallenge(verifier: string) {
  return crypto.createHash('sha256').update(verifier).digest('base64url')
}

function getRedirectUri(provider: string, req: NextRequest) {
  const base = process.env.NEXTAUTH_URL || `${req.nextUrl.protocol}//${req.nextUrl.host}`
  return `${base}/api/oauth/callback?provider=${provider}`
}

// ── GET /api/oauth/start?provider=openai ─────────────────────────────────────
export async function GET(req: NextRequest) {
  const { searchParams, pathname } = req.nextUrl

  // ── Status check ──────────────────────────────────────────────────────────
  if (pathname.endsWith('/status')) {
    const jar = cookies()
    const status: Record<string, any> = {}
    for (const p of Object.keys(PROVIDERS)) {
      const tokenCookie = jar.get(`oauth_token_${p}`)
      if (tokenCookie) {
        try {
          const t = JSON.parse(tokenCookie.value)
          status[p] = { connected: true, expired: t.expires_at < Date.now() / 1000 }
        } catch { status[p] = { connected: false } }
      } else {
        status[p] = { connected: false }
      }
    }
    return NextResponse.json({ providers: status })
  }

  // ── Start OAuth ───────────────────────────────────────────────────────────
  const provider = searchParams.get('provider')
  if (!provider || !PROVIDERS[provider]) {
    return NextResponse.json({ error: 'Invalid provider. Use: openai, gemini, antigravity' }, { status: 400 })
  }

  const cfg = PROVIDERS[provider]
  if (!cfg.clientId) {
    return NextResponse.json({
      error: `${provider.toUpperCase()} OAuth not configured`,
      setup: provider === 'openai'
        ? 'OpenAI uses a public client - should work automatically'
        : `Set ${provider.toUpperCase()}_OAUTH_CLIENT_ID and _CLIENT_SECRET in Vercel environment variables`
    }, { status: 400 })
  }

  const verifier = pkceVerifier()
  const challenge = pkceChallenge(verifier)
  const state = crypto.randomBytes(16).toString('hex')
  const redirectUri = getRedirectUri(provider, req)

  const params = new URLSearchParams({
    response_type: 'code',
    client_id: cfg.clientId,
    redirect_uri: redirectUri,
    scope: cfg.scopes,
    code_challenge: challenge,
    code_challenge_method: 'S256',
    state,
    ...cfg.extraParams,
  })

  const authUrl = `${cfg.authUrl}?${params.toString()}`

  // Store verifier + state in cookies (httpOnly, lasts 5 minutes)
  const res = NextResponse.redirect(authUrl)
  res.cookies.set(`pkce_verifier_${provider}`, verifier, { httpOnly: true, maxAge: 300, path: '/' })
  res.cookies.set(`pkce_state_${provider}`, state, { httpOnly: true, maxAge: 300, path: '/' })
  return res
}

// ── POST /api/oauth/disconnect?provider=openai ────────────────────────────────
export async function POST(req: NextRequest) {
  const provider = req.nextUrl.searchParams.get('provider')
  if (!provider) return NextResponse.json({ error: 'provider required' }, { status: 400 })
  const res = NextResponse.json({ status: 'disconnected' })
  res.cookies.delete(`oauth_token_${provider}`)
  return res
}
