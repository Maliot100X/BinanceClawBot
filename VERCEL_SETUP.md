# 🚀 Vercel Production Setup Guide (Professional Edition)

To deploy the KaiNova BinanceClawBot Dashboard to Vercel and ensure all AI providers work perfectly, you MUST follow these steps.

## 🔑 1. Environment Variables (Vercel)

Set these in your Vercel Project Settings:

| Variable | Description | Example / Note |
|----------|-------------|----------------|
| `NEXT_PUBLIC_API_URL` | **CRITICAL**: Your API Backend URL | `http://your-home-ip:8000` or `http://localhost:8000` |
| `NEXTAUTH_URL` | Your Vercel URL | `https://your-bot.vercel.app` |
| `NEXTAUTH_SECRET` | Random string | `openssl rand -base64 32` |
| `OPENAI_CLIENT_ID` | OpenAI OAuth App ID | (See Section 3) |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | (See Section 3) |

## 🛠️ 2. Step-by-Step Vercel Deployment

1. **GitHub Push**: Ensure your latest code is pushed to your repo.
2. **New Project**: In Vercel, import `BinanceClawBot`.
3. **Configure**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `dashboard`
4. **Deploy**: Hit Deploy.

## 🌐 3. Public vs Private OAuth

### Private Mode (One User)
If you only want yourself to use the bot, use your private `OPENAI_CLIENT_ID` and `BINANCE_API_KEY` in your `.env`.

### Public Mode (For Everyone)
To allow *anyone* to connect their AI to your Vercel instance:
1.  Go to the **OpenAI Developer Dashboard**.
2.  Create a **Public OAuth App**.
3.  Set the **Redirect URI** to: `https://your-bot.vercel.app/api/auth/callback/openai`.
4.  Copy the **Client ID** to your Vercel Env Vars.
5.  Users can then click "Continue with OpenAI" and it will work for their account.

## 🛡️ 4. CORS Whitelisting
The KaiNova API Backend now supports **All Origins (`*`)** by default for maximum compatibility. If you want to restrict it, update `api_server.py` with your Vercel domain.

---

## 🚦 System Health Monitor
The dashboard now includes a **Real-Time System Monitor**.
- **GREEN**: AI Backend is online and reachable.
- **RED**: AI Backend is offline. Run `py start_all.py` on your local machine.

If your Vercel app shows **OFFLINE** while your local script is running, check your Firewall/Port Forwarding for port `8000`.
