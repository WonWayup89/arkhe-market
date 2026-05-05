"""
volatility_agent.py – Volatility regime expert.

Classifies the current market regime by volatility level and trend,
returning an advisory that the supervisor uses for gating and sizing.
"""

import pandas as pd
import numpy as np
from typing import Dict


class VolatilityAgent:
    """Expert: classifies vol-regime and produces an advisory dict."""

    def __init__(self, market_type: str = "stable") -> None:
        self.market_type = market_type

    def assess(self, df: pd.DataFrame) -> Dict:
        """Return regime classification and advisory flags."""
        if df.empty or len(df) < 30:
            return {"regime": "unknown", "ok_to_trade": True, "size_factor": 1.0,
                    "detail": "not enough data"}

        c = df["close"].astype(float)
        returns = c.pct_change().dropna()

        # Realised vol (annualised approx)
        recent_vol = returns.tail(14).std() * np.sqrt(252)
        long_vol = returns.std() * np.sqrt(252)

        # ATR-based if available
        atr_pct = float(df["atr_pct"].iloc[-1]) if "atr_pct" in df.columns and not pd.isna(df["atr_pct"].iloc[-1]) else None

        # Vol ratio  (recent / long-term)
        vol_ratio = recent_vol / (long_vol + 1e-10)

        # BB width squeeze detection
        bb_width = float(df["bb_width"].iloc[-1]) if "bb_width" in df.columns and not pd.isna(df["bb_width"].iloc[-1]) else None
        bb_squeeze = False
        if bb_width is not None and "bb_width" in df.columns:
            bb_pctile = (df["bb_width"].rank(pct=True).iloc[-1])
            bb_squeeze = bb_pctile < 0.15

        # Classify regime
        if vol_ratio > 1.8:
            regime = "high_vol"
            size_factor = 0.5
        elif vol_ratio > 1.3:
            regime = "elevated"
            size_factor = 0.75
        elif vol_ratio < 0.5:
            regime = "compressed"
            size_factor = 0.8  # breakout imminent, be cautious
        else:
            regime = "normal"
            size_factor = 1.0

        ok = True
        if regime == "high_vol" and self.market_type in ("stable", "stock"):
            ok = False  # block entries on stable assets in high-vol

        detail_parts = [
            f"regime={regime}",
            f"vol_ratio={vol_ratio:.2f}",
            f"recent_vol={recent_vol:.4f}",
        ]
        if bb_squeeze:
            detail_parts.append("BB-SQUEEZE")
        if atr_pct is not None:
            detail_parts.append(f"atr%={atr_pct:.4f}")

        return {
            "regime": regime,
            "ok_to_trade": ok,
            "size_factor": size_factor,
            "vol_ratio": round(vol_ratio, 3),
            "recent_vol": round(recent_vol, 5),
            "long_vol": round(long_vol, 5),
            "bb_squeeze": bb_squeeze,
            "detail": " | ".join(detail_parts),
        }
