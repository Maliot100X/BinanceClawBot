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
    if _notify_cb:
        try: await _notify_cb(msg)
        except Exception: pass


async def run_cycle():
    """One 30-second trading cycle."""
    if not risk_manager.is_active():
        return

    client = get_client()
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

    for symbol in WATCHLIST:
        try:
            klines = await client.get_klines(symbol, "1h", 200)
            ind = compute_indicators(symbol, klines)
            if not ind: continue
            sig = generate_signal(ind)

            if sig.signal == Signal.BUY and sig.confidence > 70:
                qty = risk_manager.calc_position_size(usdt_bal, ind.close)
                if qty > 0 and symbol not in {p["symbol"] for p in order_engine.position_summary()}:
                    result = await order_engine.place_market_buy(symbol, qty)
                    if result.get("status") == "ok":
                        await _notify(
                            f"✅ *BUY {symbol}*\n"
                            f"Price: ${ind.close:,.4f} | Qty: {qty}\n"
                            f"Confidence: {sig.confidence:.0f}% | {sig.reason}\n"
                            f"SL: ${result.get('sl',0):,.4f} | TP: ${result.get('tp',0):,.4f}"
                        )

            elif sig.signal == Signal.SELL and sig.confidence > 70:
                pos = next((p for p in order_engine.position_summary() if p["symbol"] == symbol), None)
                if pos:
                    result = await order_engine.place_market_sell(symbol, pos["qty"])
                    if result.get("status") == "ok":
                        await _notify(f"📉 *SELL {symbol}* | Confidence: {sig.confidence:.0f}%")

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
