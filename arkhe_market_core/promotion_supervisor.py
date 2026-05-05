"""
promotion_supervisor.py – Orchestrator for the strategy scoring and promotion pipeline.

Runs the full cycle:
  1. StrategyScorer → compute score per symbol
  2. ShadowValidator → check sim vs live alignment per symbol
  3. PromotionEngine → evaluate tier transitions
  4. StrategyMemory → persist the snapshot for trend analysis

This is the single entry point for the promotion pipeline.
"""

from typing import Dict, List

from arkhe_market_core.strategy_scorer import StrategyScorer
from arkhe_market_core.shadow_validator import ShadowValidator
from arkhe_market_core.promotion_engine import PromotionEngine
from arkhe_market_core.strategy_memory import StrategyMemory


class PromotionSupervisor:
    """Orchestrates scoring → validation → promotion → memory."""

    def __init__(self) -> None:
        self.scorer = StrategyScorer()
        self.shadow = ShadowValidator()
        self.promoter = PromotionEngine()
        self.memory = StrategyMemory()

    def run_cycle(
        self,
        agent,
        symbols: List[str],
        starting_equities: Dict[str, float],
    ) -> List[Dict]:
        """
        Run the full promotion cycle for all symbols.

        Args:
            agent: MultiPortfolioAgent (has symbol_snapshot, get_live_price)
            symbols: list of symbol strings
            starting_equities: {symbol: starting_balance}

        Returns:
            List of promotion results per symbol.
        """
        results = []

        for sym in symbols:
            snap = agent.symbol_snapshot(sym)
            start_eq = starting_equities.get(sym, 100.0)

            # 1. Score
            score_data = self.scorer.score_symbol(sym, snap, start_eq)

            # 2. Shadow validate
            try:
                live_price = agent.get_live_price(sym)
            except Exception:
                live_price = float(snap.get("last_price", 0))

            shadow_data = self.shadow.validate_symbol(
                symbol=sym,
                trades=snap.get("trades", []),
                live_price=live_price,
            )

            # 3. Promote/demote
            promo_result = self.promoter.evaluate(sym, score_data, shadow_data)

            # 4. Remember
            self.memory.record(
                symbol=sym,
                score=score_data.get("score", 0),
                alignment=shadow_data.get("alignment", 0),
                tier=promo_result["new_tier"],
                trade_count=score_data.get("trade_count", 0),
                total_return=score_data.get("total_return", 0),
                sharpe=score_data.get("sharpe", 0),
            )

            results.append({
                "symbol": sym,
                "score": score_data,
                "shadow": shadow_data,
                "promotion": promo_result,
                "trend": self.memory.get_trend(sym),
            })

        return results

    # ── Quick summaries ────────────────────────────────────────────
    def tier_summary(self) -> Dict:
        return self.promoter.get_promotion_summary()

    def portfolio_health(self) -> Dict:
        return self.memory.portfolio_summary()

    def get_symbol_card(self, symbol: str) -> Dict:
        """Full status card for a single symbol."""
        return {
            "score": self.scorer.get_score(symbol),
            "shadow": self.shadow.get_validation(symbol),
            "tier": self.promoter.get_tier(symbol),
            "tier_state": self.promoter.get_symbol_state(symbol),
            "trend": self.memory.get_trend(symbol),
            "history": self.memory.get_history(symbol)[-5:],
        }

    def reset_all(self) -> None:
        self.scorer.clear()
        self.shadow.clear()
        self.promoter.clear()
        self.memory.clear()
