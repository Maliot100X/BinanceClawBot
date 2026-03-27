"""
KaiNova Trading Bot — Premium Telegram UI
All trading commands, inline keyboards, AI chat, real-time alerts.
"""
from __future__ import annotations
import asyncio
import html
import json
import traceback
from datetime import datetime
from typing import Optional

from loguru import logger
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand, MenuButtonCommands,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

from config.settings import settings
from core.client import get_client
from execution.order_engine import order_engine
from risk.risk_manager import risk_manager
from signals.indicators import compute_indicators
from signals.signal_generator import generate_signal, Signal
from ai.oauth import oauth
from ai.codex_agent import codex_agent, DEFAULT_SYMBOLS, _scan, _portfolio

# ─────────────────────────────── EMOJI PALETTE ──────────────────────────────
E = {
    "bot":    "🤖", "bull":   "🐂", "bear":   "🐻", "chart":  "📊",
    "money":  "💰", "fire":   "🔥", "check":  "✅", "cross":  "❌",
    "warn":   "⚠️",  "lock":   "🔒", "up":     "📈", "down":   "📉",
    "clock":  "⏰", "brain":  "🧠", "scan":   "🔍", "pos":    "📋",
    "rocket": "🚀", "stop":   "🛑", "play":   "▶️",  "key":    "🔑",
    "usdt":   "💵", "spark":  "✨", "gem":    "💎", "signal": "📡",
    "globe":  "🌐", "trade":  "💱", "earn":   "🏦", "news":   "📰",
    "pnl":    "💹", "risk":   "🛡️",  "ai":     "🤖", "link":   "🔗",
}

BANNER = (
    "╔══════════════════════════════╗\n"
    "║  🤖  <b>KaiNova Trading Bot</b>  🤖  ║\n"
    "╚══════════════════════════════╝"
)

AUTHORIZED_USERS = {int(settings.telegram_chat_id)}


def _is_authorized(update: Update) -> bool:
    uid = update.effective_user.id if update.effective_user else None
    return uid in AUTHORIZED_USERS


def _fmt_price(v: float) -> str:
    if v >= 1000:
        return f"${v:,.2f}"
    elif v >= 1:
        return f"${v:.4f}"
    return f"${v:.8f}"


def _signal_emoji(sig: str) -> str:
    return {"BUY": E["up"] + "BUY", "SELL": E["down"] + "SELL", "HOLD": "⏸️HOLD"}.get(sig, sig)


def _trend_bar(score: float) -> str:
    filled = int(score / 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {score:.0f}%"


# ─────────────────────────────── KEYBOARD BUILDERS ──────────────────────────

def _main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{E['scan']} Scan Market", callback_data="cmd_scan"),
            InlineKeyboardButton(f"{E['chart']} Portfolio", callback_data="cmd_portfolio"),
        ],
        [
            InlineKeyboardButton(f"{E['pos']} Positions", callback_data="cmd_positions"),
            InlineKeyboardButton(f"{E['pnl']} Profit/PnL", callback_data="cmd_profit"),
        ],
        [
            InlineKeyboardButton(f"{E['play']} Start Bot", callback_data="cmd_startbot"),
            InlineKeyboardButton(f"{E['stop']} Stop Bot", callback_data="cmd_stopbot"),
        ],
        [
            InlineKeyboardButton(f"{E['brain']} Ask AI", callback_data="cmd_ai"),
            InlineKeyboardButton(f"{E['risk']} Risk Status", callback_data="cmd_risk"),
        ],
        [
            InlineKeyboardButton(f"{E['signal']} Signals", callback_data="cmd_signals"),
            InlineKeyboardButton(f"{E['earn']} Earn", callback_data="cmd_earn"),
        ],
        [
            InlineKeyboardButton(f"{E['trade']} Quick Buy", callback_data="cmd_quickbuy"),
            InlineKeyboardButton(f"{E['trade']} Quick Sell", callback_data="cmd_quicksell"),
        ],
        [
            InlineKeyboardButton(f"{E['key']} Auth OpenAI", callback_data="cmd_auth"),
            InlineKeyboardButton(f"{E['globe']} Status", callback_data="cmd_status"),
        ],
    ])


def _back_button(cb: str = "cmd_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back to Menu", callback_data=cb)]])


