"""Signal generator — aggregates strategy signals into BUY/SELL/HOLD."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from signals.indicators import IndicatorSnapshot


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradeSignal:
    symbol: str
    signal: Signal
    confidence: float  # 0-100
    reason: str
    price: float
    indicators: IndicatorSnapshot


def _breakout_score(ind: IndicatorSnapshot) -> float:
    score = 0.0
    if ind.close > ind.ema20 and ind.ema20 > ind.ema50:
        score += 30
    if ind.volume > ind.vol_ma * 1.8:
        score += 30
    if ind.macd > ind.macd_signal and ind.macd_hist > 0:
        score += 20
    if ind.rsi > 55:
        score += 20
    return score


def _momentum_score(ind: IndicatorSnapshot) -> float:
    score = 0.0
    if ind.macd > ind.macd_signal:
        score += 35
    if 50 < ind.rsi < 75:
        score += 35
    if ind.trend == "UP":
        score += 30
    return score


def _mean_reversion_score(ind: IndicatorSnapshot) -> float:
    score = 0.0
    if ind.rsi < 32:  # oversold
        score += 50
    if ind.close < ind.vwap * 0.98:
        score += 30
    if ind.close < ind.ema20:
        score += 20
    return score


def _whale_score(ind: IndicatorSnapshot) -> float:
    score = 0.0
    if ind.volume > ind.vol_ma * 3.0:
        score += 60
    if ind.trend == "UP" and ind.volume > ind.vol_ma * 2:
        score += 40
    return score


def generate_signal(ind: IndicatorSnapshot) -> TradeSignal:
    """Combine all strategies into one trade signal."""
    buy_scores: list[tuple[str, float]] = [
        ("Breakout", _breakout_score(ind)),
        ("Momentum", _momentum_score(ind)),
        ("MeanReversion", _mean_reversion_score(ind)),
        ("WhaleActivity", _whale_score(ind)),
    ]

    best_name, best_score = max(buy_scores, key=lambda x: x[1])
    avg_score = sum(s for _, s in buy_scores) / len(buy_scores)

    # Sell signals (inverse)
    sell_rsi = ind.rsi > 75
    sell_macd = ind.macd < ind.macd_signal and ind.macd_hist < -0.001
    sell_trend = ind.trend == "DOWN"
    sell_score = sum([sell_rsi * 40, sell_macd * 35, sell_trend * 25])

    if sell_score > 60:
        reason = " | ".join(filter(None, [
            "Overbought RSI" if sell_rsi else "",
            "MACD bearish" if sell_macd else "",
            "Downtrend" if sell_trend else "",
        ]))
        return TradeSignal(ind.symbol, Signal.SELL, sell_score, reason, ind.close, ind)

    if best_score > 65:
        return TradeSignal(ind.symbol, Signal.BUY, best_score, f"{best_name} ({best_score:.0f}%)", ind.close, ind)

    return TradeSignal(ind.symbol, Signal.HOLD, avg_score, "No clear signal", ind.close, ind)
