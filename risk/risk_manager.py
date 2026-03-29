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
        self.risk_level = 3  # Default: Balanced
        self._apply_level_params()

    def _apply_level_params(self):
        """Maps Level 1-5 to actual risk parameters."""
        # [PosSize%, DailyLoss%, MaxLev]
        levels = {
            1: (0.02, 0.03, 2),   # Conservative
            2: (0.05, 0.05, 3),   # Low
            3: (0.10, 0.10, 5),   # Balanced (Original Default)
            4: (0.20, 0.15, 10),  # High-Yield
            5: (0.40, 0.25, 20),  # Aggressive (MAX)
        }
        p, dl, l = levels.get(self.risk_level, (0.10, 0.10, 5))
        self._max_pos_pct = p
        self._max_daily_loss_pct = dl
        self._max_lev = l

    def set_risk_level(self, level: int) -> bool:
        if 1 <= level <= 5:
            self.risk_level = level
            self._apply_level_params()
            logger.info(f"Risk level set to {level}: Pos={self._max_pos_pct:.0%}, Loss={self._max_daily_loss_pct:.0%}, Lev={self._max_lev}x")
            return True
        return False

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
        # Still cap at default trade USDT if it exists, to avoid unintended huge orders
        max_limit = getattr(settings, 'default_trade_usdt', 100)
        final_usdt = min(max_usdt, max_limit * (self.risk_level / 1.5)) # Scale cap by level
        return round(final_usdt / price, 6) if price > 0 else 0.0

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
            "risk_level": self.risk_level,
            "daily_pnl": round(self.state.daily_pnl_usdt, 2),
            "daily_loss": round(self.state.daily_loss_usdt, 2),
            "max_daily_loss_pct": round(self._max_daily_loss_pct * 100, 1),
            "max_position_pct": round(self._max_pos_pct * 100, 1),
            "max_leverage": self._max_lev,
        }


risk_manager = RiskManager()