def _symbol_keyboard(action: str) -> InlineKeyboardMarkup:
    symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOT", "AVAX", "MATIC", "LINK"]
    rows = []
    for i in range(0, len(symbols), 4):
        rows.append([
            InlineKeyboardButton(s, callback_data=f"{action}_{s}USDT")
            for s in symbols[i:i+4]
        ])
    rows.append([InlineKeyboardButton("◀️ Back", callback_data="cmd_menu")])
    return InlineKeyboardMarkup(rows)


def _confirm_keyboard(action: str, symbol: str, qty: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"✅ Confirm {action}", callback_data=f"confirm_{action}_{symbol}_{qty}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cmd_menu"),
        ]
    ])


# ─────────────────────────────── MESSAGE FORMATTERS ─────────────────────────

async def _fmt_scan(symbols: list[str] | None = None) -> str:
    data = await _scan(symbols or DEFAULT_SYMBOLS[:8])
    results = data.get("scan_results", [])
    if not results:
        return f"{E['warn']} No scan data available."

    lines = [f"{BANNER}\n\n{E['scan']} <b>Market Scan</b> — {datetime.utcnow().strftime('%H:%M UTC')}\n"]
    for r in results[:8]:
        sig_icon = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(r["signal"], "⚪")
        lines.append(
            f"{sig_icon} <b>{r['symbol']}</b>  {_fmt_price(r['price'])}\n"
            f"   Signal: <b>{r['signal']}</b> ({r['confidence']:.0f}%)  RSI: {r['rsi']}\n"
            f"   Trend: {r['trend']}  |  {r['reason']}\n"
        )
    return "\n".join(lines)


async def _fmt_portfolio() -> str:
    data = await _portfolio()
    if "error" in data:
        return f"{E['cross']} Portfolio error: {data['error']}"

    balances = data.get("balances", [])
    risk = data.get("risk_summary", {})
    total = data.get("total_usdt_approx", 0)

    lines = [f"{BANNER}\n\n{E['chart']} <b>Portfolio</b>\n"]
    lines.append(f"{E['usdt']} Total USDT: <b>${total:,.2f}</b>\n")
    lines.append(f"<b>Balances:</b>")
    for b in balances[:8]:
        free = float(b.get("free", 0))
        locked = float(b.get("locked", 0))
        if free + locked > 0.0001:
            lines.append(f"  • {b['asset']}: {free:.6f} (locked: {locked:.6f})")

    lines.append(f"\n{E['risk']} <b>Risk Summary:</b>")
    lines.append(f"  Daily PnL: ${risk.get('daily_pnl', 0):+.2f}")
    lines.append(f"  Daily Loss: ${risk.get('daily_loss', 0):.2f} / {risk.get('max_daily_loss_pct', 10)}%")
    lines.append(f"  Bot Active: {'✅' if risk.get('active') else '❌'}")
    return "\n".join(lines)


async def _fmt_positions() -> str:
    positions = order_engine.position_summary()
    if not positions:
        return f"{E['pos']} No open positions."
    lines = [f"{BANNER}\n\n{E['pos']} <b>Open Positions</b>\n"]
    for p in positions:
        side_icon = "🟢" if p["side"] == "BUY" else "🔴"
        lines.append(
            f"{side_icon} <b>{p['symbol']}</b> — {p['side']}\n"
            f"   Qty: {p['qty']}  Entry: {_fmt_price(p['entry_price'])}\n"
            f"   SL: {_fmt_price(p['stop_loss'] or 0)}  TP: {_fmt_price(p['take_profit'] or 0)}\n"
            f"   Market: {p['market']}  Opened: {p['opened']}\n"
        )
    return "\n".join(lines)


async def _fmt_profit() -> str:
    risk = risk_manager.summary()
    pnl = risk.get("daily_pnl", 0)
    loss = risk.get("daily_loss", 0)
    icon = E["up"] if pnl >= 0 else E["down"]
    return (
        f"{BANNER}\n\n"
        f"{E['pnl']} <b>Daily PnL Report</b>\n\n"
        f"{icon} Net PnL: <b>${pnl:+.2f}</b>\n"
        f"📉 Total Loss: <b>${loss:.2f}</b>\n"
        f"Max Daily Loss Limit: {risk.get('max_daily_loss_pct', 10)}%\n"
        f"Status: {'✅ Within limits' if abs(pnl) < risk.get('max_daily_loss_pct',10) else '❌ LIMIT REACHED'}"
    )


