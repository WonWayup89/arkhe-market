"""
shadow_validator.py – Expert agent: sim vs. live alignment checker.

For each sim trade, the shadow validator asks:
  "If this trade had been sent to the live broker at the same time,
   how closely would the fill have matched?"

It computes an alignment_score (0–100) per symbol based on:
  • Price drift: how far did the market move between signal time and now
  • Spread cost: estimated bid-ask impact
  • Slippage realism: does the sim's slippage model match observed spreads
  • Fill probability: would the order have filled at all (volume check)

A shadow_validated symbol has alignment ≥ 70 consistently.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


ALIGNMENT_THRESHOLD = 70  # minimum to consider shadow-validated


class ShadowValidator:
    """Expert: pairs sim trades against live market conditions."""

    def __init__(self, state_path: str = "states/shadow_validation.json") -> None:
        self.state_path = state_path
        os.makedirs(os.path.dirname(self.state_path) or ".", exist_ok=True)
        self.state = self._load()

    def _load(self) -> Dict:
        if not os.path.exists(self.state_path):
            return {}
        try:
            with open(self.state_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self) -> None:
        with open(self.state_path, "w") as f:
            json.dump(self.state, f, indent=2)

    # ── Validate a single trade ────────────────────────────────────
    def validate_trade(
        self,
        symbol: str,
        sim_price: float,
        live_price: float,
        sim_qty: float,
        side: str,
        volume_24h: float = 0.0,
        spread_bps: float = 5.0,
    ) -> Dict:
        """
        Compare a single sim trade against live conditions.
        Returns a per-trade alignment dict.
        """
        if sim_price <= 0 or live_price <= 0:
            return {"alignment": 0, "reason": "invalid prices", "valid": False}

        # Price drift (how different is sim fill from live market)
        drift_pct = abs(sim_price - live_price) / live_price * 100
        drift_score = max(100 - drift_pct * 20, 0)  # 5% drift = 0 score

        # Spread cost realism
        spread_cost = spread_bps / 100  # convert bps to %
        spread_score = 100 if drift_pct <= spread_cost else max(100 - (drift_pct - spread_cost) * 30, 0)

        # Volume check (can the market absorb this order)
        if volume_24h > 0:
            notional = sim_qty * live_price
            volume_ratio = notional / volume_24h
            fill_score = 100 if volume_ratio < 0.001 else max(100 - volume_ratio * 10000, 0)
        else:
            fill_score = 80  # assume ok if no volume data

        # Composite
        alignment = round(drift_score * 0.5 + spread_score * 0.3 + fill_score * 0.2, 1)

        return {
            "alignment": alignment,
            "drift_pct": round(drift_pct, 4),
            "drift_score": round(drift_score, 1),
            "spread_score": round(spread_score, 1),
            "fill_score": round(fill_score, 1),
            "sim_price": sim_price,
            "live_price": live_price,
            "side": side,
            "valid": alignment >= ALIGNMENT_THRESHOLD,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── Validate a symbol's recent trades ──────────────────────────
    def validate_symbol(
        self,
        symbol: str,
        trades: List[Dict],
        live_price: float,
        volume_24h: float = 0.0,
        window: int = 10,
    ) -> Dict:
        """
        Validate the last `window` trades for a symbol.
        Returns aggregate alignment score and per-trade details.
        """
        recent = trades[-window:] if len(trades) > window else trades

        if not recent:
            result = {
                "symbol": symbol,
                "alignment": 0,
                "status": "no_trades",
                "validated_count": 0,
                "passing_count": 0,
                "trades": [],
                "validated_at": datetime.now(timezone.utc).isoformat(),
            }
            self.state[symbol] = result
            self._save()
            return result

        validations = []
        for trade in recent:
            sim_price = float(trade.get("price", 0))
            sim_qty = float(trade.get("qty", 0))
            side = trade.get("side", "buy")

            v = self.validate_trade(
                symbol=symbol,
                sim_price=sim_price,
                live_price=live_price,
                sim_qty=sim_qty,
                side=side,
                volume_24h=volume_24h,
            )
            validations.append(v)

        avg_alignment = sum(v["alignment"] for v in validations) / len(validations)
        passing = sum(1 for v in validations if v["valid"])

        status = "shadow_validated" if avg_alignment >= ALIGNMENT_THRESHOLD else "shadow_failing"

        result = {
            "symbol": symbol,
            "alignment": round(avg_alignment, 1),
            "status": status,
            "validated_count": len(validations),
            "passing_count": passing,
            "pass_rate": round(passing / len(validations) * 100, 1),
            "trades": validations,
            "validated_at": datetime.now(timezone.utc).isoformat(),
        }

        self.state[symbol] = result
        self._save()
        return result

    # ── Queries ─────────────────────────────────────────────────────
    def is_shadow_validated(self, symbol: str) -> bool:
        entry = self.state.get(symbol, {})
        return entry.get("status") == "shadow_validated"

    def get_alignment(self, symbol: str) -> float:
        return self.state.get(symbol, {}).get("alignment", 0.0)

    def get_validation(self, symbol: str) -> Optional[Dict]:
        return self.state.get(symbol)

    def get_all_validations(self) -> Dict:
        return dict(self.state)

    def clear(self) -> None:
        self.state = {}
        self._save()
