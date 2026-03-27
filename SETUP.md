# 🤖 BinanceClawBot — Professional Setup & OAuth

## 1. Web Dashboard (Vercel)

The web dashboard is already configured for production. 

### Environment Variables
Set these in your Vercel project settings:
- `NEXTAUTH_SECRET`: Random string (e.g. `openssl rand -base64 32`)
- `NEXTAUTH_URL`: Your Vercel domain (e.g. `https://binance-claw-bot.vercel.app`)
- `GEMINI_OAUTH_CLIENT_ID`: From Google Cloud Console
- `GEMINI_OAUTH_CLIENT_SECRET`: From Google Cloud Console
- `NEXT_PUBLIC_API_URL`: Your backend IP/domain:8000

## 2. Professional CLI ('codex')

BinanceClawBot provides a professional CLI for bot management and authentication.

### Authentication (Device-Auth Flow)
Connect your AI brains directly from the terminal.

```powershell
# Authenticate all providers (OpenAI, Gemini, Antigravity)
py codex.py login --device-auth

# Authenticate specific provider
py codex.py login --device-auth --provider openai

# Check connection status
py codex.py status
```

### Bot Control
Manage the trading engine from the command line:

```powershell
py codex.py start
py codex.py stop
```

---

## 3. Web Dashboard (Vercel)

The web dashboard is configured for production. 

### Environment Variables
Set these in your Vercel project settings:
- `NEXTAUTH_SECRET`: Random string (e.g. `openssl rand -base64 32`)
- `GOOGLE_CLIENT_ID`: From Google Cloud Console
- `GITHUB_CLIENT_ID`: From GitHub Developer Settings
- `NEXT_PUBLIC_API_URL`: Your backend IP/domain:8000

---

## 4. Deployment (Ubuntu)

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 🔍 How it works

- **Security**: No API keys are stored in configuration files. All access is via OAuth 2.0 PKCE.
- **Tokens**: Access tokens are stored in `~/.config/bianceclawbot/` and are automatically refreshed.
- **Multi-Brain**: The bot will automatically use the first available high-quality brain (Antigravity → Gemini → OpenAI).
- **26 Skills**: All Binance Skills Hub APIs are mapped and available to the AI.