async def _fmt_status() -> str:
    client = get_client()
    binance_ok = False
    server_time = "N/A"
    try:
        t = await client.get_server_time()
        server_time = datetime.utcfromtimestamp(t / 1000).strftime("%H:%M:%S UTC")
        binance_ok = True
    except Exception:
        pass

    ai_ok = oauth.is_authenticated()
    bot_active = risk_manager.is_active()

    return (
        f"{BANNER}\n\n"
        f"{E['globe']} <b>System Status</b>\n\n"
        f"{'✅' if binance_ok else '❌'} Binance API: {'Connected' if binance_ok else 'Disconnected'}\n"
        f"   Server time: {server_time}\n"
        f"{'✅' if ai_ok else '⚠️'} OpenAI OAuth: {'Authenticated' if ai_ok else 'Not authenticated'}\n"
        f"{'✅' if bot_active else '🛑'} Trading Bot: {'Active' if bot_active else 'Paused'}\n"
        f"{E['risk']} Risk Guard: Always ON\n"
        f"{E['clock']} Scan interval: {settings.scan_interval_sec}s\n"
        f"Mode: {'🔵 DRY RUN' if settings.dry_run else '🟢 LIVE'}"
    )


# ─────────────────────────────── COMMAND HANDLERS ───────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    text = (
        f"{BANNER}\n\n"
        f"{E['rocket']} <b>Welcome to KaiNova Trading Bot!</b>\n\n"
        f"Your autonomous crypto trading assistant powered by:\n"
        f"• 26 Binance Skills Hub APIs\n"
        f"• OpenAI Codex AI reasoning engine\n"
        f"• Advanced TA: RSI / MACD / EMA / VWAP\n"
        f"• 4 strategies: Breakout / Momentum / Mean Reversion / Whale\n"
        f"• 5% max position · 10% daily loss limit · 5x max leverage\n\n"
        f"Use the menu or commands below to get started!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=_main_menu())


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    text = (
        f"{BANNER}\n\n"
        f"📖 <b>Command Reference</b>\n\n"
        f"<b>Bot Control</b>\n"
        f"/startbot — Enable auto-trading loop\n"
        f"/stopbot — Pause auto-trading\n"
        f"/status — System & connection status\n\n"
        f"<b>Market</b>\n"
        f"/scan — Full market scan with signals\n"
        f"/scan BTC ETH SOL — Scan specific coins\n"
        f"/signals — Latest trading signals\n"
        f"/ticker BTCUSDT — Live ticker for symbol\n\n"
        f"<b>Portfolio</b>\n"
        f"/portfolio — Balances and risk summary\n"
        f"/positions — Open positions\n"
        f"/profit — Daily PnL report\n"
        f"/history — Recent trade history\n\n"
        f"<b>Trading</b>\n"
        f"/buy BTCUSDT 0.001 — Market buy\n"
        f"/sell BTCUSDT 0.001 — Market sell\n"
        f"/limit BUY BTCUSDT 0.001 60000 — Limit order\n"
        f"/close BTCUSDT — Close open position\n"
        f"/closeall — Close all positions\n\n"
        f"<b>Futures</b>\n"
        f"/futures buy BTCUSDT 0.001 — Futures market buy\n"
        f"/leverage BTCUSDT 3 — Set leverage\n"
        f"/funding BTCUSDT — Funding rate\n\n"
        f"<b>Earn & Convert</b>\n"
        f"/earn — Simple earn products\n"
        f"/convert BTC USDT 0.01 — Get convert quote\n\n"
        f"<b>AI</b>\n"
        f"/ai <question> — Ask the Codex AI\n"
        f"/analyze BTCUSDT — AI deep analysis\n"
        f"/auth — Authenticate with OpenAI OAuth\n\n"
        f"<b>Info</b>\n"
        f"/risk — Risk management status\n"
        f"/menu — Show interactive menu\n"
        f"/help — This help message"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_button())


async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    await update.message.reply_text(
        f"{E['bot']} <b>KaiNova Trading Bot — Main Menu</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu(),
    )


