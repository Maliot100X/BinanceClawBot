"""
FastAPI Backend Server for BinanceClawBot
This is the API that the Next.js web dashboard calls.
Run: python api_server.py
"""
from __future__ import annotations
import asyncio, json
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import uvicorn

# Import bot modules
from config.settings import settings
from skills.loader import SKILLS
from signals.indicators import compute_indicators
from signals.signal_generator import generate_signal, Signal
from execution.order_engine import order_engine
from risk.risk_manager import risk_manager
from core.client import get_client
from ai.codex_agent import codex_agent
from ai.oauth import oauth
from core.scheduler import start_scheduler, set_notify

app = FastAPI(title="BinanceClawBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://binance-claw-bot.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── State ────────────────────────────────────────────────────────────────────
_bot_running = False
_scheduler_task = None
_config: dict = {}

# ── Helpers ──────────────────────────────────────────────────────────────────
def check_cli_session():
    sess_path = BASE_DIR / "session.json"
    if sess_path.exists():
        try:
            with open(sess_path, "r") as f:
                sess = json.load(f)
                return bool(sess.get("access_token"))
        except: return False
    return False

@app.get("/api/diag")
async def diagnostic():
    env_path = BASE_DIR / ".env"
    return {
        "cwd": os.getcwd(),
        "base_dir": str(BASE_DIR),
        "env_exists": env_path.exists(),
        "session_exists": (BASE_DIR / "session.json").exists(),
        "binance_key_loaded": bool(os.environ.get("BINANCE_API_KEY") or settings.binance_api_key),
        "openai_key_loaded": bool(os.environ.get("OPENAI_OAUTH_CLIENT_ID") or settings.openai_oauth_client_id),
    }

WATCHLIST = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
             "ADAUSDT","DOTUSDT","AVAXUSDT","MATICUSDT","LINKUSDT"]


# ── Models ───────────────────────────────────────────────────────────────────
class OrderReq(BaseModel):
    symbol: str
    qty: float

class BinanceConfig(BaseModel):
    api_key: str
    secret_key: str

class TelegramConfig(BaseModel):
    token: str
    chat_id: str

class ChatReq(BaseModel):
    message: str

class ScanReq(BaseModel):
    symbols: list[str] = WATCHLIST


# Explicitly load from settings into os.environ for client sync
import os
logger.info(f"Checking for .env at: {BASE_DIR / '.env'}")
if settings.binance_api_key: 
    os.environ["BINANCE_API_KEY"] = settings.binance_api_key
    logger.success(f"Backend loaded Binance Key: ***{settings.binance_api_key[-4:]}")
else:
    logger.warning("Backend: No Binance API Key found in settings/env")

if settings.binance_secret_key: os.environ["BINANCE_SECRET_KEY"] = settings.binance_secret_key

# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/status")
async def status():
    o_status = oauth.status()
    if check_cli_session():
        o_status["openai"] = True
    
    # Add Binance key status for verification
    binance_key = os.environ.get("BINANCE_API_KEY") or settings.binance_api_key
    b_status = f"***{binance_key[-4:]}" if binance_key else "Missing"

    return {
        "running": _bot_running,
        "dry_run": settings.dry_run,
        "scan_interval": settings.scan_interval_sec,
        "oauth": o_status,
        "binance_key": b_status,
        "risk": risk_manager.summary() if hasattr(risk_manager, 'summary') else {},
        "timestamp": datetime.utcnow().isoformat(),
        "skills_loaded": list(SKILLS.keys()),
    }

@app.post("/bot/start")
async def bot_start():
    global _bot_running, _scheduler_task
    if _bot_running:
        return {"status": "already running"}
    _bot_running = True
    risk_manager.set_active(True)
    _scheduler_task = asyncio.create_task(start_scheduler())
    logger.info("Bot started via web UI")
    return {"status": "started"}

@app.post("/bot/stop")
async def bot_stop():
    global _bot_running, _scheduler_task
    _bot_running = False
    risk_manager.set_active(False)
    if _scheduler_task:
        _scheduler_task.cancel()
        _scheduler_task = None
    logger.info("Bot stopped via web UI")
    return {"status": "stopped"}

@app.get("/health")
async def health():
    return {"status": "online", "version": "1.0.0", "engine": "KaiNova"}

@app.get("/portfolio")
async def portfolio():
    try:
        client = get_client()
        # Allow if API Key OR CLI Session exists
        binance_key = os.environ.get("BINANCE_API_KEY") or settings.binance_api_key
        if not binance_key and not check_cli_session():
             return {"balances": [], "connected": False}
        account = await client.get_account()
        balances = [b for b in account.get("balances", []) if float(b.get("free", 0)) > 0 or float(b.get("locked", 0)) > 0]
        return {"balances": balances[:20], "connected": True}
    except Exception as e:
        return {"balances": [], "connected": False, "error": str(e)}

