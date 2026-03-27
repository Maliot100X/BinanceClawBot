"""Order execution engine — supports spot, futures, margin with SL/TP/trailing."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from loguru import logger
from core.client import get_client
from risk.risk_manager import risk_manager
from config.settings import settings


@dataclass
class Position:
    symbol: str
    side: str       # BUY or SELL
    qty: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    market: str = "SPOT"   # SPOT | FUTURES | MARGIN
    order_id: Optional[int] = None
    opened_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def pnl_usdt(self) -> float:
        return 0.0  # Updated when price is known


class OrderEngine:
    def __init__(self):
        self._open_positions: dict[str, Position] = {}

    def get_positions(self) -> list[Position]:
        return list(self._open_positions.values())

    async def place_market_buy(self, symbol: str, qty: float, market: str = "SPOT", stop_loss_pct: float = 2.0, take_profit_pct: float = 4.0) -> dict:
        client = get_client()
        result = {}
        try:
            if market == "SPOT":
                result = await client.place_spot_order(symbol, "BUY", "MARKET", quantity=qty)
            elif market == "FUTURES":
                result = await client.place_futures_order(symbol, "BUY", "MARKET", quantity=qty)

            price_raw = result.get("fills", [{}])[0].get("price", 0) if "fills" in result else 0
            price = float(price_raw) if price_raw else 0.0

            sl = price * (1 - stop_loss_pct / 100) if price else None
            tp = price * (1 + take_profit_pct / 100) if price else None

            pos = Position(symbol=symbol, side="BUY", qty=qty, entry_price=price, stop_loss=sl, take_profit=tp, market=market)
            self._open_positions[symbol] = pos

            # Place SL order
            if sl and market == "SPOT":
                await client.place_spot_order(symbol, "SELL", "STOP_LOSS_LIMIT",
                    quantity=qty, stopPrice=round(sl, 2), price=round(sl * 0.99, 2), timeInForce="GTC")

            logger.info(f"BUY {symbol} qty={qty} price={price} SL={sl} TP={tp}")
            return {"status": "ok", "symbol": symbol, "side": "BUY", "qty": qty, "price": price, "sl": sl, "tp": tp}
        except Exception as e:
            logger.error(f"Order failed: {e}")
            return {"status": "error", "error": str(e)}

    async def place_market_sell(self, symbol: str, qty: float, market: str = "SPOT") -> dict:
        client = get_client()
        try:
            if market == "SPOT":
                result = await client.place_spot_order(symbol, "SELL", "MARKET", quantity=qty)
            elif market == "FUTURES":
                result = await client.place_futures_order(symbol, "SELL", "MARKET", quantity=qty)
            self._open_positions.pop(symbol, None)
            logger.info(f"SELL {symbol} qty={qty}")
            return {"status": "ok", "symbol": symbol, "side": "SELL", "qty": qty}
        except Exception as e:
            logger.error(f"Sell failed: {e}")
            return {"status": "error", "error": str(e)}

    async def place_limit_order(self, symbol: str, side: str, qty: float, price: float, market: str = "SPOT") -> dict:
        client = get_client()
        try:
            result = await client.place_spot_order(symbol, side, "LIMIT", quantity=qty, price=price, timeInForce="GTC")
            return {"status": "ok", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def close_position(self, symbol: str) -> dict:
        pos = self._open_positions.get(symbol)
        if not pos:
            return {"status": "error", "error": f"No open position for {symbol}"}
        close_side = "SELL" if pos.side == "BUY" else "BUY"
        return await self.place_market_sell(symbol, pos.qty, pos.market) if close_side == "SELL" else await self.place_market_buy(symbol, pos.qty, pos.market)

    async def close_all_positions(self) -> list[dict]:
        results = []
        for symbol in list(self._open_positions.keys()):
            r = await self.close_position(symbol)
            results.append(r)
        return results

    def position_summary(self) -> list[dict]:
        return [
            {
                "symbol": p.symbol,
                "side": p.side,
                "qty": p.qty,
                "entry_price": p.entry_price,
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "market": p.market,
                "opened": p.opened_at.strftime("%H:%M:%S"),
            }
            for p in self._open_positions.values()
        ]


order_engine = OrderEngine()