async def cmd_startbot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    risk_manager.set_active(True)
    ctx.bot_data["auto_trade"] = True
    text = (
        f"{E['play']} <b>Auto-Trading ENABLED</b>\n\n"
        f"The bot will scan every {settings.scan_interval_sec}s and\n"
        f"execute trades when signals are strong.\n\n"
        f"{E['risk']} Risk limits are always enforced:\n"
        f"• Max position: {settings.max_position_size_pct}%\n"
        f"• Daily loss limit: {settings.max_daily_loss_pct}%\n"
        f"• Max leverage: {settings.max_leverage}x"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_button())


async def cmd_stopbot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    risk_manager.set_active(False)
    ctx.bot_data["auto_trade"] = False
    await update.message.reply_text(
        f"{E['stop']} <b>Auto-Trading PAUSED</b>\n\nNo new positions will be opened.\nExisting positions remain open.",
        parse_mode=ParseMode.HTML, reply_markup=_back_button()
    )


async def cmd_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    symbols = [a.upper() + ("USDT" if not a.upper().endswith("USDT") else "") for a in args] if args else DEFAULT_SYMBOLS[:8]
    msg = await update.message.reply_text(f"{E['scan']} Scanning market...")
    try:
        text = await _fmt_scan(symbols)
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="cmd_scan"),
             InlineKeyboardButton("◀️ Menu", callback_data="cmd_menu")]
        ])
        await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception as e:
        await msg.edit_text(f"{E['cross']} Scan failed: {e}")


async def cmd_portfolio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    msg = await update.message.reply_text(f"{E['chart']} Loading portfolio...")
    try:
        text = await _fmt_portfolio()
        await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_button())
    except Exception as e:
        await msg.edit_text(f"{E['cross']} Error: {e}")


async def cmd_positions(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    text = await _fmt_positions()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="cmd_positions"),
         InlineKeyboardButton("🚫 Close All", callback_data="confirm_closeall"),
         InlineKeyboardButton("◀️ Menu", callback_data="cmd_menu")]
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_profit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    text = await _fmt_profit()
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_button())


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    text = await _fmt_status()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="cmd_status"),
         InlineKeyboardButton("◀️ Menu", callback_data="cmd_menu")]
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_buy(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            f"{E['warn']} Usage: /buy BTCUSDT 0.001\n"
            "Or use the quick buy button in the menu.",
            reply_markup=_symbol_keyboard("quickbuy")
        )
        return
    symbol, qty = args[0].upper(), args[1]
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    kb = _confirm_keyboard("BUY", symbol, qty)
    await update.message.reply_text(
        f"{E['up']} <b>Confirm Order</b>\n\n"
        f"Symbol: <b>{symbol}</b>\n"
        f"Side: <b>BUY</b>\n"
        f"Quantity: <b>{qty}</b>\n"
        f"Type: Market\n\n"
        f"⚠️ Stop loss will be set automatically.",
        parse_mode=ParseMode.HTML, reply_markup=kb
    )


async def cmd_sell(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            f"{E['warn']} Usage: /sell BTCUSDT 0.001",
            reply_markup=_symbol_keyboard("quicksell")
        )
        return
    symbol, qty = args[0].upper(), args[1]
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    kb = _confirm_keyboard("SELL", symbol, qty)
    await update.message.reply_text(
        f"{E['down']} <b>Confirm Order</b>\n\n"
        f"Symbol: <b>{symbol}</b>\nSide: <b>SELL</b>\nQty: <b>{qty}</b>",
        parse_mode=ParseMode.HTML, reply_markup=kb
    )


async def cmd_limit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if len(args) < 4:
        await update.message.reply_text(f"{E['warn']} Usage: /limit BUY BTCUSDT 0.001 60000")
        return
    side, symbol, qty, price = args[0].upper(), args[1].upper(), args[2], args[3]
    try:
        result = await order_engine.place_limit_order(symbol, side, float(qty), float(price))
        await update.message.reply_text(
            f"{E['check']} Limit order placed!\n{symbol} {side} {qty} @ ${price}",
            parse_mode=ParseMode.HTML, reply_markup=_back_button()
        )
    except Exception as e:
        await update.message.reply_text(f"{E['cross']} Failed: {e}")


