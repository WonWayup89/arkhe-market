"""
technical_agent.py – Expert technical-analysis signal generator.

Computes a rich indicator set and produces scored buy / sell signals
with adaptive thresholds per market type (crypto-stable, crypto-alt,
stock, futures).
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict


PROFILES: Dict[str, dict] = {
    "stable": {
        "ma_short": 12, "ma_long": 40,
        "min_vol": 0.002, "max_vol": 0.05,
        "buy_thresh": 3, "sell_thresh": 2,
        "stop_mult": 1.2, "min_stop_pct": 0.005,
    },
    "alt": {
        "ma_short": 10, "ma_long": 30,
        "min_vol": 0.008, "max_vol": 0.18,
        "buy_thresh": 3, "sell_thresh": 2,
        "stop_mult": 1.5, "min_stop_pct": 0.01,
    },
    "stock": {
        "ma_short": 10, "ma_long": 50,
        "min_vol": 0.001, "max_vol": 0.08,
        "buy_thresh": 3, "sell_thresh": 2,
        "stop_mult": 1.3, "min_stop_pct": 0.004,
    },
    "futures": {
        "ma_short": 9, "ma_long": 21,
        "min_vol": 0.001, "max_vol": 0.06,
        "buy_thresh": 3, "sell_thresh": 2,
        "stop_mult": 1.4, "min_stop_pct": 0.003,
    },
}


class TechnicalAgent:
    def __init__(self, market_type: str = "stable") -> None:
        self.market_type = market_type
        self.profile = PROFILES.get(market_type, PROFILES["stable"])

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        c = df["close"]

        # RSI-14
        delta = c.diff()
        gain = delta.clip(lower=0).ewm(span=14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(span=14, adjust=False).mean()
        rs = gain / loss
        df["rsi"] = 100.0 - (100.0 / (1.0 + rs))

        # Moving averages
        df["ma_short"] = c.rolling(window=self.profile["ma_short"]).mean()
        df["ma_long"] = c.rolling(window=self.profile["ma_long"]).mean()
        df["ema_9"] = c.ewm(span=9, adjust=False).mean()
        df["ema_21"] = c.ewm(span=21, adjust=False).mean()

        # MACD (12, 26, 9)
        ema12 = c.ewm(span=12, adjust=False).mean()
        ema26 = c.ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # Stochastic %K / %D
        low14 = df["low"].rolling(14).min()
        high14 = df["high"].rolling(14).max()
        df["stoch_k"] = 100 * (c - low14) / (high14 - low14 + 1e-10)
        df["stoch_d"] = df["stoch_k"].rolling(3).mean()

        # ATR
        hl = df["high"] - df["low"]
        hc = (df["high"] - c.shift()).abs()
        lc = (df["low"] - c.shift()).abs()
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        df["atr"] = tr.rolling(14).mean()
        df["atr_pct"] = df["atr"] / c

        # Bollinger Bands
        bb_mid = c.rolling(20).mean()
        bb_std = c.rolling(20).std()
        df["bb_mid"] = bb_mid
        df["bb_upper"] = bb_mid + 2 * bb_std
        df["bb_lower"] = bb_mid - 2 * bb_std
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / (df["bb_mid"] + 1e-10)

        # Volume
        df["volume_ma"] = df["volume"].rolling(20).mean()
        df["volume_ratio"] = df["volume"] / (df["volume_ma"] + 1e-10)

        # OBV
        obv_sign = delta.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        df["obv"] = (obv_sign * df["volume"]).cumsum()
        df["obv_ma"] = df["obv"].rolling(20).mean()

        # VWAP
        typical = (df["high"] + df["low"] + c) / 3
        cum_tp_vol = (typical * df["volume"]).cumsum()
        cum_vol = df["volume"].cumsum()
        df["vwap"] = cum_tp_vol / (cum_vol + 1e-10)

        # Trend strength
        df["trend_strength"] = (
            (df["ma_short"] - df["ma_long"]).abs() / (df["ma_long"] + 1e-10) * 100
        )

        return df

    def generate_signal(
        self, df: pd.DataFrame, has_position: bool,
    ) -> Tuple[Optional[str], Optional[float], str]:
        if len(df) < 5:
            return None, None, "not enough candles"

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        p = self.profile

        required = ["rsi", "ma_short", "ma_long", "atr", "atr_pct", "close",
                     "macd", "macd_signal", "stoch_k", "bb_upper", "bb_lower", "volume_ma"]
        for f in required:
            if pd.isna(latest.get(f, float("nan"))):
                return None, None, f"waiting on {f}"

        atr_pct = float(latest["atr_pct"])
        if atr_pct < p["min_vol"]:
            return None, None, f"vol too low {atr_pct:.4f}"
        if atr_pct > p["max_vol"]:
            return None, None, f"vol too high {atr_pct:.4f}"

        close = float(latest["close"])
        atr = float(latest["atr"])
        rsi = float(latest["rsi"])
        stoch_k = float(latest["stoch_k"])
        vol_ratio = float(latest.get("volume_ratio", 1.0))
        obv_rising = latest.get("obv", 0) > latest.get("obv_ma", 0)

        bullish_ma = prev["ma_short"] <= prev["ma_long"] and latest["ma_short"] > latest["ma_long"]
        bearish_ma = prev["ma_short"] >= prev["ma_long"] and latest["ma_short"] < latest["ma_long"]
        macd_cross_up = prev["macd"] <= prev["macd_signal"] and latest["macd"] > latest["macd_signal"]
        macd_cross_dn = prev["macd"] >= prev["macd_signal"] and latest["macd"] < latest["macd_signal"]

        if not has_position:
            score, reasons = 0, []
            if rsi < 35: score += 2; reasons.append("rsi<35")
            elif rsi < 45: score += 1; reasons.append("rsi<45")
            if bullish_ma: score += 2; reasons.append("MA↑")
            elif latest["ma_short"] > latest["ma_long"]: score += 1; reasons.append("trend+")
            if macd_cross_up: score += 2; reasons.append("MACD↑")
            elif latest["macd"] > latest["macd_signal"]: score += 1; reasons.append("MACD+")
            if stoch_k < 20: score += 1; reasons.append("stoch↓")
            if close < float(latest["bb_lower"]): score += 2; reasons.append("<BB-")
            elif close < float(latest["ma_short"]): score += 1; reasons.append("<MA")
            if vol_ratio >= 1.0: score += 1; reasons.append("vol✓")
            if obv_rising: score += 1; reasons.append("OBV↑")

            if score >= p["buy_thresh"]:
                stop = max(atr * p["stop_mult"], close * p["min_stop_pct"])
                return "buy", stop, f"BUY {score}pts: {', '.join(reasons)}"
            return None, None, f"wait (buy {score})"

        score, reasons = 0, []
        if rsi > 70: score += 2; reasons.append("rsi>70")
        elif rsi > 60: score += 1; reasons.append("rsi>60")
        if bearish_ma: score += 2; reasons.append("MA↓")
        elif latest["ma_short"] < latest["ma_long"]: score += 1; reasons.append("trend-")
        if macd_cross_dn: score += 2; reasons.append("MACD↓")
        if stoch_k > 80: score += 1; reasons.append("stoch↑")
        if close > float(latest["bb_upper"]): score += 2; reasons.append(">BB+")

        if score >= p["sell_thresh"]:
            return "sell", None, f"SELL {score}pts: {', '.join(reasons)}"
        return None, None, f"hold (sell {score})"

    def indicator_summary(self, df: pd.DataFrame) -> dict:
        if df.empty or len(df) < 2:
            return {}
        l = df.iloc[-1]
        return {
            "rsi": round(float(l.get("rsi", 0)), 2),
            "macd": round(float(l.get("macd", 0)), 4),
            "stoch_k": round(float(l.get("stoch_k", 0)), 2),
            "atr_pct": round(float(l.get("atr_pct", 0)), 5),
            "bb_width": round(float(l.get("bb_width", 0)), 4),
            "volume_ratio": round(float(l.get("volume_ratio", 1)), 2),
            "trend_strength": round(float(l.get("trend_strength", 0)), 2),
            "vwap": round(float(l.get("vwap", 0)), 4),
        }
