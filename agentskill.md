---
description: "KaiNova Ecosystem: Zero-Friction Setup & Initialization Prompt"
tags: ["setup", "binance", "telegram", "ai-brain", "installation"]
---

# KaiNova AI Agent Skill: One-Shot Autonomous Setup
**Instructions for User:** Copy the prompt below entirely and paste it to your active AI agent (e.g., Gemini, Claude Code, OpenClaw, or ChatGPT) inside this repository to automatically configure and start your ecosystem without errors.

---
### 📋 COPY-PASTE THIS TO YOUR AI AGENT:
```text
SYSTEM DIRECTIVE: KAINOVA ECOSYSTEM SETUP
You are now activating the KaiNova Autonomous Trading Ecosystem. Your goal is to configure the environment, establish all API connections, and launch the 3D dashboard + trading loop securely and correctly on the first try.

Follow these strict, additive steps. Do NOT delete or modify existing functional logic:

1. DEPENDENCIES & ENVIRONMENT 📦
- Verify Python 3.10+ and Node.js >= 16 are installed.
- Ensure all Python dependencies are installed: `pip install -r requirements.txt`
- Check for the existence of the `.env` file in the root directory. If missing, create it from `.env.example`.

2. CREDENTIALS & API BINDINGS 🔑
Ask the user to provide the following securely or verify they are populated in `.env`:
- `BINANCE_API_KEY` & `BINANCE_SECRET_KEY` (MUST have Spot & Futures endpoints enabled).
- `TELEGRAM_BOT_TOKEN` (Obtained from BotFather) & `TELEGRAM_CHAT_ID`.
- `ACTIVE_AI_PROVIDER` (e.g., ollama, groq, openai, deepseek) and its corresponding key (e.g., `OLLAMA_URL=http://localhost:11434` or `GROQ_API_KEY`).

3. SYSTEM CLOCK SYNCHRONIZATION ⏳
- Binance requires strict 400ms time synchronization.
- Automatically execute `w32tm /resync` (Windows) or `sudo ntpdate pool.ntp.org` (Linux/Mac) to ensure timestamps do not trigger 400 Bad Request HMAC errors.

4. PORT CLEANUP & LAUNCH 🚀
- Aggressively terminate any existing zombie processes on ports `8000` (FastAPI) and `3000` (Next.js Dashboard).
- Do not kill the Ollama underlying service if `OLLAMA_URL` is active.
- Execute `py start_all.py` (or `python start_all.py`).

5. VERIFICATION STAGE ✅
- Validate that the terminal outputs: "✨ ALL SYSTEMS LIVE & SYNCHRONIZED ✨"
- Ensure no "coroutine / get_client()" `AttributeError` exceptions appear in the logs.
- Provide the user with the Dashboard link: `http://localhost:3000`
```
---
