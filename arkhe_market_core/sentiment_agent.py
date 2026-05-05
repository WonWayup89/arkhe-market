"""
sentiment_agent.py – Market-momentum and breadth expert.

Uses price-action derived signals as a proxy for sentiment:
momentum, rate-of-change, consecutive-bar direction, volume divergence.
"""

import pandas as pd
import numpy as np
from typing import Dict


class SentimentAgent:
    """Expert: momentum & breadth sentiment scoring."""

    def assess(self, df: pd.DataFrame) -> Dict:
        if df.empty or len(df) < 20:
            return {"score": 0, "label": "neutral", "detail": "insufficient data"}

        c = df["close"].astype(float)

        # Rate of Change (10-bar)
        roc_10 = (c.iloc[-1] / c.iloc[-11] - 1) * 100 if len(c) > 11 else 0.0

        # Consecutive up/down bars
        direction = c.diff().tail(10)
        up_streak = 0
        for v in reversed(direction.values):
            if v > 0:
                up_streak += 1
            else:
                break
        dn_streak = 0
        for v in reversed(direction.values):
            if v < 0:
                dn_streak += 1
            else:
                break

        # Volume-price divergence (rising price + falling volume = bearish divergence)
        price_up = c.iloc[-1] > c.iloc[-6] if len(c) > 6 else False
        vol_down = False
        if "volume" in df.columns and len(df) > 6:
            vol_down = float(df["volume"].iloc[-1]) < float(df["volume"].iloc[-6])

        divergence = "bearish" if (price_up and vol_down) else (
            "bullish" if (not price_up and not vol_down) else "none"
        )

        # Composite score (-100 to +100)
        score = 0
        reasons = []

        if roc_10 > 5:
            score += 30; reasons.append(f"ROC10 {roc_10:.1f}%")
        elif roc_10 > 2:
            score += 15; reasons.append(f"ROC10 {roc_10:.1f}%")
        elif roc_10 < -5:
            score -= 30; reasons.append(f"ROC10 {roc_10:.1f}%")
        elif roc_10 < -2:
            score -= 15; reasons.append(f"ROC10 {roc_10:.1f}%")

        if up_streak >= 4:
            score += 20; reasons.append(f"{up_streak} up bars")
        elif dn_streak >= 4:
            score -= 20; reasons.append(f"{dn_streak} dn bars")

        if divergence == "bearish":
            score -= 15; reasons.append("vol divergence↓")
        elif divergence == "bullish":
            score += 15; reasons.append("vol divergence↑")

        # RSI momentum if present
        if "rsi" in df.columns:
            rsi = float(df["rsi"].iloc[-1])
            if rsi > 60:
                score += 10
            elif rsi < 40:
                score -= 10

        score = max(-100, min(100, score))
        label = "bullish" if score > 20 else ("bearish" if score < -20 else "neutral")

        return {
            "score": score,
            "label": label,
            "roc_10": round(roc_10, 2),
            "up_streak": up_streak,
            "dn_streak": dn_streak,
            "divergence": divergence,
            "detail": f"{label} ({score}) – {'; '.join(reasons) if reasons else 'mixed signals'}",
        }