async def cmd_close(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if not args:
        await update.message.reply_text(f"{E['warn']} Usage: /close BTCUSDT")
        return
    symbol = args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    result = await order_engine.close_position(symbol)
    status = E["check"] if result.get("status") == "ok" else E["cross"]
    await update.message.reply_text(
        f"{status} Close {symbol}: {result.get('status', result.get('error', 'unknown'))}",
        reply_markup=_back_button()
    )


async def cmd_closeall(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, close all", callback_data="confirm_closeall"),
         InlineKeyboardButton("❌ Cancel", callback_data="cmd_menu")]
    ])
    await update.message.reply_text(
        f"{E['warn']} <b>Close ALL positions?</b>\n\nThis will market-sell every open position.",
        parse_mode=ParseMode.HTML, reply_markup=kb
    )


async def cmd_futures(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if len(args) < 3:
        await update.message.reply_text(f"{E['warn']} Usage: /futures buy BTCUSDT 0.001")
        return
    side, symbol, qty = args[0].upper(), args[1].upper(), float(args[2])
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    if side == "BUY":
        result = await order_engine.place_market_buy(symbol, qty, "FUTURES")
    else:
        result = await order_engine.place_market_sell(symbol, qty, "FUTURES")
    status = E["check"] if result.get("status") == "ok" else E["cross"]
    await update.message.reply_text(f"{status} Futures {side} {symbol}: {result}", reply_markup=_back_button())


async def cmd_leverage(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(f"{E['warn']} Usage: /leverage BTCUSDT 3")
        return
    symbol, lev = args[0].upper(), int(args[1])
    client = get_client()
    result = await client.set_futures_leverage(symbol, lev)
    await update.message.reply_text(f"{E['check']} Leverage set: {result}", reply_markup=_back_button())


async def cmd_funding(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    from skills.binance_skills import ALL_SKILLS
    args = ctx.args
    symbol = args[0].upper() if args else "BTCUSDT"
    fut = ALL_SKILLS["derivatives_usds_futures"]
    result = await fut.get_funding_rate(symbol)
    rate = float(result.get("lastFundingRate", 0)) * 100
    await update.message.reply_text(
        f"⛽ <b>Funding Rate</b> {symbol}\n\nRate: <b>{rate:.4f}%</b>",
        parse_mode=ParseMode.HTML, reply_markup=_back_button()
    )


async def cmd_ticker(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    symbol = args[0].upper() if args else "BTCUSDT"
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    client = get_client()
    t = await client.get_ticker(symbol)
    chg = float(t.get("priceChangePercent", 0))
    icon = E["up"] if chg >= 0 else E["down"]
    await update.message.reply_text(
        f"{icon} <b>{symbol}</b>\n\n"
        f"Price: <b>{_fmt_price(float(t.get('lastPrice', 0)))}</b>\n"
        f"24h Change: <b>{chg:+.2f}%</b>\n"
        f"24h High: {_fmt_price(float(t.get('highPrice', 0)))}\n"
        f"24h Low: {_fmt_price(float(t.get('lowPrice', 0)))}\n"
        f"24h Volume: {float(t.get('volume', 0)):,.2f}",
        parse_mode=ParseMode.HTML, reply_markup=_back_button()
    )


async def cmd_signals(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    msg = await update.message.reply_text(f"{E['signal']} Generating signals...")
    data = await _scan_market(DEFAULT_SYMBOLS)
    results = data.get("scan_results", [])
    buys = [r for r in results if r["signal"] == "BUY"]
    sells = [r for r in results if r["signal"] == "SELL"]
    lines = [f"{BANNER}\n\n{E['signal']} <b>Active Signals</b>\n"]
    if buys:
        lines.append(f"🟢 <b>BUY Signals ({len(buys)})</b>")
        for r in buys:
            lines.append(f"  • {r['symbol']} | {_trend_bar(r['confidence'])} | RSI {r['rsi']}")
    if sells:
        lines.append(f"\n🔴 <b>SELL Signals ({len(sells)})</b>")
        for r in sells:
            lines.append(f"  • {r['symbol']} | {_trend_bar(r['confidence'])} | RSI {r['rsi']}")
    if not buys and not sells:
        lines.append("⏸️ No strong signals at the moment. Market is ranging.")
    await msg.edit_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=_back_button())


async def cmd_earn(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    from skills.binance_skills import ALL_SKILLS
    try:
        products = await ALL_SKILLS["simple_earn"].get_flexible_products()
        account = await ALL_SKILLS["simple_earn"].get_earn_account()
        lines = [f"{E['earn']} <b>Simple Earn</b>\n"]
        rows = (products.get("rows") or products) if isinstance(products, dict) else products
        for p in (rows or [])[:5]:
            lines.append(f"  • {p.get('asset', '?')} APY: {p.get('latestAnnualPercentageRate', '?')}")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=_back_button())
    except Exception as e:
        await update.message.reply_text(f"{E['cross']} Earn: {e}", reply_markup=_back_button())


async def cmd_convert(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if len(args) < 3:
        await update.message.reply_text(f"{E['warn']} Usage: /convert BTC USDT 0.01")
        return
    from skills.binance_skills import ALL_SKILLS
    try:
        result = await ALL_SKILLS["convert"].get_quote(args[0].upper(), args[1].upper(), float(args[2]))
        await update.message.reply_text(
            f"{E['trade']} <b>Convert Quote</b>\n\n{result}",
            parse_mode=ParseMode.HTML, reply_markup=_back_button()
        )
    except Exception as e:
        await update.message.reply_text(f"{E['cross']} Error: {e}")


async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    symbol = args[0].upper() if args else "BTCUSDT"
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    client = get_client()
    try:
        trades = await client.get_my_trades(symbol, limit=5)
        if not trades:
            await update.message.reply_text(f"No trades found for {symbol}.")
            return
        lines = [f"{E['news']} <b>Trade History: {symbol}</b>\n"]
        for t in trades:
            side = "BUY" if t.get("isBuyer") else "SELL"
            icon = "🟢" if side == "BUY" else "🔴"
            lines.append(f"{icon} {side} {t.get('qty')} @ {_fmt_price(float(t.get('price', 0)))}")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=_back_button())
    except Exception as e:
        await update.message.reply_text(f"{E['cross']} {e}")


async def cmd_risk(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    r = risk_manager.summary()
    text = (
        f"{BANNER}\n\n"
        f"{E['risk']} <b>Risk Management Status</b>\n\n"
        f"Bot Active: {'✅' if r['active'] else '🛑'}\n"
        f"Daily PnL: <b>${r['daily_pnl']:+.2f}</b>\n"
        f"Daily Loss: <b>${r['daily_loss']:.2f}</b>\n"
        f"Max Daily Loss: <b>{r['max_daily_loss_pct']}%</b>\n"
        f"Max Position: <b>{r['max_position_pct']}%</b>\n"
        f"Max Leverage: <b>{r['max_leverage']}x</b>\n\n"
        f"Stop Loss: ✅ Required on all trades\n"
        f"Default Position: ${settings.default_trade_usdt}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_button())


async def cmd_analyze(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    symbol = args[0].upper() if args else "BTCUSDT"
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    msg = await update.message.reply_text(f"{E['brain']} Asking AI to analyze {symbol}...")
    response = await codex_agent.think(f"Give me a detailed trading analysis for {symbol}. Use the scan_market and portfolio_status tools.")
    await msg.edit_text(
        f"{E['brain']} <b>AI Analysis: {symbol}</b>\n\n{html.escape(response)}",
        parse_mode=ParseMode.HTML, reply_markup=_back_button()
    )


async def cmd_ai(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if not args:
        await update.message.reply_text(f"{E['warn']} Usage: /ai <your question>")
        return
    question = " ".join(args)
    msg = await update.message.reply_text(f"{E['brain']} Thinking...")
    response = await codex_agent.think(question)
    await msg.edit_text(
        f"{E['brain']} <b>AI Response</b>\n\n{html.escape(response)}",
        parse_mode=ParseMode.HTML, reply_markup=_back_button()
    )


async def cmd_auth(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    if oauth_manager.is_authenticated():
        await update.message.reply_text(f"{E['check']} Already authenticated with OpenAI OAuth!", reply_markup=_back_button())
        return
    await update.message.reply_text(
        f"{E['key']} <b>OpenAI OAuth Authentication</b>\n\n"
        f"Starting browser authentication flow...\n"
        f"A browser window will open on the server.\n"
        f"After logging in, the bot will be connected.",
        parse_mode=ParseMode.HTML
    )
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, oauth.login, "openai")
        if oauth.is_authenticated():
            await update.message.reply_text(f"{E['check']} Authentication successful! AI features are now active.", reply_markup=_main_menu())
        else:
            await update.message.reply_text(f"{E['cross']} Authentication failed or was cancelled.", reply_markup=_back_button())
    except Exception as e:
        await update.message.reply_text(f"{E['cross']} Auth error: {e}")


# ─────────────────────────────── CALLBACK QUERY HANDLER ─────────────────────

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    async def edit(text: str, kb=None, parse=ParseMode.HTML):
        try:
            await q.edit_message_text(text, parse_mode=parse, reply_markup=kb or _back_button())
        except Exception:
            pass

    if data == "cmd_menu":
        await edit(f"{E['bot']} <b>KaiNova Main Menu</b>", _main_menu())

    elif data == "cmd_scan":
        await edit(f"{E['scan']} Scanning...")
        text = await _fmt_scan()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="cmd_scan"),
             InlineKeyboardButton("◀️ Menu", callback_data="cmd_menu")]
        ])
        await edit(text, kb)

    elif data == "cmd_portfolio":
        await edit(f"{E['chart']} Loading...")
        await edit(await _fmt_portfolio())

    elif data == "cmd_positions":
        text = await _fmt_positions()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="cmd_positions"),
             InlineKeyboardButton("🚫 Close All", callback_data="confirm_closeall"),
             InlineKeyboardButton("◀️ Menu", callback_data="cmd_menu")]
        ])
        await edit(text, kb)

    elif data == "cmd_profit":
        await edit(await _fmt_profit())

    elif data == "cmd_status":
        text = await _fmt_status()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="cmd_status"),
             InlineKeyboardButton("◀️ Menu", callback_data="cmd_menu")]
        ])
        await edit(text, kb)

    elif data == "cmd_startbot":
        risk_manager.set_active(True)
        ctx.bot_data["auto_trade"] = True
        await edit(f"{E['play']} <b>Auto-Trading ENABLED</b>\n\nBot will trade every {settings.scan_interval_sec} seconds.")

    elif data == "cmd_stopbot":
        risk_manager.set_active(False)
        ctx.bot_data["auto_trade"] = False
        await edit(f"{E['stop']} <b>Auto-Trading PAUSED</b>")

    elif data == "cmd_signals":
        await edit(f"{E['signal']} Generating signals...")
        data2 = await _scan_market(DEFAULT_SYMBOLS)
        results = data2.get("scan_results", [])
        buys = [r for r in results if r["signal"] == "BUY"]
        sells = [r for r in results if r["signal"] == "SELL"]
        lines = [f"{E['signal']} <b>Active Signals</b>\n"]
        for r in buys:
            lines.append(f"🟢 <b>{r['symbol']}</b> {r['confidence']:.0f}% | RSI {r['rsi']} | {r['reason']}")
        for r in sells:
            lines.append(f"🔴 <b>{r['symbol']}</b> {r['confidence']:.0f}% | RSI {r['rsi']} | {r['reason']}")
        if not buys and not sells:
            lines.append("⏸️ No strong signals right now.")
        await edit("\n".join(lines))

    elif data == "cmd_risk":
        r = risk_manager.summary()
        text = (
            f"{E['risk']} <b>Risk Status</b>\n\n"
            f"Daily PnL: ${r['daily_pnl']:+.2f}\n"
            f"Daily Loss: ${r['daily_loss']:.2f} / {r['max_daily_loss_pct']}%\n"
            f"Max Position: {r['max_position_pct']}%\n"
            f"Max Leverage: {r['max_leverage']}x\n"
            f"Bot: {'✅ Active' if r['active'] else '🛑 Paused'}"
        )
        await edit(text)

    elif data == "cmd_earn":
        from skills.binance_skills import ALL_SKILLS
        try:
            products = await ALL_SKILLS["simple_earn"].get_flexible_products()
            rows = (products.get("rows") or []) if isinstance(products, dict) else (products or [])
            lines = [f"{E['earn']} <b>Simple Earn</b>\n"]
            for p in rows[:5]:
                lines.append(f"  • {p.get('asset')} APY: {p.get('latestAnnualPercentageRate', 'N/A')}")
            await edit("\n".join(lines))
        except Exception as e:
            await edit(f"{E['cross']} Earn error: {e}")

    elif data == "cmd_ai":
        await edit(
            f"{E['brain']} <b>AI Chat Mode</b>\n\n"
            f"Send me a message and I'll answer using OpenAI Codex.\n\n"
            f"Use /ai <question> or just type your question."
        )

    elif data == "cmd_auth":
        if oauth_manager.is_authenticated():
            await edit(f"{E['check']} Already authenticated!")
        else:
            await edit(f"{E['key']} Use /auth command to start OAuth flow.")

    elif data == "cmd_quickbuy":
        await edit(f"{E['up']} <b>Quick Buy</b>\nSelect a coin:", _symbol_keyboard("quickbuy"))

    elif data == "cmd_quicksell":
        await edit(f"{E['down']} <b>Quick Sell</b>\nSelect a coin:", _symbol_keyboard("quicksell"))

    elif data.startswith("quickbuy_"):
        symbol = data.replace("quickbuy_", "")
        client = get_client()
        ticker = await client.get_ticker(symbol)
        price = float(ticker.get("lastPrice", 0))
        usdt = settings.default_trade_usdt
        qty = round(usdt / price, 6) if price > 0 else 0
        await edit(
            f"{E['up']} <b>Buy {symbol}</b>\n\n"
            f"Current Price: {_fmt_price(price)}\n"
            f"USDT to spend: ${usdt}\n"
            f"Est. Qty: {qty}",
            _confirm_keyboard("BUY", symbol, str(qty))
        )

    elif data.startswith("quicksell_"):
        symbol = data.replace("quicksell_", "")
        positions = order_engine.position_summary()
        pos = next((p for p in positions if p["symbol"] == symbol), None)
        qty = pos["qty"] if pos else 0
        await edit(
            f"{E['down']} <b>Sell {symbol}</b>\n\nQty: {qty}",
            _confirm_keyboard("SELL", symbol, str(qty))
        )

    elif data.startswith("confirm_BUY_") or data.startswith("confirm_SELL_"):
        parts = data.split("_")
        side, sym, qty_str = parts[1], parts[2], parts[3]
        await edit(f"⏳ Placing {side} order for {sym}...")
        qty = float(qty_str)
        if side == "BUY":
            result = await order_engine.place_market_buy(sym, qty)
        else:
            result = await order_engine.place_market_sell(sym, qty)
        status = E["check"] if result.get("status") == "ok" else E["cross"]
        await edit(
            f"{status} <b>Order {'Executed' if result.get('status')=='ok' else 'Failed'}</b>\n\n"
            f"Symbol: {sym}\nSide: {side}\nQty: {qty}\n"
            f"Price: {_fmt_price(result.get('price', 0))}\n"
            f"SL: {_fmt_price(result.get('sl') or 0)}"
        )

    elif data == "confirm_closeall":
        await edit("⏳ Closing all positions...")
        results = await order_engine.close_all_positions()
        await edit(f"{E['check']} Closed {len(results)} positions.")


