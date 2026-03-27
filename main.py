"""KaiNova — Main entry point. Starts Telegram bot + 30s scheduler concurrently."""
from __future__ import annotations
import asyncio, sys
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
    logger.info(f"Mode: {'DRY RUN 🔵' if settings.dry_run else 'LIVE 🟢'}")
    logger.info(f"Scan interval: {settings.scan_interval_sec}s")

    # Build Telegram app
    app = build_bot()
    set_notify(_send_telegram)

    # Run scheduler + Telegram concurrently
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        logger.success("✅ Telegram bot online")

        # Register bot commands menu
        from telegram import BotCommand
        commands = [
            BotCommand("start",     "Launch bot"),
            BotCommand("help",      "All commands"),
            BotCommand("menu",      "Interactive menu"),
            BotCommand("scan",      "Market scan"),
            BotCommand("portfolio", "Portfolio"),
            BotCommand("positions", "Open positions"),
            BotCommand("profit",    "Daily PnL"),
            BotCommand("status",    "System status"),
            BotCommand("startbot",  "Enable auto-trading"),
            BotCommand("stopbot",   "Pause auto-trading"),
            BotCommand("buy",       "Market buy"),
            BotCommand("sell",      "Market sell"),
            BotCommand("limit",     "Limit order"),
            BotCommand("close",     "Close position"),
            BotCommand("closeall",  "Close all positions"),
            BotCommand("futures",   "Futures order"),
            BotCommand("leverage",  "Set leverage"),
            BotCommand("funding",   "Funding rate"),
            BotCommand("ticker",    "Live ticker"),
            BotCommand("signals",   "Trading signals"),
            BotCommand("earn",      "Simple earn"),
            BotCommand("convert",   "Convert quote"),
            BotCommand("history",   "Trade history"),
            BotCommand("risk",      "Risk status"),
            BotCommand("analyze",   "AI deep analysis"),
            BotCommand("ai",        "Ask AI anything"),
            BotCommand("auth",      "OAuth authentication"),
        ]
        await app.bot.set_my_commands(commands)

        # Start 30-second scheduler
        await start_scheduler()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
