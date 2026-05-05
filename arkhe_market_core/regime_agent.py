"""
regime_agent.py – Market-regime detection expert.

Classifies the market into: trending-up, trending-down, ranging, breakout.
Combines slope, ADX-like metric, and mean-reversion signals.
"""

import pandas as pd
import numpy as np
from typing import Dict


class RegimeAgent:
    """Expert: detects the prevailing market regime."""

    def __init__(self, lookback: int = 50) -> None:
        self.lookback = lookback

    def assess(self, df: pd.DataFrame) -> Dict:
        if df.empty or len(df) < self.lookback:
            return {"regime": "unknown", "confidence": 0.0, "bias": "neutral", "detail": "insufficient data"}

        c = df["close"].astype(float).tail(self.lookback)
        x = np.arange(len(c))

        # Linear-regression slope (normalised)
        slope = np.polyfit(x, c.values, 1)[0]
        slope_pct = slope / (c.mean() + 1e-10) * 100  # % per bar

        # Trend consistency: R²
        fit = np.polyval(np.polyfit(x, c.values, 1), x)
        ss_res = np.sum((c.values - fit) ** 2)
        ss_tot = np.sum((c.values - c.mean()) ** 2)
        r_sq = 1 - ss_res / (ss_tot + 1e-10)

        # Mean-reversion score: how often price crosses its MA
        ma = c.rolling(int(self.lookback * 0.4)).mean()
        crosses = ((c > ma).astype(int).diff().abs()).sum()
        cross_rate = crosses / len(c)

        # ADX-like: directional intensity
        if "ma_short" in df.columns and "ma_long" in df.columns:
            trend_str = float(df["trend_strength"].iloc[-1]) if "trend_strength" in df.columns else 0.0
        else:
            trend_str = abs(slope_pct) * 10

        # Classify
        if r_sq > 0.7 and abs(slope_pct) > 0.05:
            regime = "trending_up" if slope_pct > 0 else "trending_down"
            confidence = min(r_sq, 0.99)
        elif cross_rate > 0.15:
            regime = "ranging"
            confidence = cross_rate
        elif r_sq < 0.3 and abs(slope_pct) < 0.02:
            regime = "ranging"
            confidence = 0.5
        else:
            regime = "mixed"
            confidence = 0.4

        bias = "bullish" if slope_pct > 0.02 else ("bearish" if slope_pct < -0.02 else "neutral")

        return {
            "regime": regime,
            "confidence": round(confidence, 3),
            "bias": bias,
            "slope_pct": round(slope_pct, 4),
            "r_squared": round(r_sq, 4),
            "cross_rate": round(cross_rate, 4),
            "trend_strength": round(trend_str, 2),
            "detail": f"{regime} (R²={r_sq:.2f}, slope={slope_pct:.3f}%/bar, bias={bias})",
        }
