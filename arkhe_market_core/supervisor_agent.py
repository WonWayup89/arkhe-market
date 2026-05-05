from arkhe_market_core.ml.inference.neural_decision import neural_entry_ok, neural_exit_ok
from arkhe_market_core.ml.inference.neural_stats import bump_entry_block, bump_exit_block
"""
supervisor_agent.py – Orchestrator that coordinates every expert per symbol.

Flow per run_once():
  1. Fetch candles via DataFeed
  2. TechnicalAgent → indicators + signal
  3. VolatilityAgent → regime + size_factor
  4. RegimeAgent → trend classification
  5. SentimentAgent → momentum score
  6. RiskAgent → position size + drawdown gate
  7. ExecutionAgent → paper fill + log
"""

import pandas as pd
from datetime import datetime, timezone
from typing import Tuple

from arkhe_market_core.data_feeds import DataFeed
from arkhe_market_core.technical_agent import TechnicalAgent
from arkhe_market_core.volatility_agent import VolatilityAgent
from arkhe_market_core.regime_agent import RegimeAgent
from arkhe_market_core.sentiment_agent import SentimentAgent
from arkhe_market_core.risk_agent import RiskAgent
from arkhe_market_core.execution_agent import ExecutionAgent
from cooldown_store import CooldownStore
from arkhe_market_core.fee_agent import decision_after_cost
from services.live_market_resolver import live_market_status
from arkhe_market_core.ml.ml_expert_agent import MLExpertAgent