# ─────────────────────────────── FREE TEXT → AI ─────────────────────────────

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    text = update.message.text
    if not text:
        return
    msg = await update.message.reply_text(f"{E['brain']} Thinking...")
    response = await codex_agent.think(text)
    await msg.edit_text(
        f"{E['brain']} {html.escape(response)}",
        parse_mode=ParseMode.HTML, reply_markup=_back_button()
    )


# ─────────────────────────────── ERROR HANDLER ──────────────────────────────

async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Telegram error: {ctx.error}")


# ─────────────────────────────── BOT BUILDER ────────────────────────────────

def build_bot() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()

    # Register all commands
    handlers = [
        ("start",     cmd_start),
        ("help",      cmd_help),
        ("menu",      cmd_menu),
        ("startbot",  cmd_startbot),
        ("stopbot",   cmd_stopbot),
        ("scan",      cmd_scan),
        ("portfolio", cmd_portfolio),
        ("positions", cmd_positions),
        ("profit",    cmd_profit),
        ("status",    cmd_status),
        ("buy",       cmd_buy),
        ("sell",      cmd_sell),
        ("limit",     cmd_limit),
        ("close",     cmd_close),
        ("closeall",  cmd_closeall),
        ("futures",   cmd_futures),
        ("leverage",  cmd_leverage),
        ("funding",   cmd_funding),
        ("ticker",    cmd_ticker),
        ("signals",   cmd_signals),
        ("earn",      cmd_earn),
        ("convert",   cmd_convert),
        ("history",   cmd_history),
        ("risk",      cmd_risk),
        ("analyze",   cmd_analyze),
        ("ai",        cmd_ai),
        ("auth",      cmd_auth),
    ]
    for name, handler in handlers:
        app.add_handler(CommandHandler(name, handler))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    return app
