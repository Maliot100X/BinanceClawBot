"""Async Binance REST + WebSocket client wrapper."""
from __future__ import annotations
import asyncio
import hmac
import hashlib
import time
from typing import Any
import aiohttp
from loguru import logger
from config.settings import settings


BINANCE_BASE = "https://api.binance.com"
BINANCE_FUTURES_BASE = "https://fapi.binance.com"
BINANCE_COIN_FUTURES_BASE = "https://dapi.binance.com"
BINANCE_TESTNET_BASE = "https://testnet.binance.vision"


class BinanceClient:
    """Async Binance REST client with HMAC-SHA256 signing."""

    def __init__(self) -> None:
        import os
        # Prioritize os.environ for dynamic updates from Dashboard
        self.api_key = os.environ.get("BINANCE_API_KEY") or settings.binance_api_key
        self.secret = os.environ.get("BINANCE_SECRET_KEY") or settings.binance_secret_key
        self.testnet = settings.binance_testnet
        self.base = BINANCE_TESTNET_BASE if self.testnet else BINANCE_BASE
        self.futures_base = BINANCE_TESTNET_BASE if self.testnet else BINANCE_FUTURES_BASE
        self.coin_base = BINANCE_COIN_FUTURES_BASE
        self._session: aiohttp.ClientSession | None = None
        
        if self.api_key:
            logger.info(f"Binance Client initialized with key: ***{self.api_key[-4:]}")

    async def test_authentication(self) -> bool:
        """Pings account endpoint to verify keys."""
        try:
            await self.get_account()
            logger.success("✅ Binance API Authentication Successful")
            return True
        except Exception as e:
            logger.error(f"❌ Binance API Authentication Failed: {e}")
            return False

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"X-MBX-APIKEY": self.api_key}
            )
        return self._session

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000)
        query = "&".join(f"{k}={v}" for k, v in params.items())
        sig = hmac.new(
            self.secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        params["signature"] = sig
        return params

    async def _get(self, url: str, params: dict | None = None, signed: bool = False) -> Any:
        session = await self._get_session()
        p = self._sign(params or {}) if signed else (params or {})
        async with session.get(url, params=p) as r:
            r.raise_for_status()
            return await r.json()

    async def _post(self, url: str, params: dict | None = None, signed: bool = True) -> Any:
        session = await self._get_session()
        p = self._sign(params or {}) if signed else (params or {})
        async with session.post(url, params=p) as r:
            r.raise_for_status()
            return await r.json()

    async def _delete(self, url: str, params: dict | None = None, signed: bool = True) -> Any:
        session = await self._get_session()
        p = self._sign(params or {}) if signed else (params or {})
        async with session.delete(url, params=p) as r:
            r.raise_for_status()
            return await r.json()

    # ── Market Data ────────────────────────────────────────
    async def get_ticker(self, symbol: str) -> dict:
        return await self._get(f"{self.base}/api/v3/ticker/24hr", {"symbol": symbol})

    async def get_all_tickers(self) -> list:
        return await self._get(f"{self.base}/api/v3/ticker/24hr")

    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 200) -> list:
        return await self._get(
            f"{self.base}/api/v3/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )

    async def get_order_book(self, symbol: str, limit: int = 20) -> dict:
        return await self._get(f"{self.base}/api/v3/depth", {"symbol": symbol, "limit": limit})

    async def get_exchange_info(self) -> dict:
        return await self._get(f"{self.base}/api/v3/exchangeInfo")

    async def get_server_time(self) -> int:
        data = await self._get(f"{self.base}/api/v3/time")
        return data["serverTime"]

    # ── Account ────────────────────────────────────────────
    async def get_account(self) -> dict:
        return await self._get(f"{self.base}/api/v3/account", signed=True)

    async def get_balances(self) -> list[dict]:
        acc = await self.get_account()
        return [b for b in acc.get("balances", []) if float(b["free"]) > 0 or float(b["locked"]) > 0]

    async def get_nonnegligible_balances(self) -> list[dict]:
        return [b for b in await self.get_balances() if float(b["free"]) + float(b["locked"]) >= 0.001]

    # ── Spot Orders ────────────────────────────────────────
    async def place_spot_order(self, symbol: str, side: str, order_type: str, **kwargs) -> dict:
        params = {"symbol": symbol, "side": side, "type": order_type, **kwargs}
        if settings.dry_run:
            logger.info(f"[DRY RUN] Would place order: {params}")
            return {"status": "DRY_RUN", "params": params}
        return await self._post(f"{self.base}/api/v3/order", params)

    async def cancel_spot_order(self, symbol: str, order_id: int) -> dict:
        return await self._delete(f"{self.base}/api/v3/order", {"symbol": symbol, "orderId": order_id})

    async def get_open_orders(self, symbol: str | None = None) -> list:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return await self._get(f"{self.base}/api/v3/openOrders", params, signed=True)

    async def get_my_trades(self, symbol: str, limit: int = 50) -> list:
        return await self._get(f"{self.base}/api/v3/myTrades", {"symbol": symbol, "limit": limit}, signed=True)

    # ── Futures (USDS-M) ───────────────────────────────────
    async def get_futures_ticker(self, symbol: str) -> dict:
        return await self._get(f"{self.futures_base}/fapi/v1/ticker/24hr", {"symbol": symbol})

    async def get_futures_account(self) -> dict:
        return await self._get(f"{self.futures_base}/fapi/v2/account", signed=True)

    async def get_futures_positions(self) -> list:
        acc = await self.get_futures_account()
        return [p for p in acc.get("positions", []) if float(p.get("positionAmt", 0)) != 0]

    async def place_futures_order(self, symbol: str, side: str, order_type: str, **kwargs) -> dict:
        params = {"symbol": symbol, "side": side, "type": order_type, **kwargs}
        if settings.dry_run:
            logger.info(f"[DRY RUN] Would place futures order: {params}")
            return {"status": "DRY_RUN", "params": params}
        return await self._post(f"{self.futures_base}/fapi/v1/order", params)

    async def set_futures_leverage(self, symbol: str, leverage: int) -> dict:
        return await self._post(f"{self.futures_base}/fapi/v1/leverage", {"symbol": symbol, "leverage": min(leverage, settings.max_leverage)})

    async def set_futures_margin_type(self, symbol: str, margin_type: str) -> dict:
        return await self._post(f"{self.futures_base}/fapi/v1/marginType", {"symbol": symbol, "marginType": margin_type})

    async def close(self):
        if self._session:
            await self._session.close()


# Singleton
_client: BinanceClient | None = None


def get_client(force_new: bool = False) -> BinanceClient:
    global _client
    if _client is None or force_new:
        _client = BinanceClient()
    return _client