class SupervisorAgent:
    def __init__(
        self,
        symbol: str,
        market_type: str,        # stable | alt | stock | futures
        asset_class: str = "crypto",   # crypto | stock | futures
        timeframe: int = 3600,
        history_limit: int = 200,
        risk_pct: float = 0.01,
        daily_drawdown_limit: float = 0.04,
        starting_balance: float = 100.0,
        test_mode: bool = True,
        state_path: str = "states/default.json",
        log_path: str = "logs/default.csv",
        cooldown_seconds: int = 900,
        slippage_bps: float = 5.0,
        data_feed: DataFeed = None,
        cooldown_store: CooldownStore = None,
        ml_expert: "MLExpertAgent | None" = None,
    ) -> None:
        self.symbol = symbol
        self.market_type = market_type
        self.asset_class = asset_class
        self.test_mode = bool(test_mode)
        self.timeframe = int(timeframe)
        self.history_limit = int(history_limit)
        self.cooldown_seconds = int(cooldown_seconds)

        self.feed = data_feed or DataFeed()
        self.technical = TechnicalAgent(market_type=market_type)
        self.volatility = VolatilityAgent(market_type=market_type)
        self.regime = RegimeAgent()
        self.sentiment = SentimentAgent()
        self.risk = RiskAgent(
            risk_pct=risk_pct,
            daily_drawdown_limit=daily_drawdown_limit,
            market_type=market_type,
            starting_balance=starting_balance,
            test_mode=test_mode,
        )
        self.execution = ExecutionAgent(
            state_path=state_path,
            log_path=log_path,
            starting_cash=starting_balance,
            slippage_bps=slippage_bps,
        )
        self.cooldowns = cooldown_store or CooldownStore()
        # Optional consultative ML advisor. Never gates trades on its own —
        # its output is added to run_experts() for logging and (eventually)
        # combined scoring. Pass `ml_expert=MLExpertAgent()` to enable.
        self.ml_expert = ml_expert

    # ── data ───────────────────────────────────────────────────────
    def fetch_candles(self) -> pd.DataFrame:
        if self.asset_class == "crypto":
            return self.feed.fetch_crypto(self.symbol, self.timeframe, self.history_limit)
        elif self.asset_class in ("stock", "stocks"):
            return self.feed.fetch_stock(self.symbol, self.timeframe, self.history_limit)
        elif self.asset_class == "futures":
            return self.feed.fetch_futures(self.symbol, self.timeframe, self.history_limit)
        return pd.DataFrame()

    def get_live_price(self) -> float:
        if self.asset_class == "crypto":
            return self.feed.live_price_crypto(self.symbol)
        elif self.asset_class in ("stock", "stocks"):
            return self.feed.live_price_stock(self.symbol)
        elif self.asset_class == "futures":
            return self.feed.live_price_futures(self.symbol)
        return 0.0



    def _market_control_state(self):
        # Plain-Python market control read — no Streamlit dependency in the
        # engine path. The Streamlit sidebar mutates the same store via
        # services.market_controls.set_market_control(...).
        from services.market_controls import get_market_control
        return get_market_control(self.asset_class)

    def _live_status(self):
        try:
            snap = self.execution.paper.snapshot()
            balance = float(snap.get("equity", 0))
        except Exception:
            balance = 0.0

        ctl = self._market_control_state()
        connected = ctl["connected"] if not self.test_mode else False

        return live_market_status(
            self.asset_class,
            connected,
            balance,
            override_minimum=ctl["override_minimum"],
            market_enabled=ctl["enabled"],
            market_paused=ctl["paused"],
        )

    # ── cooldown ───────────────────────────────────────────────────
    def _cooldown_active(self):
        last = self.cooldowns.get_last_trade_time(self.symbol)
        if last is None:
            return False, 0
        now = datetime.now(timezone.utc)
        elapsed = (now - last).total_seconds()
        remaining = max(self.cooldown_seconds - elapsed, 0)
        return (True, int(remaining)) if remaining > 0 else (False, 0)

    # ── expert panel ───────────────────────────────────────────────
    def run_experts(self, df: pd.DataFrame) -> dict:
        """Run all expert agents and return their assessments."""
        df = self.technical.calculate_indicators(df)
        latest_price = float(df.iloc[-1]["close"])
        self.execution.mark_price(latest_price)

        snap = self.execution.paper.snapshot()
        self.risk.update_balance_position(snap)
        has_pos = self.risk.position > 0

        signal, stop_dist, reason = self.technical.generate_signal(df, has_pos)
        vol_info = self.volatility.assess(df)
        regime_info = self.regime.assess(df)
        sent_info = self.sentiment.assess(df)
        indicators = self.technical.indicator_summary(df)

        # Consultative ML advisor — purely informational here, does not
        # change `signal`. Wire into the trade path only after backtesting.
        ml_info = None
        if self.ml_expert is not None:
            try:
                ml_info = self.ml_expert.analyze(df)
            except Exception as e:  # noqa: BLE001
                ml_info = {"signal": None, "confidence": 0.0, "prediction": 0.0,
                           "reason": f"ml_error:{type(e).__name__}", "mode": "error"}

        return {
            "price": latest_price,
            "signal": signal,
            "stop_distance": stop_dist,
            "reason": reason,
            "has_position": has_pos,
            "vol": vol_info,
            "regime": regime_info,
            "sentiment": sent_info,
            "ml": ml_info,
            "indicators": indicators,
            "risk": self.risk.risk_summary(),
        }

    # ── pre-trade mark to market ───────────────────────────────────
    def _pretrade_mark_to_market(self) -> None:
        """
        Pull a live (or last-known) price and mark the paper engine before
        the drawdown gate runs. The audit found that the gate previously
        used stale equity from the prior loop, allowing one extra cycle
        of trades to fire after a fast loss had already breached the
        daily limit.

        Best-effort: any failure here is logged and ignored — the gate
        will still run on whatever equity it has.
        """
        try:
            price = float(self.get_live_price())
        except Exception:
            return
        if price <= 0:
            return
        try:
            self.execution.mark_price(price)
            snap = self.execution.paper.snapshot()
            self.risk.update_balance_position(snap)
        except Exception:
            return

    # ── main cycle ─────────────────────────────────────────────────
    def run_once(self) -> str:
        self.risk.reset_daily_balance()

        status = self._live_status()

        if status.get("reason") == "disabled":
            return f"{self.symbol}: ⛔ market disabled"

        if status.get("reason") == "paused":
            return f"{self.symbol}: ⏸ market paused"

        if not self.test_mode and not status.get("live_eligible", False):
            return f"{self.symbol}: 🔒 live_block {status.get('reason','unknown')} balance={round(status.get('balance',0),2)} min={round(status.get('minimum_live_balance',0),2)}"

        # Mark to market before the drawdown gate so it sees current
        # equity, not yesterday's. Critical for fast-moving sessions.
        self._pretrade_mark_to_market()

        if self.risk.exceeded_drawdown():
            return f"{self.symbol}: ⛔ drawdown limit"

        if not self.risk.is_trading_time():
            return f"{self.symbol}: ⏸ outside trading hours"

        cd_active, cd_remain = self._cooldown_active()
        if cd_active:
            return f"{self.symbol}: ⏳ cooldown ({cd_remain}s)"

        try:
            df = self.fetch_candles()
        except Exception as e:
            return f"{self.symbol}: ❌ data error – {e}"

        if df.empty or len(df) < 10:
            return f"{self.symbol}: ⚠ insufficient data ({len(df)} bars)"

        panel = self.run_experts(df)
        signal = panel["signal"]
        stop_dist = panel["stop_distance"]
        reason = panel["reason"]
        vol = panel["vol"]
        regime = panel["regime"]
        sent = panel["sentiment"]
        price = panel["price"]

        try:
            neural = neural_entry_ok(self.symbol, price, self.asset_class, volatility=0.1)
        except Exception:
            neural = {"score": None, "gate": "unknown", "allow": True}

        # ── Supervisor conflict resolution ─────────────────────────
        if signal == "buy":
            if not neural.get("allow", True):
                bump_entry_block()
                return f"{self.symbol}:🧠 entry_gate:{neural.get('gate','unknown')} score={round(float(neural.get('score', 0) or 0), 4)}"
            # Block if vol agent says no
            if not vol.get("ok_to_trade", True):
                return f"{self.symbol}: 🚫 vol-blocked ({vol['detail']})"

            # Reduce score requirement if regime is trending-down
            if regime.get("regime") == "trending_down" and regime.get("confidence", 0) > 0.6:
                return f"{self.symbol}: 🚫 regime-blocked ({regime['detail']})"

            size_factor = vol.get("size_factor", 1.0)
            # Sentiment adjustment
            if sent.get("score", 0) < -40:
                size_factor *= 0.5

            qty = self.risk.calculate_position_size(price, stop_dist, size_factor)
            max_afford = round(self.risk.cash / price, 8) if price > 0 else 0
            qty = min(qty, max_afford)

            if qty > 0:
                edge_pct = max(float(stop_dist or 0) / max(price, 1e-9) * 100.0, 0.0)
                cost_check = decision_after_cost(
                    self.symbol, "buy", price, qty, edge_pct,
                    mode="test" if self.test_mode else "live"
                )
                if not cost_check.get("allow", True):
                    return f"{self.symbol}: 💸 fee_block buy net_edge={round(cost_check['net_edge_pct'],4)} cost={round(cost_check['cost_pct_of_notional'],4)} buffer={round(cost_check['minimum_edge_buffer_pct'],4)}"

                snap = self.execution.execute(
                    symbol=self.symbol, side="buy", quantity=qty, price=price,
                    stop_loss=stop_dist, reason=reason,
                    regime=regime.get("regime", ""), sentiment=sent.get("label", ""),
                )
                self.risk.update_balance_position(snap)
                self.cooldowns.set_last_trade_time(self.symbol, datetime.now(timezone.utc))
                return f"{self.symbol}: ✅ BUY {qty:.8f} @ {price:.4f} | {reason}"
            return f"{self.symbol}: ⚠ qty=0"

        if signal == "sell" and self.risk.position > 0:
            try:
                neural_exit = neural_exit_ok(self.symbol, price, self.asset_class, volatility=0.1)
            except Exception:
                neural_exit = {"score": None, "gate": "unknown", "allow": True}
            if not neural_exit.get("allow", True):
                bump_exit_block()
                return f"{self.symbol}:🧠 exit_gate:{neural_exit.get('gate','unknown')} score={round(float(neural_exit.get('score', 0) or 0), 4)}"
            qty = self.risk.position
            edge_pct = max(abs(float(stop_dist or 0)) / max(price, 1e-9) * 100.0, 0.25)
            cost_check = decision_after_cost(
                self.symbol, "sell", price, qty, edge_pct,
                mode="test" if self.test_mode else "live"
            )
            if not cost_check.get("allow", True):
                return f"{self.symbol}: 💸 fee_block sell net_edge={round(cost_check['net_edge_pct'],4)} cost={round(cost_check['cost_pct_of_notional'],4)} buffer={round(cost_check['minimum_edge_buffer_pct'],4)}"

            snap = self.execution.execute(
                symbol=self.symbol, side="sell", quantity=qty, price=price,
                reason=reason,
                regime=regime.get("regime", ""), sentiment=sent.get("label", ""),
            )
            self.risk.update_balance_position(snap)
            self.cooldowns.set_last_trade_time(self.symbol, datetime.now(timezone.utc))
            return f"{self.symbol}: ✅ SELL {qty:.8f} @ {price:.4f} | {reason}"

        return f"{self.symbol}: 👀 {reason}"
