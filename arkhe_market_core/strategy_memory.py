"""
strategy_memory.py – Persistent strategy analytics and decision log.

Stores a rolling history of scores, shadow validations, and promotion
decisions per symbol. Enables trend analysis: "is this strategy improving
or degrading over time?"
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import defaultdict


class StrategyMemory:
    """Expert: rolling memory of strategy performance over time."""

    def __init__(self, path: str = "states/strategy_memory.json", max_entries: int = 100) -> None:
        self.path = path
        self.max_entries = max_entries
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self) -> None:
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    # ── Record a snapshot ──────────────────────────────────────────
    def record(self, symbol: str, score: float, alignment: float,
               tier: str, trade_count: int, **extra) -> None:
        """Append a timestamped snapshot to the symbol's history."""
        if symbol not in self.data:
            self.data[symbol] = []

        entry = {
            "score": score,
            "alignment": alignment,
            "tier": tier,
            "trade_count": trade_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **extra,
        }

        self.data[symbol].append(entry)
        self.data[symbol] = self.data[symbol][-self.max_entries:]
        self._save()

    # ── Trend analysis ─────────────────────────────────────────────
    def get_trend(self, symbol: str, window: int = 10) -> Dict:
        """Analyze score trend over the last `window` entries."""
        entries = self.data.get(symbol, [])
        if len(entries) < 2:
            return {"trend": "insufficient_data", "entries": len(entries)}

        recent = entries[-window:]
        scores = [e["score"] for e in recent]
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]

        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0
        delta = avg_second - avg_first

        if delta > 5:
            trend = "improving"
        elif delta < -5:
            trend = "degrading"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "delta": round(delta, 2),
            "current_score": scores[-1] if scores else 0,
            "avg_recent": round(avg_second, 2),
            "avg_prior": round(avg_first, 2),
            "entries": len(entries),
            "window": len(recent),
        }

    def get_history(self, symbol: str) -> List[Dict]:
        return self.data.get(symbol, [])

    def get_latest(self, symbol: str) -> Optional[Dict]:
        entries = self.data.get(symbol, [])
        return entries[-1] if entries else None

    # ── Portfolio-level analytics ──────────────────────────────────
    def portfolio_summary(self) -> Dict:
        """Summary stats across all tracked symbols."""
        summary = {
            "total_symbols": len(self.data),
            "total_entries": sum(len(v) for v in self.data.values()),
            "by_tier": defaultdict(list),
            "avg_score": 0,
            "improving": [],
            "degrading": [],
            "stable": [],
        }

        scores = []
        for sym in self.data:
            latest = self.get_latest(sym)
            if latest:
                scores.append(latest["score"])
                summary["by_tier"][latest.get("tier", "sim_only")].append(sym)

            trend = self.get_trend(sym)
            if trend["trend"] == "improving":
                summary["improving"].append(sym)
            elif trend["trend"] == "degrading":
                summary["degrading"].append(sym)
            else:
                summary["stable"].append(sym)

        summary["avg_score"] = round(sum(scores) / len(scores), 1) if scores else 0
        summary["by_tier"] = dict(summary["by_tier"])
        return summary

    def clear(self) -> None:
        self.data = {}
        self._save()
