"""RSI, MACD, EMA, VWAP, Volume indicators — pure pandas/numpy."""
from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class IndicatorSnapshot:
    symbol: str
    close: float
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    ema20: float
    ema50: float
    ema200: float
    vwap: float
    volume: float
    vol_ma: float
    trend: str  # "UP", "DOWN", "NEUTRAL"
    signal_strength: float  # 0-100


def klines_to_df(raw: list) -> pd.DataFrame:
    """Convert Binance klines list to DataFrame."""
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore",
    ])
    for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
        df[col] = pd.to_numeric(df[col])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df.set_index("open_time")


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def calc_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calc_vwap(df: pd.DataFrame) -> pd.Series:
    typical = (df["high"] + df["low"] + df["close"]) / 3
    cum_vol = df["volume"].cumsum()
    cum_pv = (typical * df["volume"]).cumsum()
    return cum_pv / cum_vol.replace(0, np.nan)


def compute_indicators(symbol: str, raw_klines: list) -> Optional[IndicatorSnapshot]:
    if not raw_klines or len(raw_klines) < 50:
        return None

    df = klines_to_df(raw_klines)
    close = df["close"]

    rsi_s = calc_rsi(close)
    macd_s, sig_s, hist_s = calc_macd(close)
    ema20 = calc_ema(close, 20)
    ema50 = calc_ema(close, 50)
    ema200 = calc_ema(close, 200)
    vwap = calc_vwap(df)
    vol_ma = df["volume"].rolling(20).mean()

    rsi_val = float(rsi_s.iloc[-1])
    macd_val = float(macd_s.iloc[-1])
    sig_val = float(sig_s.iloc[-1])
    hist_val = float(hist_s.iloc[-1])
    ema20_val = float(ema20.iloc[-1])
    ema50_val = float(ema50.iloc[-1])
    ema200_val = float(ema200.iloc[-1]) if len(df) >= 200 else ema50_val
    vwap_val = float(vwap.iloc[-1])
    vol_val = float(df["volume"].iloc[-1])
    vol_ma_val = float(vol_ma.iloc[-1])
    price = float(close.iloc[-1])

    # Trend
    if ema20_val > ema50_val > ema200_val and price > vwap_val:
        trend = "UP"
    elif ema20_val < ema50_val < ema200_val and price < vwap_val:
        trend = "DOWN"
    else:
        trend = "NEUTRAL"

    # Signal strength 0-100
    score = 50.0
    if trend == "UP":
        score += 20
    elif trend == "DOWN":
        score -= 20
    if macd_val > sig_val:
        score += 10
    else:
        score -= 10
    if 30 < rsi_val < 70:
        score += 5
    elif rsi_val < 30:
        score += 15  # oversold → bullish
        if trend == "DOWN":
            score -= 20
    elif rsi_val > 70:
        score -= 15  # overbought → bearish
    if vol_val > vol_ma_val * 1.5:
        score = score * 1.1  # volume confirmation

    return IndicatorSnapshot(
        symbol=symbol,
        close=price,
        rsi=rsi_val,
        macd=macd_val,
        macd_signal=sig_val,
        macd_hist=hist_val,
        ema20=ema20_val,
        ema50=ema50_val,
        ema200=ema200_val,
        vwap=vwap_val,
        volume=vol_val,
        vol_ma=vol_ma_val,
        trend=trend,
        signal_strength=min(max(score, 0), 100),
    )