@app.get("/positions")
async def positions():
    try:
        binance_key = os.environ.get("BINANCE_API_KEY") or settings.binance_api_key
        if not binance_key and not check_cli_session():
             return {"positions": [], "connected": False}
        return {"positions": order_engine.position_summary(), "connected": True}
    except: return {"positions": [], "connected": False}

@app.get("/signals")
async def signals():
    try:
        client = get_client()
        binance_key = os.environ.get("BINANCE_API_KEY") or settings.binance_api_key
        if not binance_key and not check_cli_session():
             return {"signals": []}
        results = []
        for sym in WATCHLIST[:6]:
            try:
                klines = await client.get_klines(sym, "1h", 200)
                ind = compute_indicators(sym, klines)
                if ind:
                    sig = generate_signal(ind)
                    results.append({"symbol": sym, "signal": sig.signal.value,
                        "confidence": sig.confidence, "rsi": ind.rsi,
                        "price": ind.close, "trend": ind.trend, "reason": sig.reason})
            except Exception: pass
        return {"signals": results}
    except: return {"signals": []}

@app.post("/scan")
async def scan(req: ScanReq):
    try:
        client = get_client()
        binance_key = os.environ.get("BINANCE_API_KEY") or settings.binance_api_key
        if not binance_key and not check_cli_session(): return {"results": []}
        results = []
        for sym in req.symbols[:10]:
            try:
                klines = await client.get_klines(sym, "1h", 200)
                ind = compute_indicators(sym, klines)
                if ind:
                    sig = generate_signal(ind)
                    results.append({"symbol": sym, "signal": sig.signal.value,
                        "confidence": sig.confidence, "price": ind.close})
            except Exception: pass
        return {"results": results}
    except: return {"results": []}

@app.get("/skills")
async def list_skills():
    return {name: s.__class__.__doc__ or "" for name, s in SKILLS.items()}

@app.get("/ticker/{symbol}")
async def ticker(symbol: str):
    spot = SKILLS.get("spot")
    if not spot: raise HTTPException(404, "spot skill not loaded")
    return await spot.ticker_price(symbol)

@app.post("/binance/config")
async def binance_config(cfg: BinanceConfig):
    os.environ["BINANCE_API_KEY"] = cfg.api_key
    os.environ["BINANCE_SECRET_KEY"] = cfg.secret_key
    # Force reset client
    get_client(force_new=True)
    return {"status": "ok", "message": "Binance keys configured"}

class AIConfig(BaseModel):
    provider: str
    api_key: str

@app.post("/ai/config")
async def ai_config(cfg: AIConfig):
    import os
    # Map to env vars that ai/oauth.py or codex_agent.py can use
    provider_key = f"{cfg.provider.upper()}_API_KEY"
    os.environ[provider_key] = cfg.api_key
    # Also save to local config if persistent
    from ai.oauth import oauth
    oauth.save_api_key(cfg.provider, cfg.api_key)
    return {"status": "ok", "message": f"{cfg.provider} configured successfully"}

@app.post("/telegram/config")
async def telegram_config(cfg: TelegramConfig):
    import os
    os.environ["TELEGRAM_BOT_TOKEN"] = cfg.token
    os.environ["TELEGRAM_CHAT_ID"] = cfg.chat_id
    return {"status": "ok", "message": "Telegram configured"}

@app.get("/auth/status")
async def auth_status():
    return oauth.status()

@app.post("/auth/start")
async def auth_start(body: dict):
    provider = body.get("provider", "openai")
    return {"status": "redirect", "url": f"/auth/callback/{provider}"}

@app.post("/order/buy")
async def order_buy(req: OrderReq):
    result = await order_engine.place_market_buy(req.symbol, req.qty)
    return result

@app.post("/order/sell")
async def order_sell(req: OrderReq):
    result = await order_engine.place_market_sell(req.symbol, req.qty)
    return result

@app.post("/position/close/{symbol}")
async def close_pos(symbol: str):
    result = await order_engine.close_position(symbol)
    return result

@app.post("/ai/chat")
async def ai_chat(req: ChatReq):
    reply = await codex_agent.think(req.message)
    return {"reply": reply}

@app.get("/trades/history")
async def trade_history():
    spot = SKILLS.get("spot")
    if not spot: return {"trades": []}
    try:
        t = await spot.my_trades("BTCUSDT", limit=20)
        return {"trades": t}
    except Exception: return {"trades": []}

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
