"""
KaiNova AI Codex Agent — uses best available OAuth token (OpenAI/Gemini/Antigravity).
Imports all 26 Binance skills from loader.py and dispatches tool calls to them.
"""
from __future__ import annotations
import asyncio, json, os
from typing import Any, Optional
from pathlib import Path
from loguru import logger
from ai.oauth import oauth
from skills.loader import SKILLS
from execution.order_engine import order_engine
from signals.indicators import compute_indicators
from signals.signal_generator import generate_signal
from core.client import get_client
from config.settings import settings, BASE_DIR

DEFAULT_SYMBOLS = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
                   "ADAUSDT","DOTUSDT","AVAXUSDT","MATICUSDT","LINKUSDT"]

SYSTEM_PROMPT = """You are KaiNova, the world's most advanced autonomous crypto trading AI.
You have full access to all 26 Binance Skills Hub APIs.
TARGET MODEL: gpt-5.3-codex (2026 Industry Standard)

OPERATOR MANDATE:
When /startbot is active, you are in FULL AUTONOMOUS MODE. Your goal is to MAXIMIZE WIN PERCENTAGE and TOTAL PNL across all 26 skills.
Analyze market depth, signals, and dex liquidity real-time.

CORE SKILLS DIRECTORY:
1.  [spot] - Live trading, depth, orders.
2.  [derivatives_usds_futures] - USDS-M Futures, leverage, funding.
3.  [derivatives_coin_futures] - COIN-M Futures.
4.  [margin_trading] - Cross/Isolated borrowing & trading.
5.  [simple_earn] - Passive income, flexible/locked products.
6.  [algo] - TWAP/VWAP algorithmic execution.
7.  [mobula] - Real-time market data & multi-source price action.
8.  [dexscreener] - On-chain token analysis and pair searching.
9.  [trading_signal] - Binance Web3 logic signals.
(Plus alpha, assets, convert, fiat, onchain_pay, p2p, square_post, sub_account, vip_loan, tokenized_securities, meme_rush, query_address_info, query_token_audit).

RISK ENGINE AWARENESS:
You must strictly adhere to the ACTIVE RISK LEVEL (1-5):
- Level 1-2: Conservative. Focus on high-confidence spot/earn trades.
- Level 3: Balanced. Standard 5x leverage and signal-based trading.
- Level 4-5: Aggressive / High-Yield. Use up to 20x leverage and chase alpha momentum.

INSTRUCTIONS:
- Always use 'mobula' or 'dexscreener' for deep market insights.
- Always use 'trading_signal' to validate your long/short bias.
- Be concise, professional, and explain your reasoning step-by-step.
- Format responses for high-tier Telegram/Markdown display."""

