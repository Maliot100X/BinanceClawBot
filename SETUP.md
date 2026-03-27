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

---

## 2. CLI OAuth (Local Machine / CMD)

To connect your bots directly from the command line:

```powershell
# 1. Install requirements
pip install -r requirements.txt

# 2. Connect OpenAI (Codex)
# This will open your browser and use port 1455 for callback
python oauth_connect.py openai

# 3. Connect Gemini / Antigravity
# This will use port 8085 / 8086 for callback
python oauth_connect.py gemini
python oauth_connect.py antigravity

# 4. Check status
python oauth_connect.py status
```

---

## 3. Deployment (Ubuntu)

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
