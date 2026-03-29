"""KaiNova — Main entry point. Starts Telegram bot + 30s scheduler concurrently."""
from __future__ import annotations
import asyncio, json, sys, os
from pathlib import Path
from loguru import logger

# ── Logging setup ─────────────────────────────────────────────────────────────
logger.remove()
logger.add(sys.stderr, level="INFO", colorize=True,
           format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
logger.add("logs/kaanova.log", rotation="10 MB", retention="7 days", level="DEBUG")
Path("logs").mkdir(exist_ok=True)

from config.settings import settings
from core.scheduler import start_scheduler, set_notify
from telegram_bot.bot import build_bot


async def _send_telegram(msg: str):
    """Injected as the scheduler's notification callback."""
    await app.bot.send_message(
        chat_id=settings.telegram_chat_id,
        text=msg,
        parse_mode="Markdown",
    )


async def main():
    global app
    logger.info("🚀 KaiNova Trading Bot starting...")

    # 1. Verify AI Brain Awareness
    session_file = Path("session.json")
    if session_file.exists() or os.environ.get("ACTIVE_AI_PROVIDER"):
        logger.success("🧠 AI Brain: Connected via Local/Cloud Provider")
    else:
        logger.warning("🧠 AI Brain: OFFLINE - Run 'py provider_setup.py' to connect")

    # 2. Verify Binance API Keys & Connection
    from core.client import get_client
    client = await get_client()
    api_key = os.environ.get("BINANCE_API_KEY") or settings.binance_api_key
    if api_key:
        logger.info(f"Checking Binance connectivity for key: ***{api_key[-4:]}...")
        await client.test_authentication()
    else:
        logger.warning("⚠️ No Binance API Key found in .env or environment")

    logger.info(f"Mode: {'DRY RUN 🔵' if settings.dry_run else 'LIVE 🟢'}")
    logger.info(f"Scan interval: {settings.scan_interval_sec}s")

    # 3. Build Telegram app
    app = build_bot()
    set_notify(_send_telegram)

    # 4. Start concurrent components
    await app.initialize()
    await app.start()
        
    # Components are already fully configured via build_bot and post_init
    
    # Start 30-second scheduler as a background task
    asyncio.create_task(start_scheduler())
    
    # Start Polling
    await app.updater.start_polling(drop_pending_updates=True)
    logger.success("✅ Telegram bot online & synchronized")
    
    # Proactive Startup Notification
    ai_model = "Unknown"
    ai_prov = "Unknown"
    from ai.oauth import oauth
    from ai.codex_agent import codex_agent
    p, t = oauth.best_token()
    if p:
        ai_prov = str(p).upper()
        ai_model = codex_agent._model
        ai_msg = f"🟢 <b>AI BRAIN ACTIVE</b> ({ai_prov}/{ai_model})"
    else:
        ai_msg = "⚠️ <b>AI BRAIN OFFLINE</b>"
        
    binance_msg = "✅ <b>BINANCE CONNECTED</b>" if api_key else "❌ <b>BINANCE MISSING</b>"
    
    start_text = (
        f"🚀 <b>KaiNova Ecosystem Online</b>\n\n"
        f"{ai_msg}\n"
        f"{binance_msg}\n\n"
        f"<i>Model in use: {ai_model}</i>\n"
        f"<i>Mode: {'DRY RUN' if settings.dry_run else 'LIVE'}</i>\n\n"
        f"Use /menu to start trading."
    )
    await _send_telegram(start_text)
    
    # Idle loop
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Shutting down bot...")
    finally:
        if app.updater.running:
            await app.updater.stop()
        if app.running:
            await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
