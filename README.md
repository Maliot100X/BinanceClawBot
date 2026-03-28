<div align="center">

# 🦾 KaiNova BinanceClawBot
**The Ultimate Autonomous AI Crypto Trading Platform**

![KaiNova Banner](https://raw.githubusercontent.com/Maliot100X/BinanceClawBot/main/dashboard/public/banner.png)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-00ff88?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-00d4ff?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![Binance](https://img.shields.io/badge/Binance-Skills%2026-F0B90B?style=for-the-badge&logo=binance&logoColor=black)](https://binance.com)

*26 Binance Skills • Multi-Provider AI (Ollama/Groq/Gemini) • 3D Dashboard • 24/7 AI Brain*

</div>

---

## 🚀 Overview

KaiNova BinanceClawBot is a production-grade autonomous trading platform that combines the power of **LLM reasoning** (Ollama, Groq, Gemini, OpenAI) with a hardened **Binance Skills Hub (26 skills)**. It scans markets every 30 seconds, computes deep TA (RSI, MACD, EMA, VWAP), and executes trades with professional-grade risk circuits.

---

## 🛠️ Installation & Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Maliot100X/BinanceClawBot.git
cd BinanceClawBot
pip install -r requirements.txt
cd dashboard && npm install && cd ..
```

### 2. Configure AI Brain & Keys
Launch the interactive setup tool to configure your API keys and select your active AI provider:
```bash
py provider_setup.py
```
*Supports Ollama (Local/Cloud), Groq (Llama 3.3), Google Gemini, and OpenAI.*

### 3. One-Click Launch
The unified launcher handles process hardening and synchronization across the full stack:
```bash
py start_all.py
```
- **Dashboard**: `http://localhost:3000`
- **FastAPI Backend**: `http://localhost:8000`
- **Telegram Bot**: Active immediately

---

## 🤖 AI Commands (Telegram)

| Command | Description |
|---------|-------------|
| `/startbot` | Activate autonomous trading algorithm |
| `/stopbot` | Safely pause the trading loop |
| `/scan` | Full market scan with AI reasoning |
| `/dex <sym>`| **[NEW]** Real-time search on Dexscreener |
| `/mobula <sym>`| **[NEW]** Market analytics (Price/Cap) |
| `/portfolio`| Real-time balance, positions, and PnL |
| `/models` | List available models for the active brain |
| `/ai <q>` | Direct interaction with the KaiNova Brain |

---

## 📋 System Commands (CLI)

### `py start_all.py`
The master launcher that performs aggressive process hardening (clearing port 8000/3000), verifies AI authentication, and boots the Dashboard, Backend, and Bot concurrently.

### `py provider_setup.py`
The interactive management hub for:
- Configuring multi-provider API keys.
- Managing local models (`ollama pull deepseek-v3`).
- Switching the active "AI Brain" for the entire ecosystem.
- Testing connectivity heartbeats.

---

## 📄 Project Architecture

```bash
BinanceClawBot/
├── ai/              # Multi-provider Brain & OAuth logic
├── api_server.py    # FastAPI High-Performance Backend
├── dashboard/       # Next.js 14 Premium Web UI
├── telegram_bot/    # Feature-rich Telegram Interface
├── skills/          # The 26 Binance Skills Modules
├── core/            # Database & Shared Logic
├── signals/         # Technical Analysis Engine
└── start_all.py     # Unified Sync Manager
```

---

## ⚔️ Maliot100X Laboratory
**Founder of an autonomous AI lab building multi-agent systems, digital operators, and 24/7 execution infrastructure.**

### 🧠 The Thesis
The next generation of software won’t be static. It will be agentic, collaborative, persistent, and operational. KaiNova is the realization of 24/7 autonomous execution where AI stops being a chatbot and starts being an operator.

- **Multi-Agent Systems**: Coordinated execution across specialized skills.
- **24/7 Infrastructure**: Always-on monitoring and response.
- **GitHub Native**: Built in public for the future of agentic finance.

### 🛠️ Stack
`Python` `Next.js` `FastAPI` `TypeScript` `Binance API` `Ollama` `Groq` `Gemini` `OpenRouter`

---

## Lobster Society & Maliot100X
Built by @Maliot100X for the Lobster Society. No compromise, pure execution.

---

## ⚠️ Disclaimer
**Trading cryptocurrencies involves substantial risk of loss. This software is provided "as is". Use with extreme caution and always monitor your risk circuits.**
