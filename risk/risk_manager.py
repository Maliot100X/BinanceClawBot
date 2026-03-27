"""Risk management: enforces position sizing, daily loss, and leverage limits."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from loguru import logger
from config.settings import settings


@dataclass
class RiskState:
    daily_loss_usdt: float = 0.0
    daily_pnl_usdt: float = 0.0
    trade_date: date = field(default_factory=date.today)
    bot_active: bool = True

    def reset_if_new_day(self):
        today = date.today()
        if self.trade_date != today:
            self.daily_loss_usdt = 0.0
            self.daily_pnl_usdt = 0.0
            self.trade_date = today


class RiskManager:
    def __init__(self):
        self.state = RiskState()
        self._max_pos_pct = settings.max_position_size_pct / 100
        self._max_daily_loss_pct = settings.max_daily_loss_pct / 100
        self._max_lev = settings.max_leverage

    def check_daily_loss(self, portfolio_value: float) -> bool:
        """Returns True if trading is allowed (daily loss limit not hit)."""
        self.state.reset_if_new_day()
        loss_pct = abs(self.state.daily_loss_usdt) / max(portfolio_value, 1)
        if loss_pct >= self._max_daily_loss_pct:
            logger.warning(
                f"Daily loss limit reached: {loss_pct:.1%} >= {self._max_daily_loss_pct:.1%}"
            )
            return False
        return True

    def calc_position_size(self, portfolio_value: float, price: float) -> float:
        """Returns quantity to trade based on max position size rule."""
        max_usdt = portfolio_value * self._max_pos_pct
        max_usdt = min(max_usdt, settings.default_trade_usdt)
        return round(max_usdt / price, 6) if price > 0 else 0.0

    def validate_leverage(self, leverage: int) -> int:
        return min(leverage, self._max_lev)

    def record_trade_result(self, pnl: float):
        self.state.daily_pnl_usdt += pnl
        if pnl < 0:
            self.state.daily_loss_usdt += abs(pnl)

    def is_active(self) -> bool:
        return self.state.bot_active

    def set_active(self, active: bool):
        self.state.bot_active = active
        logger.info(f"Bot {'ACTIVATED' if active else 'PAUSED'} by risk manager")

    def summary(self) -> dict:
        return {
            "active": self.state.bot_active,
            "daily_pnl": round(self.state.daily_pnl_usdt, 2),
            "daily_loss": round(self.state.daily_loss_usdt, 2),
            "max_daily_loss_pct": settings.max_daily_loss_pct,
            "max_position_pct": settings.max_position_size_pct,
            "max_leverage": self._max_lev,
        }


risk_manager = RiskManager()
