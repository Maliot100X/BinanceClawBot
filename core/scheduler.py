"""30-second automation loop — the heartbeat of KaiNova."""
from __future__ import annotations
import asyncio
from datetime import datetime
from loguru import logger
from core.client import get_client
from signals.indicators import compute_indicators
from signals.signal_generator import generate_signal, Signal
from execution.order_engine import order_engine
from risk.risk_manager import risk_manager
from config.settings import settings

WATCHLIST = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
             "ADAUSDT","DOTUSDT","AVAXUSDT","MATICUSDT","LINKUSDT"]

_notify_cb = None  # Telegram notification callback injected by main.py

def set_notify(cb): global _notify_cb; _notify_cb = cb

async def _notify(msg: str):
    """Notify both the main user and the specialized signal channel."""
    if _notify_cb:
        try: await _notify_cb(msg)
        except Exception: pass
    
    # Also broadcast to the signal channel if it exists
    await broadcast_to_signal(msg)


async def broadcast_to_signal(msg: str):
    """Send specialized tactical updates to the BinanceClawSignal channel."""
    try:
        from core.client import get_client
        # Avoid circular import, bot setup might be cleaner but this works for now
        # We'll use a direct telegram bot instance if available, but for now we rely on the injected callback
        # Actually, let's use the Bot token directly for reliability if callback fails
        import httpx
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": settings.telegram_signal_channel_id,
            "text": msg,
            "parse_mode": "HTML"
        }
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload)
    except Exception as e:
        logger.warning(f"Tactical broadcast failed: {e}")


async def post_heartbeat():
    """5-minute heartbeat for specialized channel."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    msg = (
        f"<b>🫀 KaiNova Heartbeat</b>\n"
        f"🕒 Timestamp: <code>{now} UTC</code>\n"
        f"🟢 <b>Bot Active</b> | Monitoring Market\n"
        f"📡 <b>Signal Channel:</b> Operational"
    )
    await broadcast_to_signal(msg)


_cycle_counter = 0

async def run_cycle():
    """One 30-second trading cycle."""
    global _cycle_counter
    if not risk_manager.is_active():
        return

    _cycle_counter += 1
    # 5-minute heartbeat (10 cycles of 30s)
    if _cycle_counter % 10 == 0:
        await post_heartbeat()

    client = await get_client()
    try:
        account = await client.get_account()
        balances = account.get("balances", [])
        usdt_bal = next((float(b["free"]) for b in balances if b["asset"] == "USDT"), 0.0)
    except Exception as e:
        logger.warning(f"Balance fetch failed: {e}"); return

    if not risk_manager.check_daily_loss(usdt_bal):
        await _notify("🛑 *Daily loss limit hit.* Auto-trading paused.")
        risk_manager.set_active(False)
        return

    # 1. AI-DRIVEN AUTONOMOUS EXECUTION (High Tier: Rate-Limited to every 3 mins)
    if _cycle_counter % 6 == 0:
        from ai.codex_agent import codex_agent
        try:
            # Prompt the AI Brain to perform an autonomous cycle
            prompt = (
                f"AUTONOMOUS CYCLE START. Risk Level: {risk_manager.risk_level}. "
                f"Mandate: MAXIMIZE WIN PERCENTAGE and TOTAL PNL. "
                f"Analyze WATCHLIST {WATCHLIST} and execute any high-confidence trades now."
            )
            logger.info("🧠 Brain initiating tactical review...")
            response = await codex_agent.think(prompt)
            # We don't notify the full response to avoid spam, but we log it
            logger.debug(f"AI Tactical Response: {response[:200]}...")
        except Exception as e:
            logger.error(f"AI Tactical error: {e}")

    # 2. FAILSAFE TECHNICAL EXECUTION (Spot Baseline)
    for symbol in WATCHLIST:
        try:
            klines = await client.get_klines(symbol, "1h", 200)
            ind = compute_indicators(symbol, klines)
            if not ind: continue
            sig = generate_signal(ind)

            if sig.signal == Signal.BUY and sig.confidence > 75:
                qty = risk_manager.calc_position_size(usdt_bal, ind.close)
                if qty > 0 and symbol not in {p["symbol"] for p in order_engine.position_summary()}:
                    result = await order_engine.place_market_buy(symbol, qty)
                    if result.get("status") == "ok":
                        await _notify(
                            f"✅ *AI BUY {symbol}*\n"
                            f"Price: ${ind.close:,.4f} | Qty: {qty}\n"
                            f"Reason: {sig.reason}\n"
                            f"SL: ${result.get('sl',0):,.4f} | TP: ${result.get('tp',0):,.4f}"
                        )

            elif sig.signal == Signal.SELL and sig.confidence > 75:
                pos = next((p for p in order_engine.position_summary() if p["symbol"] == symbol), None)
                if pos:
                    result = await order_engine.place_market_sell(symbol, pos["qty"])
                    if result.get("status") == "ok":
                        await _notify(f"📉 *AI SELL {symbol}* | Confidence: {sig.confidence:.0f}%")

        except Exception as e:
            logger.debug(f"Cycle error {symbol}: {e}")

    logger.info(f"[{datetime.utcnow().strftime('%H:%M:%S')}] Cycle complete. USDT: ${usdt_bal:,.2f}")


async def start_scheduler():
    """Infinite 30-second loop."""
    logger.info(f"Scheduler started — interval: {settings.scan_interval_sec}s")
    while True:
        try:
            await run_cycle()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        await asyncio.sleep(settings.scan_interval_sec)
