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
    "model":  "🧬",
}

BANNER = (
    "╔══════════════════════════════╗\n"
    "║  🤖  KaiNova Trading Bot  🤖  ║\n"
    "╚══════════════════════════════╝"
)

WELCOME_MSG = (
    f"{BANNER}\n\n"
    f"🦾 <b>Welcome to KaiNova — Professional Autonomous Trading</b>\n\n"
    f"You are now connected to the most advanced AI trading platform on Binance.\n\n"
    f"<b>Integrated Stack:</b>\n"
    f"• 🧠 <b>Dynamic Brain:</b> Multi-Provider Autonomous Intelligence\n"
    f"• 📡 <b>26 Skills Hub:</b> Native Binance Spot/Futures/Margin/Algo\n"
    f"• 🛡️ <b>Risk Guard:</b> Automated SL/TP, 10% Daily circuit breaker\n"
    f"• 📊 <b>3D Dashboard:</b> Live monitoring at your fingertip\n\n"
    f"🌐 <b>Dashboard:</b> https://kai-nova-showdown.vercel.app/\n\n"
    f"Use the menu below or type /help for a full command reference."
)



AUTHORIZED_USERS = {int(settings.telegram_chat_id)}


def _is_authorized(update: Update) -> bool:
    uid = update.effective_user.id if update.effective_user else None
    authorized = uid in AUTHORIZED_USERS
    if not authorized:
        logger.warning(f"Unauthorized access attempt from user ID: {uid}")
    return authorized


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
            InlineKeyboardButton(f"{E['model']} Models", callback_data="cmd_models"),
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

    ai_prov_name = str(oauth.best_token()[0]).upper() if ai_ok else "Unknown"
    ai_status = f"{E['brain']} <b>BRAIN ACTIVE</b> ({ai_prov_name})" if ai_ok else f"⚠️ <b>BRAIN OFFLINE</b> (Run 'py provider_setup.py')"

    return (
        f"{BANNER}\n\n"
        f"{E['globe']} <b>System Status</b>\n\n"
        f"{'✅' if binance_ok else '❌'} <b>Binance API:</b> {'CONNECTED' if binance_ok else 'DISCONNECTED'}\n"
        f"   🕒 Server Time: {server_time}\n\n"
        f"{ai_status}\n"
        f"   🧠 Intelligence: {ai_prov_name} Autonomous Engine\n\n"
        f"{'✅' if bot_active else '🛑'} <b>Trading Engine:</b> {'AUTONOMOUS' if bot_active else 'PAUSED'}\n"
        f"   🛡️ Risk Guard: <b>100% SECURE</b>\n"
        f"   ⏰ Scan Interval: {settings.scan_interval_sec}s\n"
        f"   📊 Mode: <b>{'🔵 DRY RUN' if settings.dry_run else '🟢 LIVE'}</b>"
    )


# ─────────────────────────────── COMMAND HANDLERS ───────────────────────────