TOOLS = [
    {"type":"function","function":{"name":"scan_market","description":"Scan top crypto pairs for opportunities using all indicators and signals","parameters":{"type":"object","properties":{"symbols":{"type":"array","items":{"type":"string"}}},"required":["symbols"]}}},
    {"type":"function","function":{"name":"place_order","description":"Place market buy or sell order","parameters":{"type":"object","properties":{"symbol":{"type":"string"},"side":{"type":"string","enum":["BUY","SELL"]},"qty":{"type":"number"},"market":{"type":"string","enum":["SPOT","FUTURES"],"default":"SPOT"}},"required":["symbol","side","qty"]}}},
    {"type":"function","function":{"name":"close_position","description":"Close open position","parameters":{"type":"object","properties":{"symbol":{"type":"string"}},"required":["symbol"]}}},
    {"type":"function","function":{"name":"portfolio_status","description":"Get balances, positions, PnL","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"get_signals","description":"Get trading signals for symbols","parameters":{"type":"object","properties":{"symbols":{"type":"array","items":{"type":"string"}}},"required":["symbols"]}}},
    {"type":"function","function":{"name":"skill_call","description":"Call any of the 26 Binance skills","parameters":{"type":"object","properties":{"skill":{"type":"string"},"method":{"type":"string"},"kwargs":{"type":"object"}},"required":["skill","method"]}}},
]


async def _scan(symbols: list[str]) -> dict:
    client = await get_client()
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
    client = await get_client()
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
    """
    OpenClaw-Compatible Agentic Codex Heartbeat.
    Supports dynamic provider/model patterns (e.g. 'openai/gpt-5.3-codex').
    """
    def __init__(self, model: str = "openai/gpt-5.3-codex"):
        self._set_initial_model(model)
        self.client = None
        self.skills = SKILLS
        self.tools = self._build_tools()
        self._history = []

    def _set_initial_model(self, model: str):
        # Load from session if exists, else use default
        sess_path = BASE_DIR / "session.json"
        if sess_path.exists():
            try:
                with open(sess_path, "r") as f:
                    sess = json.load(f)
                    self._model = sess.get("model", model)
            except: self._model = model
        else:
            self._model = model
            
    def set_model(self, model_str: str):
        """Sets the real-time brain target (e.g. 'openai/gpt-4o')"""
        self._model = model_str
        # Persist to session for ecosystem sync
        sess_path = BASE_DIR / "session.json"
        sess = {}
        if sess_path.exists():
            try:
                with open(sess_path, "r") as f: sess = json.load(f)
            except: pass
        sess["model"] = model_str
        with open(sess_path, "w") as f:
            json.dump(sess, f, indent=2)
        logger.success(f"Brain Sync: Active model switched to {model_str}")

    @property
    def model_id(self) -> str:
        # Returns the core model name (e.g. 'gpt-4o' from 'openai/gpt-4o')
        if "/" in self._model:
            return self._model.split("/")[-1]
        return self._model

    async def fetch_available_models(self) -> list[str]:
        """Fetch actual models available to the current active provider."""
        provider, token = oauth.best_token()
        if not provider or not token: return []
        
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                if provider == "openai":
                    r = await c.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {token}"})
                    data = r.json().get("data", [])
                    return sorted([m["id"] for m in data if "gpt" in m["id"] or "o1" in m["id"]], reverse=True)
                elif provider == "groq":
                    r = await c.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {token}"})
                    return sorted([m["id"] for m in r.json().get("data", [])])
                elif provider == "deepseek":
                    r = await c.get("https://api.deepseek.com/models", headers={"Authorization": f"Bearer {token}"})
                    return sorted([m["id"] for m in r.json().get("data", [])])
                elif provider == "openrouter":
                    r = await c.get("https://openrouter.ai/api/v1/models")
                    return sorted([m["id"] for m in r.json().get("data", [])])
                elif provider == "gemini":
                    # Google doesn't have a clean 'list' endpoint for models via simple API key easily
                    return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-pro-exp-02-05"]
                elif provider == "antigravity":
                    return [
                        "antigravity-gemini-3-pro", "antigravity-gemini-3.1-pro",
                        "antigravity-gemini-3-flash", "antigravity-claude-sonnet-4-6",
                        "antigravity-claude-opus-4-6-thinking",
                        "gemini-2.5-flash", "gemini-2.5-pro",
                        "gemini-3-flash-preview", "gemini-3-pro-preview",
                    ]
                elif provider == "ollama":
                    url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
                    r = await c.get(f"{url}/api/tags")
                    return [m["name"] for m in r.json().get("models", [])]
                elif provider == "nvidia":
                    nvidia_url = "https://integrate.api.nvidia.com/v1"
                    r = await c.get(f"{nvidia_url}/models", headers={"Authorization": f"Bearer {token}"})
                    if r.status_code == 200:
                        return [m["id"] for m in r.json().get("data", [])]
                    return [
                        "deepseek-ai/deepseek-v3.1", "deepseek-ai/deepseek-v3.2",
                        "minimaxai/minimax-m2.5", "z-ai/glm5", "moonshotai/kimi-k2.5",
                    ]
        except Exception as e:
            logger.error(f"Failed to fetch models for {provider}: {e}")
        return [self._model]

    async def pull_model(self, model_name: str) -> bool:
        """Tell Ollama to pull a new model."""
        url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        import httpx
        logger.info(f"Ollama: Pulling model {model_name}...")
        try:
            async with httpx.AsyncClient(timeout=None) as c:
                async with c.stream("POST", f"{url}/api/pull", json={"name": model_name}) as r:
                    async for line in r.aiter_lines():
                        if not line: continue
                        data = json.loads(line)
                        if "status" in data:
                            logger.info(f"Ollama Pull: {data['status']}")
            return True
        except Exception as e:
            logger.error(f"Ollama Pull Failed: {e}")
            return False

    def _build_tools(self) -> list[dict]:
        # This method needs to be implemented based on the TOOLS global variable
        # For now, returning the global TOOLS directly
        return TOOLS

    async def _get_session(self) -> dict | None:
        """Load tokens from the CLI session file."""
        sess_path = BASE_DIR / "session.json"
        
        if not sess_path.exists():
            logger.warning(f"AI Agent: session.json not found at {sess_path}")
            return None
            
        try:
            import json
            with open(sess_path, "r") as f:
                data = json.load(f)
                if data.get("access_token"):
                    logger.success(f"AI Agent: Loaded bridged session from {sess_path}")
                return data
        except Exception as e:
            logger.error(f"AI Agent: Failed to read session.json: {e}")
            return None

    async def think(self, user_msg: str) -> str:
        # Use oauth.best_token() as the single source of truth for provider + token
        provider, token = oauth.best_token()

        if not token:
            return "⚠️ No AI provider configured.\n\nOptions:\n• Add a free API key: GROQ_API_KEY in .env (https://console.groq.com)\n• Run: py codex.py login\n• Or use the CMD dashboard: py provider_setup.py"

        logger.info(f"AI Brain: provider={provider}, model={self._model}")

        import httpx
        self._history.append({"role": "user", "content": user_msg})
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self._history[-20:]
        
        # ── Configure Provider Endpoints ─────────────────────────────────────
        # ── Configure Provider SDKs / Endpoints ──────────────────────────────
        model_for_request = self.model_id
        
        # Mapping 'Codex' placeholder to real high-reasoning models
        CODEX_MAPPING = {
            "openai": "gpt-4o",
            "groq": "llama-3.3-70b-versatile",
            "deepseek": "deepseek-chat",
            "gemini": "gemini-2.0-flash",
            "openrouter": "anthropic/claude-3.5-sonnet",
            "ollama": "llama3.3",
            "antigravity": "gemini-2.5-flash",
            "nvidia": "deepseek-ai/deepseek-v3.1",
        }
        
        # Override for specific cloud model naming if needed
        if provider == "ollama" and "deepseek" in user_msg.lower() and "cloud" in model_for_request.lower():
             logger.info("Ollama Cloud: DeepSeek requested, ensuring header sync.")

        # ── Execution Loop ──────────────────────────────────────────────────
        openai_compat = True
        try:
            if provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=token)
                model = genai.GenerativeModel(model_name=model_for_request)
                user_msg_with_sys = f"SYSTEM: {SYSTEM_PROMPT}\n\nUSER: {user_msg}"
                response = await asyncio.to_thread(model.generate_content, user_msg_with_sys)
                content = response.text
                self._history.append({"role": "assistant", "content": content})
                return content

            elif provider == "groq":
                from groq import Groq
                client = Groq(api_key=token)
                chat_completion = await asyncio.to_thread(
                    client.chat.completions.create,
                    messages=messages,
                    model=model_for_request,
                    tools=TOOLS,
                    tool_choice="auto"
                )
                resp = chat_completion.model_dump()
                # Continue to OpenAI-compatible parsing below
                
            elif provider == "openai":
                endpoint = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                payload = {"model": model_for_request if "codex" not in model_for_request else "gpt-4o-mini", 
                           "messages": messages, "tools": TOOLS, "tool_choice": "auto"}
                openai_compat = "REST"
            elif provider == "deepseek":
                endpoint = "https://api.deepseek.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                payload = {"model": "deepseek-chat", "messages": messages, "tools": TOOLS, "tool_choice": "auto"}
                openai_compat = "REST"
            elif provider == "openrouter":
                endpoint = "https://openrouter.ai/api/v1/chat/completions"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "HTTP-Referer": "https://github.com/Maliot100X/BinanceClawBot"}
                payload = {"model": model_for_request if "/" in model_for_request else f"openai/{model_for_request}", "messages": messages, "tools": TOOLS}
                openai_compat = "REST"
            elif provider == "ollama":
                ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
                endpoint = f"{ollama_url}/v1/chat/completions"
                headers = {"Content-Type": "application/json"}
                # Check for explicit OLLAMA_API_KEY in .env
                ollama_key = os.environ.get("OLLAMA_API_KEY")
                if ollama_key and ollama_key not in ("", "your_key_here"):
                    headers["Authorization"] = f"Bearer {ollama_key}"
                elif token and token != "local":
                    headers["Authorization"] = f"Bearer {token}"
                
                payload = {"model": model_for_request, "messages": messages}
                openai_compat = "REST"
            elif provider == "antigravity":
                # Route through Google's generativelanguage API with OAuth Bearer token
                ag_model = model_for_request
                if "codex" in ag_model.lower() or "gpt" in ag_model.lower():
                    ag_model = CODEX_MAPPING.get("antigravity", "gemini-2.5-flash")
                
                ag_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{ag_model}:generateContent"
                ag_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
                # Convert OpenAI messages format to Gemini format
                gemini_contents = []
                for m in messages:
                    role = "user" if m["role"] in ("user", "system") else "model"
                    gemini_contents.append({"role": role, "parts": [{"text": m["content"]}]})
                ag_payload = {
                    "contents": gemini_contents,
                    "generationConfig": {"maxOutputTokens": 4096}
                }
                try:
                    async with httpx.AsyncClient(timeout=60.0) as c:
                        r = await c.post(ag_endpoint, headers=ag_headers, json=ag_payload)
                        if r.status_code == 200:
                            resp = r.json()
                            text = resp["candidates"][0]["content"]["parts"][0]["text"]
                            self._history.append({"role": "assistant", "content": text})
                            return text
                        else:
                            logger.error(f"Antigravity API error: {r.status_code} {r.text[:200]}")
                            return f"⚠️ Antigravity API error: {r.status_code}"
                except Exception as e:
                    logger.error(f"Antigravity request failed: {e}")
                    return f"⚠️ Antigravity error: {str(e)}"
            elif provider == "nvidia":
                nvidia_model = model_for_request
                if "codex" in nvidia_model.lower() or "gpt" in nvidia_model.lower():
                    nvidia_model = CODEX_MAPPING.get("nvidia", "deepseek-ai/deepseek-v3.1")
                endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                payload = {"model": nvidia_model, "messages": messages, "max_tokens": 4096}
                openai_compat = "REST"
            else:
                return f"⚠️ Unknown provider: {provider}"
        except Exception as e:
            logger.error(f"AI Core Failure ({provider}): {e}")
            return f"⚠️ {provider.upper()} Engine error: {str(e)}"

        if openai_compat == "REST":
            for _ in range(5):
                logger.info(f"[AI:{provider}] Requesting REST: {endpoint}")
                async with httpx.AsyncClient(timeout=60.0) as c:
                    r = await c.post(endpoint, headers=headers, json=payload)
                    if r.status_code != 200: return f"⚠️ {provider} API error: {r.status_code}"
                    resp = r.json()
                
                # Standard OpenAI Result Parsing
                choice = resp["choices"][0]
                msg = choice["message"]
                if choice.get("finish_reason") == "tool_calls" or "tool_calls" in msg:
                    messages.append(msg)
                    tool_msgs = []
                    for tc in msg.get("tool_calls", []):
                        fn, args = tc["function"]["name"], json.loads(tc["function"]["arguments"])
                        res = await _dispatch(fn, args)
                        tool_msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(res)})
                    messages.extend(tool_msgs)
                    payload["messages"] = messages
                else:
                    self._history.append({"role": "assistant", "content": msg["content"]})
                    return msg["content"]
        
        elif openai_compat == True: # Groq / SDK bridge
            choice = resp["choices"][0]
            msg = choice["message"]
            if choice.get("finish_reason") == "tool_calls":
                 return "⚠️ Tool calls via Groq SDK pending full implementation."
            self._history.append({"role": "assistant", "content": msg["content"]})
            return msg["content"]
        return "⚠️ AI loop limit reached."

    def clear(self): self._history = []


codex_agent = CodexAgent()
