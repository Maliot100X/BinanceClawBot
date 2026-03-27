# 🚀 Vercel Production Setup Guide

To deploy the KaiNova BinanceClawBot Dashboard to Vercel and ensure all AI providers work perfectly, you MUST set the following Environment Variables in your Vercel Project Settings.

## 🔑 Authentication (NextAuth)

| Variable | Description | Example / Note |
|----------|-------------|----------------|
| `NEXTAUTH_URL` | Your production URL | `https://your-bot.vercel.app` |
| `NEXTAUTH_SECRET` | A long random string | Use `openssl rand -base64 32` |

## 🤖 AI Provider OAuth (PKCE)

### OpenAI Codex
| Variable | Description |
|----------|-------------|
| `OPENAI_CLIENT_ID` | Your OpenAI OAuth App ID |
| `OPENAI_CLIENT_SECRET`| (Optional for PKCE) |

### Google Gemini / Antigravity
| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google Cloud Console Client ID |
| `GOOGLE_CLIENT_SECRET`| Google Cloud Console Client Secret |

## 📡 API Connectivity

| Variable | Description | Note |
|----------|-------------|------|
| `NEXT_PUBLIC_API_URL` | URL of your local/remote FastAPI | Default: `http://localhost:8000` |

---

## 🛠️ Step-by-Step Vercel Deployment

1. **GitHub Push**: Ensure your latest code is pushed to your repo.
2. **New Project**: Go to [Vercel](https://vercel.com) and import `BinanceClawBot`.
3. **Configure Settings**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `dashboard`
4. **Environment Variables**: Add all the variables listed above.
5. **Deploy**: Hit Deploy.

## ⚠️ Important: OpenAI Callback URL
In the OpenAI Developer Dashboard, you MUST whitelist this exact Redirect URI:
`https://your-bot.vercel.app/api/auth/callback/openai`

Failure to do this will result in the `unknown_error` or `redirect_uri_mismatch` you previously encountered.
