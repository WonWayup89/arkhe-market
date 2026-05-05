"""
promotion_engine.py – Expert agent: strategy promotion lifecycle manager.

Manages each symbol through three tiers:

  sim_only → shadow_validated → live_eligible

Promotion rules:
  • sim_only → shadow_validated:
      strategy_score ≥ 50 AND shadow_alignment ≥ 70
      AND at least 10 trades AND positive return

  • shadow_validated → live_eligible:
      strategy_score ≥ 70 AND shadow_alignment ≥ 80
      AND at least 20 trades AND sharpe ≥ 0.3
      AND max_drawdown < 15%

  • Demotion:
      Any tier can drop back to sim_only if score falls below 30
      or alignment drops below 50

The engine persists promotion state and emits a reason for each decision.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


TIERS = ["sim_only", "shadow_validated", "live_eligible"]

# ── Promotion thresholds ───────────────────────────────────────────
PROMOTE_TO_SHADOW = {
    "min_score": 50,
    "min_alignment": 70,
    "min_trades": 10,
    "min_return": 0.0,  # must be non-negative
}

PROMOTE_TO_LIVE = {
    "min_score": 70,
    "min_alignment": 80,
    "min_trades": 20,
    "min_sharpe": 0.3,
    "max_drawdown": 0.15,
}

DEMOTE_THRESHOLD = {
    "score_below": 30,
    "alignment_below": 50,
}


class PromotionEngine:
    """Expert: manages strategy tier promotion and demotion."""

    def __init__(self, state_path: str = "states/promotion_state.json") -> None:
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

    # ── Get/set tier ───────────────────────────────────────────────
    def get_tier(self, symbol: str) -> str:
        return self.state.get(symbol, {}).get("tier", "sim_only")

    def get_symbol_state(self, symbol: str) -> Dict:
        return self.state.get(symbol, {
            "tier": "sim_only",
            "history": [],
            "last_evaluated": None,
        })

    # ── Evaluate promotion/demotion ────────────────────────────────
    def evaluate(
        self,
        symbol: str,
        score_data: Dict,
        shadow_data: Dict,
    ) -> Dict:
        """
        Evaluate a symbol's promotion eligibility based on its
        strategy score and shadow validation data.

        Returns the new tier and reason.
        """
        current_tier = self.get_tier(symbol)
        score = score_data.get("score", 0)
        alignment = shadow_data.get("alignment", 0)
        trade_count = score_data.get("trade_count", 0)
        total_return = score_data.get("total_return", 0)
        sharpe = score_data.get("sharpe", 0)
        max_dd = score_data.get("max_drawdown", 1.0)

        new_tier = current_tier
        reason = "no change"
        action = "hold"

        # ── Check demotion first ───────────────────────────────────
        if score < DEMOTE_THRESHOLD["score_below"] and current_tier != "sim_only":
            new_tier = "sim_only"
            reason = f"demoted: score {score} < {DEMOTE_THRESHOLD['score_below']}"
            action = "demote"

        elif alignment < DEMOTE_THRESHOLD["alignment_below"] and current_tier == "live_eligible":
            new_tier = "shadow_validated"
            reason = f"demoted from live: alignment {alignment} < {DEMOTE_THRESHOLD['alignment_below']}"
            action = "demote"

        # ── Check promotion ────────────────────────────────────────
        elif current_tier == "sim_only":
            p = PROMOTE_TO_SHADOW
            if (score >= p["min_score"] and
                alignment >= p["min_alignment"] and
                trade_count >= p["min_trades"] and
                total_return >= p["min_return"]):
                new_tier = "shadow_validated"
                reason = (f"promoted: score={score}≥{p['min_score']}, "
                         f"align={alignment}≥{p['min_alignment']}, "
                         f"trades={trade_count}≥{p['min_trades']}")
                action = "promote"
            else:
                missing = []
                if score < p["min_score"]:
                    missing.append(f"score {score}<{p['min_score']}")
                if alignment < p["min_alignment"]:
                    missing.append(f"align {alignment}<{p['min_alignment']}")
                if trade_count < p["min_trades"]:
                    missing.append(f"trades {trade_count}<{p['min_trades']}")
                if total_return < p["min_return"]:
                    missing.append(f"return {total_return*100:.1f}%<0%")
                reason = f"sim_only: needs {', '.join(missing)}"

        elif current_tier == "shadow_validated":
            p = PROMOTE_TO_LIVE
            if (score >= p["min_score"] and
                alignment >= p["min_alignment"] and
                trade_count >= p["min_trades"] and
                sharpe >= p["min_sharpe"] and
                max_dd < p["max_drawdown"]):
                new_tier = "live_eligible"
                reason = (f"promoted to live: score={score}≥{p['min_score']}, "
                         f"sharpe={sharpe:.2f}≥{p['min_sharpe']}, "
                         f"dd={max_dd*100:.1f}%<{p['max_drawdown']*100:.0f}%")
                action = "promote"
            else:
                missing = []
                if score < p["min_score"]:
                    missing.append(f"score {score}<{p['min_score']}")
                if alignment < p["min_alignment"]:
                    missing.append(f"align {alignment}<{p['min_alignment']}")
                if trade_count < p["min_trades"]:
                    missing.append(f"trades {trade_count}<{p['min_trades']}")
                if sharpe < p["min_sharpe"]:
                    missing.append(f"sharpe {sharpe:.2f}<{p['min_sharpe']}")
                if max_dd >= p["max_drawdown"]:
                    missing.append(f"dd {max_dd*100:.1f}%≥{p['max_drawdown']*100:.0f}%")
                reason = f"shadow_validated: needs {', '.join(missing)}"

        elif current_tier == "live_eligible":
            reason = f"live_eligible: score={score}, align={alignment}, maintaining"

        # ── Record ─────────────────────────────────────────────────
        now = datetime.now(timezone.utc).isoformat()
        entry = self.state.get(symbol, {"tier": "sim_only", "history": []})
        history = entry.get("history", [])

        if new_tier != current_tier:
            history.append({
                "from": current_tier,
                "to": new_tier,
                "action": action,
                "reason": reason,
                "score": score,
                "alignment": alignment,
                "timestamp": now,
            })

        self.state[symbol] = {
            "tier": new_tier,
            "score": score,
            "alignment": alignment,
            "trade_count": trade_count,
            "reason": reason,
            "action": action,
            "last_evaluated": now,
            "history": history[-20:],  # keep last 20 transitions
        }
        self._save()

        return {
            "symbol": symbol,
            "previous_tier": current_tier,
            "new_tier": new_tier,
            "action": action,
            "reason": reason,
            "score": score,
            "alignment": alignment,
        }

    # ── Batch evaluate ─────────────────────────────────────────────
    def evaluate_all(
        self,
        symbols: List[str],
        scores: Dict[str, Dict],
        shadows: Dict[str, Dict],
    ) -> List[Dict]:
        """Evaluate every symbol and return promotion results."""
        results = []
        for sym in symbols:
            score_data = scores.get(sym, {"score": 0, "trade_count": 0})
            shadow_data = shadows.get(sym, {"alignment": 0})
            results.append(self.evaluate(sym, score_data, shadow_data))
        return results

    # ── Queries ─────────────────────────────────────────────────────
    def get_all_tiers(self) -> Dict[str, str]:
        return {sym: data.get("tier", "sim_only") for sym, data in self.state.items()}

    def symbols_at_tier(self, tier: str) -> List[str]:
        return [sym for sym, data in self.state.items() if data.get("tier") == tier]

    def get_promotion_summary(self) -> Dict:
        tiers = self.get_all_tiers()
        return {
            "sim_only": [s for s, t in tiers.items() if t == "sim_only"],
            "shadow_validated": [s for s, t in tiers.items() if t == "shadow_validated"],
            "live_eligible": [s for s, t in tiers.items() if t == "live_eligible"],
            "total": len(tiers),
        }

    def clear(self) -> None:
        self.state = {}
        self._save()