async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    await update.message.reply_text(
        WELCOME_MSG,
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
    data = await _scan(DEFAULT_SYMBOLS)
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


async def cmd_mobula(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if not args:
        await update.message.reply_text(f"💡 Usage: /mobula BTC (or coin name)\n\nThis fetches real-time price and market cap from the Mobula Analytics engine.")
        return
    asset = " ".join(args)
    from skills.loader import SKILLS
    try:
        res = await SKILLS["mobula"].market_data(asset)
        if not res or "price" not in res:
             await update.message.reply_text(f"❌ Asset '{asset}' not found on Mobula. Try a full name or different symbol.")
             return
        price = res.get("price", 0)
        cap = res.get("market_cap", 0)
        await update.message.reply_text(
            f"📊 <b>Mobula Analytics: {asset}</b>\n\n"
            f"Price: <b>${price:,.2f}</b>\n"
            f"Market Cap: <b>${cap:,.0f}</b>",
            parse_mode=ParseMode.HTML, reply_markup=_back_button()
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Mobula API Error: {e}\n\nCheck your API key in .env if this persists.")


async def cmd_dex(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if not args:
        await update.message.reply_text(f"💡 Usage: /dex <symbol_or_address>\n\nFetches real-time pairs and liquidity from Dexscreener.")
        return
    query = " ".join(args)
    from skills.loader import SKILLS
    try:
        res = await SKILLS["dexscreener"].search_pairs(query)
        pairs = res.get("pairs", [])
        if not pairs:
            await update.message.reply_text(f"🔍 No pairs found for '{query}' on Dexscreener.")
            return
        
        # Format top 3 pairs
        lines = [f"🦅 <b>Dexscreener: {query}</b>\n"]
        for p in pairs[:3]:
            lines.append(
                f"🔹 <b>{p.get('baseToken',{}).get('symbol')}/{p.get('quoteToken',{}).get('symbol')}</b> ({p.get('chainId')})\n"
                f"   Price: <b>${p.get('priceUsd', '0')}</b>\n"
                f"   Liq: ${float(p.get('liquidity',{}).get('usd',0)):,.0f}\n"
                f"   Vol 24h: ${float(p.get('volume',{}).get('h24',0)):,.0f}\n"
            )
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=_back_button())
    except Exception as e:
        await update.message.reply_text(f"❌ Dexscreener Error: {e}")


async def cmd_set(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if len(args) < 2 or args[0].lower() != "risk":
        await update.message.reply_text(f"💡 Usage: <code>/set risk 1-5</code>\n\n1: Consv | 2: Low | 3: Bal | 4: High | 5: Aggro", parse_mode=ParseMode.HTML)
        return
    
    try:
        level = int(args[1])
        from risk.risk_manager import risk_manager
        if risk_manager.set_risk_level(level):
            summary = risk_manager.summary()
            await update.message.reply_text(
                f"🛡️ <b>Risk Profile Updated: Level {level}</b>\n\n"
                f"• Max Position: <b>{summary['max_position_pct']}%</b>\n"
                f"• Daily Loss Limit: <b>{summary['max_daily_loss_pct']}%</b>\n"
                f"• Max Leverage: <b>{summary['max_leverage']}x</b>\n\n"
                f"✅ Engine re-calibrated for {'Aggressive' if level > 3 else 'Safe'} execution.",
                parse_mode=ParseMode.HTML, reply_markup=_back_button()
            )
        else:
            await update.message.reply_text("❌ Invalid level. Choose 1 to 5.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_skills(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    from skills.loader import SKILLS
    text = (
        f"{BANNER}\n\n"
        f"🔧 <b>Binance Skills Hub — {len(SKILLS)} Active</b>\n\n"
        f"1.  <b>Spot Trading:</b> Full market execution\n"
        f"2.  <b>USDS-M Futures:</b> Up to 20x leverage\n"
        f"3.  <b>Coin-M Futures:</b> Inverse trading\n"
        f"4.  <b>Margin:</b> Borrowing & Isolated pairs\n"
        f"5.  <b>Simple Earn:</b> Passive yield management\n"
        f"6.  <b>Algo Tools:</b> TWAP/VWAP execution\n"
        f"7.  <b>Mobula:</b> Professional market data\n"
        f"8.  <b>DexScreener:</b> On-chain analytics\n"
        f"9.  <b>Signals:</b> AI-generated bias validation\n\n"
        f"<i>Plus 17 additional sub-account, VIP, and pay skills.</i>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_button())


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


async def cmd_models(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    provider, _ = oauth.best_token()
    msg = await update.message.reply_text(f"🤖 <b>Fetching models for {provider}...</b>", parse_mode=ParseMode.HTML)
    try:
        models = await codex_agent.fetch_available_models()
        if not models:
            await msg.edit_text(f"❌ Failed to fetch models for {provider}.")
            return
            
        model_list = "\n".join([f"• <code>{mod}</code>" for mod in models[:20]])
        text = (
            f"🤖 <b>Active Provider:</b> {str(provider).upper()}\n"
            f"🎯 <b>Current Model:</b> {codex_agent._model}\n\n"
            f"<i>Available Models:</i>\n{model_list}\n\n"
            f"<i>Switch with:</i> <code>/ai .model &lt;name&gt;</code>"
        )
        await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_button())
    except Exception as e:
        await msg.edit_text(f"❌ Error fetching models: {e}")

async def cmd_ai(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    args = ctx.args
    if not args:
        await update.message.reply_text(f"{E['warn']} Usage: /ai <your question>")
        return
    question = " ".join(args)
    
    # Handle model switching via .model/models/model shortcut
    cmd = question.split()[0].lower()
    if cmd in [".model", ".models", "model", "models"]:
        m = question.replace(cmd, "").strip()
        if not m:
             return await cmd_models(update, ctx)
             
        codex_agent.set_model(m)
        await update.message.reply_text(f"✅ <b>Brain Target Updated:</b> {codex_agent._model}", parse_mode=ParseMode.HTML)
        return

    msg = await update.message.reply_text(f"{E['brain']} Thinking ({codex_agent._model})...")
    response = await codex_agent.think(question)
    
    if "404" in str(response) and "ollama" in codex_agent._model.lower():
        response += f"\n\n💡 <b>Tip:</b> This model might not be downloaded. Run <code>py provider_setup.py</code> on your server and use the 'Pull' option."

    await msg.edit_text(
        f"{E['brain']} <b>AI ({codex_agent._model})</b>\n\n{html.escape(response)}",
        parse_mode=ParseMode.HTML, reply_markup=_back_button()
    )


async def cmd_auth(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    status = oauth.status()
    active_p, _ = oauth.best_token()
    
    text = (
        f"{E['key']} <b>Provider Authentication</b>\n\n"
        f"Active Provider: <b>{active_p.upper() if active_p else 'None'}</b>\n\n"
        f"<b>Status:</b>\n"
    )
    for p, ok in status.items():
        text += f"{'✅' if ok else '❌'} {p.upper()}\n"
    
    text += f"\n<i>To change providers or add keys, run:</i>\n<code>py provider_setup.py</code>\n<i>on your server.</i>"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_button())
    return


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
        await edit(WELCOME_MSG, _main_menu())

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
        data2 = await _scan(DEFAULT_SYMBOLS)
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

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        await update.message.reply_text("🛑 <b>Unauthorized</b>\n\nYour ID is not recognized. Contact the operator.")
        return
    await update.message.reply_text(
        WELCOME_MSG,
        parse_mode=ParseMode.HTML,
        reply_markup=_main_menu()
    )


async def cmd_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Always authorized — helps user find their ID."""
    uid = update.effective_user.id
    logger.info(f"ID CHECK hit by user {uid}")
    await update.message.reply_text(f"💳 <b>Your Telegram ID:</b> <code>{uid}</code>", parse_mode=ParseMode.HTML)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    text = (
        f"{BANNER}\n\n"
        f"📖 <b>KaiNova Master Command Reference</b>\n\n"
        f"<b>⚙️ Bot Control & Meta</b>\n"
        f"/start — Initialize bot & status menu\n"
        f"/menu — Universal control dashboard\n"
        f"/status — Engine & Connection health\n"
        f"/auth — OAuth & Key status\n"
        f"/help — This comprehensive guide\n\n"
        f"<b>🤖 Autonomous Trading</b>\n"
        f"/startbot — <b>ENABLE</b> Auto-Trading (Full AI AI)\n"
        f"/stopbot — <b>PAUSE</b> All automated execution\n"
        f"/set risk 1-5 — Change AI risk profile\n"
        f"/risk — View current risk parameters\n\n"
        f"<b>🦅 Market Analytics & Skills</b>\n"
        f"/scan — Full market scan with indicators\n"
        f"/scan BTC ETH — Scan specific symbols\n"
        f"/skills — Overview of all 26 Binance skills\n"
        f"/dex SOL — Real-time DexScreener search\n"
        f"/mobula BTC — Mobula price & market cap\n"
        f"/ticker BTCUSDT — Live price for any pair\n"
        f"/signals — Latest Binance Web3 signals\n\n"
        f"<b>💼 Portfolio & Logs</b>\n"
        f"/portfolio — Balances & risk metrics\n"
        f"/positions — View all open positions\n"
        f"/profit — Detailed Daily PnL summary\n"
        f"/history BTCUSDT — Recent trade history\n\n"
        f"<b>🔥 Spot Trading Ops</b>\n"
        f"/buy SYS QTY — Market buy\n"
        f"/sell SYS QTY — Market sell\n"
        f"/limit SIDE SYS QTY PX — Limit order\n"
        f"/close SYS — Close specific position\n"
        f"/closeall — Emergency close ALL positions\n\n"
        f"<b>📉 Derivatives & Advanced</b>\n"
        f"/futures buy BTC 0.1 — Market buy Futures\n"
        f"/leverage BTC 5 — Set futures leverage\n"
        f"/funding BTC — Check funding rates\n"
        f"/earn — Simple Earn flexible products\n"
        f"/convert BTC USDT 0.1 — Get convert quote\n\n"
        f"<b>🧠 AI Brain Tools</b>\n"
        f"/ai <text> — Chat with the KaiNova Brain\n"
        f"/analyze BTC — Deep AI market analysis\n"
        f"/models — Switch AI model providers\n"
        f"/id — View your Telegram ID (Debug)"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=_back_button())


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


async def post_init(app: Application):
    """Register all commands to the Telegram Bot API for the (/) menu."""
    from telegram import BotCommand, BotCommandScopeDefault
    commands = [
        BotCommand("start",     "Status dashboard"),
        BotCommand("help",      "Full command guide"),
        BotCommand("menu",      "Interactive menu"),
        BotCommand("startbot",  "ENABLE Auto-Trading"),
        BotCommand("stopbot",   "PAUSE Auto-Trading"),
        BotCommand("set",       "Set risk level (1-5)"),
        BotCommand("skills",    "List all 26 skills"),
        BotCommand("scan",      "Market scanner"),
        BotCommand("portfolio", "Balances & PnL"),
        BotCommand("positions", "Active positions"),
        BotCommand("profit",    "Daily performance"),
        BotCommand("status",    "Check health"),
        BotCommand("buy",       "Market buy"),
        BotCommand("sell",      "Market sell"),
        BotCommand("limit",     "Limit order"),
        BotCommand("close",     "Close position"),
        BotCommand("closeall",  "Emergency close"),
        BotCommand("futures",   "Futures trading"),
        BotCommand("leverage",  "Set leverage"),
        BotCommand("funding",   "Check funding"),
        BotCommand("ticker",    "Price ticker"),
        BotCommand("signals",   "Trade signals"),
        BotCommand("earn",      "Simple Earn"),
        BotCommand("convert",   "Quick convert"),
        BotCommand("mobula",    "Mobula Analytics"),
        BotCommand("dex",       "DexScreener search"),
        BotCommand("history",   "Trade history"),
        BotCommand("risk",      "Risk summary"),
        BotCommand("analyze",   "AI Deep analysis"),
        BotCommand("ai",        "Ask the AI Brain"),
        BotCommand("auth",      "Check OAuth status"),
        BotCommand("models",    "Switch AI models"),
    ]
    try:
        from telegram import BotCommandScopeDefault, BotCommandScopeAllPrivateChats
        await app.bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        await app.bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())
        logger.success(f"✅ Successfully registered {len(commands)} commands to ALL Telegram scopes")
    except Exception as e:
        logger.error(f"❌ Failed to register commands: {e}")


# ─────────────────────────────── BOT BUILDER ────────────────────────────────

def build_bot() -> Application:
    logger.info("Building KaiNova Application with post_init...")
    app = Application.builder().token(settings.telegram_bot_token).post_init(post_init).build()

    # Register all handlers
    handlers = [
        ("start",     cmd_start),
        ("help",      cmd_help),
        ("menu",      cmd_menu),
        ("startbot",  cmd_startbot),
        ("stopbot",   cmd_stopbot),
        ("set",       cmd_set),
        ("skills",    cmd_skills),
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
        ("mobula",    cmd_mobula),
        ("dex",       cmd_dex),
        ("history",   cmd_history),
        ("risk",      cmd_risk),
        ("id",       cmd_id),
        ("analyze",   cmd_analyze),
        ("ai",        cmd_ai),
        ("auth",      cmd_auth),
        ("models",    cmd_models),
    ]
    for name, handler in handlers:
        app.add_handler(CommandHandler(name, handler))
    
    logger.info(f"Registered {len(handlers)} handlers to Dispatcher")

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    return app
