"""
KaiNova AI Codex Agent — uses best available OAuth token (OpenAI/Gemini/Antigravity).
Imports all 26 Binance skills from loader.py and dispatches tool calls to them.
"""
from __future__ import annotations
import asyncio, json
from typing import Any
from loguru import logger
from ai.oauth import oauth
from skills.loader import SKILLS
from execution.order_engine import order_engine
from signals.indicators import compute_indicators
from signals.signal_generator import generate_signal
from core.client import get_client
from config.settings import settings

DEFAULT_SYMBOLS = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
                   "ADAUSDT","DOTUSDT","AVAXUSDT","MATICUSDT","LINKUSDT"]

SYSTEM_PROMPT = """You are KaiNova, the world's most advanced autonomous crypto trading AI.
You have full access to all 26 Binance Skills Hub APIs (spot, futures, margin, algo, earn, defi, web3).
Risk rules you MUST enforce on every trade:
- Max position: 5% of portfolio
- Max daily loss: 10% circuit breaker
- Max leverage: 5x
- Every trade requires stop loss
Think step by step. Be concise. Format responses for Telegram."""

TOOLS = [
    {"type":"function","function":{"name":"scan_market","description":"Scan top crypto pairs for opportunities using all indicators and signals","parameters":{"type":"object","properties":{"symbols":{"type":"array","items":{"type":"string"}}},"required":["symbols"]}}},
    {"type":"function","function":{"name":"place_order","description":"Place market buy or sell order","parameters":{"type":"object","properties":{"symbol":{"type":"string"},"side":{"type":"string","enum":["BUY","SELL"]},"qty":{"type":"number"},"market":{"type":"string","enum":["SPOT","FUTURES"],"default":"SPOT"}},"required":["symbol","side","qty"]}}},
    {"type":"function","function":{"name":"close_position","description":"Close open position","parameters":{"type":"object","properties":{"symbol":{"type":"string"}},"required":["symbol"]}}},
    {"type":"function","function":{"name":"portfolio_status","description":"Get balances, positions, PnL","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"get_signals","description":"Get trading signals for symbols","parameters":{"type":"object","properties":{"symbols":{"type":"array","items":{"type":"string"}}},"required":["symbols"]}}},
    {"type":"function","function":{"name":"skill_call","description":"Call any of the 26 Binance skills","parameters":{"type":"object","properties":{"skill":{"type":"string"},"method":{"type":"string"},"kwargs":{"type":"object"}},"required":["skill","method"]}}},
]


async def _scan(symbols: list[str]) -> dict:
    client = get_client()
    results = []
    for sym in symbols[:10]:
        try:
            klines = await client.get_klines(sym, "1h", 200)
            ind = compute_indicators(sym, klines)
            if ind:
                sig = generate_signal(ind)
                results.append({"symbol": sym, "price": ind.close, "signal": sig.signal.value,
                    "confidence": round(sig.confidence, 1), "rsi": round(ind.rsi, 1),
                    "trend": ind.trend, "reason": sig.reason})
        except Exception as e:
            logger.debug(f"scan skip {sym}: {e}")
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return {"scan_results": results}


async def _portfolio() -> dict:
    client = get_client()
    try:
        balances = await client.get_nonnegligible_balances()
        positions = order_engine.position_summary()
        from risk.risk_manager import risk_manager
        return {"balances": balances[:10], "open_positions": positions, "risk": risk_manager.summary()}
    except Exception as e:
        return {"error": str(e)}


async def _skill_call(skill: str, method: str, kwargs: dict) -> Any:
    s = SKILLS.get(skill)
    if not s: return {"error": f"Unknown skill: {skill}"}
    fn = getattr(s, method, None)
    if not fn: return {"error": f"Unknown method {method} on {skill}"}
    return await fn(**kwargs)


async def _dispatch(name: str, args: dict) -> Any:
    if name == "scan_market": return await _scan(args.get("symbols", DEFAULT_SYMBOLS))
    if name == "get_signals": return await _scan(args.get("symbols", DEFAULT_SYMBOLS))
    if name == "portfolio_status": return await _portfolio()
    if name == "close_position": return await order_engine.close_position(args["symbol"])
    if name == "skill_call": return await _skill_call(args["skill"], args["method"], args.get("kwargs", {}))
    if name == "place_order":
        side, sym, qty, mkt = args["side"], args["symbol"], args["qty"], args.get("market","SPOT")
        if side == "BUY": return await order_engine.place_market_buy(sym, qty, mkt)
        return await order_engine.place_market_sell(sym, qty, mkt)
    return {"error": f"Unknown tool: {name}"}


class CodexAgent:
    def __init__(self):
        self._history: list[dict] = []

    async def think(self, user_msg: str) -> str:
        # Prioritize CLI-bridged session.json (OpenAI)
        import os, json
        provider, token = None, None
        
        if os.path.exists("session.json"):
            try:
                with open("session.json", "r") as f:
                    sess = json.load(f)
                    if sess.get("access_token"):
                        provider = "openai"
                        token = sess["access_token"]
                        logger.info("Using bridged OpenAI session from session.json")
            except: pass
            
        if not token:
            provider, token = oauth.best_token()

        if not token:
            return "⚠️ No AI authenticated. Use /auth or py codex.py login to connect."

        import httpx
        self._history.append({"role": "user", "content": user_msg})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self._history[-20:]
        
        # ── Configure Provider Endpoints ─────────────────────────────────────
        if provider == "openai":
            endpoint = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o", "messages": messages, "tools": TOOLS, "tool_choice": "auto"}
        elif provider == "openrouter":
            endpoint = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "HTTP-Referer": "https://github.com/Maliot100X/BinanceClawBot"}
            payload = {"model": "anthropic/claude-3.5-sonnet", "messages": messages, "tools": TOOLS}
        elif provider == "groq":
            endpoint = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {"model": "llama3-70b-8192", "messages": messages, "tools": TOOLS}
        elif provider == "ollama":
            endpoint = "http://localhost:11434/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
            payload = {"model": "llama3", "messages": messages}
        else:
            # Gemini / Antigravity via Google Generative Language API
            model_name = "gemini-3.1-pro-search" if "antigravity" in provider else "gemini-1.5-pro"
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            # Google AI 1.5+ format
            payload = {
                "contents": [{"role": m["role"], "parts": [{"text": m["content"]}]} for m in messages],
                "tools": [{"function_declarations": [t["function"] for t in TOOLS]}],
            }

        for _ in range(5):
            logger.info(f"[AI:{provider}] Reaching endpoint: {endpoint}")
            async with httpx.AsyncClient(timeout=20.0) as c:
                try:
                    r = await c.post(endpoint, headers=headers, json=payload)
                    if r.status_code != 200:
                        logger.error(f"AI Error ({provider}): {r.text}")
                        return f"⚠️ AI error: {r.status_code}"
                    resp = r.json()
                except httpx.TimeoutException:
                    logger.error(f"AI Timeout ({provider})")
                    return "⚠️ AI response timed out (20s)."
                except Exception as e:
                    logger.error(f"AI Request Failed: {e}")
                    return f"⚠️ AI Request failed: {str(e)}"
                
            if provider == "openai":
                choice = resp["choices"][0]
                msg = choice["message"]
                messages.append(msg)
                if choice["finish_reason"] == "tool_calls":
                    tool_msgs = []
                    for tc in msg.get("tool_calls", []):
                        fn, fn_args = tc["function"]["name"], json.loads(tc["function"]["arguments"])
                        logger.info(f"[AI:{provider}] → {fn}({fn_args})")
                        result = await _dispatch(fn, fn_args)
                        tool_msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result, default=str)})
                    messages.extend(tool_msgs)
                    payload["messages"] = messages # Update payload for next loop
                else:
                    content = msg.get("content", "")
                    self._history.append({"role": "assistant", "content": content})
                    return content
            else:
                # Google format response handling
                candidate = resp["candidates"][0]
                msg = candidate["content"]
                # Convert back to common format for history
                text = "".join(p.get("text", "") for p in msg["parts"])
                if "tool_calls" in candidate or any("function_call" in p for p in msg["parts"]):
                    # Simplified tool loop for Google
                    for part in msg["parts"]:
                        if "function_call" in part:
                            fc = part["function_call"]
                            fn, fn_args = fc["name"], fc["args"]
                            logger.info(f"[AI:{provider}] → {fn}({fn_args})")
                            result = await _dispatch(fn, fn_args)
                            # Add response back to payload
                            payload["contents"].append(msg) # Assistant message
                            payload["contents"].append({
                                "role": "function",
                                "parts": [{"function_response": {"name": fn, "response": {"result": result}}}]
                            })
                    continue # Loop back
                else:
                    self._history.append({"role": "assistant", "content": text})
                    return text
        return "⚠️ AI loop limit reached."

    def clear(self): self._history = []


codex_agent = CodexAgent()
