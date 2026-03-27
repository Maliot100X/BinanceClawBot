<div align="center">

# 🦾 KaiNova BinanceClawBot
**The Ultimate Autonomous AI Crypto Trading Platform**

![KaiNova Banner](https://raw.githubusercontent.com/Maliot100X/BinanceClawBot/main/dashboard/public/banner.png)

[![Python 3.12](https://img.shields.io/badge/Python-3.12-00ff88?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-00d4ff?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![Binance](https://img.shields.io/badge/Binance-Skills%2026-F0B90B?style=for-the-badge&logo=binance&logoColor=black)](https://binance.com)

*26 Binance Skills • Professional PKCE OAuth • 3D Dashboard Preview • 24/7 AI Brain*

</div>

---

## 🚀 Overview

KaiNova BinanceClawBot is a production-grade autonomous trading platform that combines the power of **LLM reasoning** (OpenAI GPT-4o, Google Gemini) with the **Binance Skills Hub API (26 skills)**. It scans markets every 30 seconds, analyzes technical indicators (RSI, MACD, EMA, VWAP), and executes trades with professional risk management protocols.

## ✨ Key Features

- **26 Binance Skills**: Native support for Spot, Futures, Margin, Algo trading, Earn, and DeFi.
- **AI Reasoning Engine**: Multi-provider support (OpenAI, Gemini, Antigravity) via secure PKCE OAuth.
- **Advanced Technical Analysis**: Real-time compute of RSI, MACD, EMA, VWAP, Bollinger Bands, and ATR.
- **Pro Risk Management**: 5% max position, 10% daily loss circuit breaker, and 5x max leverage.
- **Telegram Control**: Full command-and-control via a premium Telegram interface.
- **3D Dashboard**: Stunning Next.js 14 dashboard with real-time charting and public preview mode.

---

## 🚀 Quick Start (Local Development)

### 1. Installation

```bash
git clone https://github.com/Maliot100X/BinanceClawBot.git
cd BinanceClawBot
pip install -r requirements.txt
cd dashboard && npm install && cd ..
```

### 2. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

### 3. One-Click Launch
The new `start_all.py` script automatically verifies your environment and launches everything:
```bash
py start_all.py
```
*Accessible at: Dashboard (http://localhost:3000), API (http://localhost:8000), and your Telegram Bot.*

---

## 🔑 Professional OAuth & Security

KaiNova implements high-security **Proof Key for Code Exchange (PKCE)**. No API keys for your AI Brain are stored in `.env`.

- **CLI Auth**: `py codex.py login`
- **Web Auth**: Connect directly from the dashboard navbar.
- **Encryption**: All tokens are stored encrypted in your local `.config` directory.

---

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/startbot` | Enable auto-trading algorithm |
| `/stopbot` | Pause auto-trading |
| `/scan` | Full market scan with AI insights |
| `/portfolio`| Real-time balance and risk summary |
| `/status` | System, API, and Brain connectivity |
| `/ai <q>` | Ask the KaiNova Codex Brain anything |

---

## 📋 Pro CLI Commands (`codex.py`)
| Command | Description |
|---------|-------------|
| `py codex.py login` | Connect OpenAI/Gemini/Antigravity |
| `py codex.py status` | Check system & connectivity status |
| `py codex.py start` | Activate the autonomous trading loop |
| `py codex.py stop` | Safely pause the bot |

---

## 📄 Project Structure

```
BinanceClawBot/
├── ai/              # AI Brain & OAuth managers
├── api_server.py    # FastAPI backend
├── config/          # Centralized settings
├── core/            # Database & shared logic
├── dashboard/       # Next.js 14 Web UI
├── execution/       # Order execution engine
├── risk/            # Risk management & circuit breakers
├── signals/         # TA & signal generation
├── skills/          # 26 Binance Skills Hub modules
├── telegram_bot/    # Premium Telegram UI
└── start_all.py     # Unified process manager
```

---

## ⚠️ Disclaimer
**Trading cryptocurrencies involves substantial risk of loss. This software is provided "as is". Past performance is not indicative of future results. Use with extreme caution.**

---

<div align="center">
Built with ❤️ for the future of agentic finance by **Maliot / KaiNova**.
</div>
