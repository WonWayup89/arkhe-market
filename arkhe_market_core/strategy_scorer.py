"""
strategy_scorer.py – Expert agent: rolling strategy performance scorer.

Evaluates each symbol's paper-trading results over a configurable window
and produces a composite score that feeds the promotion engine.

Scores range 0–100:
  0–29   = failing (signal quality too low or negative edge)
  30–49  = developing (some edge but inconsistent)
  50–69  = competent (stable positive expectancy)
  70–89  = strong (consistent profits, controlled drawdown)
  90–100 = elite (exceptional risk-adjusted returns)
"""

import json
import os
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional

from arkhe_market_core.metrics import (
    compute_equity_curve,
    compute_max_drawdown,
    compute_simple_return,
    compute_sharpe_like,
    compute_sortino,
    compute_profit_factor,
)


# ── Score weights ──────────────────────────────────────────────────
WEIGHTS = {
    "return": 20,         # total return contribution
    "sharpe": 20,         # risk-adjusted return
    "sortino": 10,        # downside risk awareness
    "win_rate": 15,       # consistency
    "profit_factor": 15,  # gross profit vs gross loss
    "drawdown": 10,       # max drawdown penalty
    "trade_count": 10,    # minimum activity requirement
}

MIN_TRADES_FOR_SCORE = 5  # need at least this many trades to score


class StrategyScorer:
    """Expert: computes a 0–100 composite strategy score per symbol."""

    def __init__(self, history_path: str = "states/strategy_scores.json") -> None:
        self.history_path = history_path
        os.makedirs(os.path.dirname(self.history_path) or ".", exist_ok=True)
        self.history = self._load()

    def _load(self) -> Dict:
        if not os.path.exists(self.history_path):
            return {}
        try:
            with open(self.history_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self) -> None:
        with open(self.history_path, "w") as f:
            json.dump(self.history, f, indent=2)

    # ── Core scoring ───────────────────────────────────────────────
    def score_symbol(self, symbol: str, snapshot: dict, starting_equity: float) -> Dict:
        """Score a single symbol's strategy performance."""
        trades = snapshot.get("trades", [])
        equity = float(snapshot.get("equity", starting_equity))
        trade_count = int(snapshot.get("trade_count", len(trades)))
        win_count = int(snapshot.get("win_count", 0))
        loss_count = int(snapshot.get("loss_count", 0))

        # Not enough data
        if trade_count < MIN_TRADES_FOR_SCORE:
            return self._build_result(symbol, 0, "insufficient_data",
                                      f"need {MIN_TRADES_FOR_SCORE} trades, have {trade_count}",
                                      trade_count=trade_count)

        curve = compute_equity_curve(trades, equity, starting_equity)
        total_return = compute_simple_return(starting_equity, equity)
        max_dd = compute_max_drawdown(curve)
        sharpe = compute_sharpe_like(curve)
        sortino = compute_sortino(curve)
        pf = compute_profit_factor(trades)
        win_rate = win_count / max(win_count + loss_count, 1)

        # ── Component scores (each 0–1) ───────────────────────────
        s_return = self._sigmoid(total_return * 100, center=2, scale=5)
        s_sharpe = self._sigmoid(sharpe, center=0.5, scale=1.5)
        s_sortino = self._sigmoid(sortino, center=0.5, scale=1.5)
        s_win = min(win_rate / 0.6, 1.0)  # 60% win rate = full marks
        s_pf = self._sigmoid(pf, center=1.2, scale=2.0)
        s_dd = max(1.0 - max_dd * 5, 0.0)  # 20% DD = zero score
        s_trades = min(trade_count / 20, 1.0)  # 20 trades = full marks

        # ── Weighted composite ─────────────────────────────────────
        composite = (
            s_return * WEIGHTS["return"] +
            s_sharpe * WEIGHTS["sharpe"] +
            s_sortino * WEIGHTS["sortino"] +
            s_win * WEIGHTS["win_rate"] +
            s_pf * WEIGHTS["profit_factor"] +
            s_dd * WEIGHTS["drawdown"] +
            s_trades * WEIGHTS["trade_count"]
        )

        # Classify
        if composite >= 90:
            tier = "elite"
        elif composite >= 70:
            tier = "strong"
        elif composite >= 50:
            tier = "competent"
        elif composite >= 30:
            tier = "developing"
        else:
            tier = "failing"

        result = self._build_result(
            symbol, round(composite, 1), tier,
            f"ret={total_return*100:.1f}% sharpe={sharpe:.2f} wr={win_rate*100:.0f}% pf={pf:.2f} dd={max_dd*100:.1f}%",
            trade_count=trade_count,
            total_return=round(total_return, 4),
            sharpe=round(sharpe, 3),
            sortino=round(sortino, 3),
            win_rate=round(win_rate, 3),
            profit_factor=round(pf, 3),
            max_drawdown=round(max_dd, 4),
            components={
                "return": round(s_return, 3),
                "sharpe": round(s_sharpe, 3),
                "sortino": round(s_sortino, 3),
                "win_rate": round(s_win, 3),
                "profit_factor": round(s_pf, 3),
                "drawdown": round(s_dd, 3),
                "trade_count": round(s_trades, 3),
            },
        )

        # Persist
        self.history[symbol] = result
        self._save()

        return result

    # ── Batch scoring ──────────────────────────────────────────────
    def score_all(self, agent, symbols: List[str], starting_equities: Dict[str, float]) -> List[Dict]:
        """Score every symbol in the portfolio."""
        results = []
        for sym in symbols:
            snap = agent.symbol_snapshot(sym)
            start_eq = starting_equities.get(sym, 100.0)
            results.append(self.score_symbol(sym, snap, start_eq))
        return results

    # ── Helpers ─────────────────────────────────────────────────────
    @staticmethod
    def _sigmoid(x: float, center: float = 0, scale: float = 1) -> float:
        """Smooth 0–1 mapping centered at `center`."""
        try:
            return 1.0 / (1.0 + math.exp(-(x - center) / max(scale, 0.01)))
        except OverflowError:
            return 0.0 if x < center else 1.0

    @staticmethod
    def _build_result(symbol, score, tier, detail, **kwargs) -> Dict:
        return {
            "symbol": symbol,
            "score": score,
            "tier": tier,
            "detail": detail,
            "scored_at": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }

    def get_score(self, symbol: str) -> Optional[Dict]:
        return self.history.get(symbol)

    def get_all_scores(self) -> Dict:
        return dict(self.history)

    def clear(self) -> None:
        self.history = {}
        self._save()
