"""
multi_portfolio_agent.py – Multi-market portfolio orchestrator.

Creates and manages SupervisorAgent instances for crypto (stable/alt),
stocks, and futures.  Each symbol gets its own paper engine.
"""

import os
import glob
from typing import Dict, List, Optional

from arkhe_market_core.data_feeds import DataFeed
from arkhe_market_core.supervisor_agent import SupervisorAgent
from cooldown_store import CooldownStore


class MultiPortfolioAgent:
    def __init__(
        self,
        total_balance: float = 100.0,
        stable_allocation: float = 0.7,
        stable_symbols: List[str] = None,
        alt_symbols: List[str] = None,
        stock_symbols: List[str] = None,
        futures_symbols: List[str] = None,
        risk_pct_stable: float = 0.01,
        risk_pct_alt: float = 0.015,
        risk_pct_stock: float = 0.01,
        risk_pct_futures: float = 0.012,
        timeframe: int = 3600,
        history_limit: int = 200,
        daily_drawdown_limit: float = 0.04,
        test_mode: bool = True,
        cooldown_seconds: int = 900,
        stock_balance: float = 0.0,
        futures_balance: float = 0.0,
    ) -> None:
        self.total_balance = float(total_balance)
        self.stable_allocation = float(stable_allocation)
        self.alt_allocation = 1.0 - self.stable_allocation

        self.stable_symbols = stable_symbols or ["BTC-USD", "ETH-USD"]
        self.alt_symbols = alt_symbols or ["SOL-USD", "XRP-USD", "AVAX-USD", "SUI-USD"]
        self.stock_symbols = stock_symbols or []
        self.futures_symbols = futures_symbols or []

        self.risk_pct_stable = float(risk_pct_stable)
        self.risk_pct_alt = float(risk_pct_alt)
        self.risk_pct_stock = float(risk_pct_stock)
        self.risk_pct_futures = float(risk_pct_futures)
        self.timeframe = int(timeframe)
        self.history_limit = int(history_limit)
        self.daily_drawdown_limit = float(daily_drawdown_limit)
        self.test_mode = bool(test_mode)
        self.cooldown_seconds = int(cooldown_seconds)
        self.stock_balance = float(stock_balance)
        self.futures_balance = float(futures_balance)

        os.makedirs("states", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        self.feed = DataFeed(cache_ttl=15)
        self.shared_cooldowns = CooldownStore()
        self.agents: Dict[str, SupervisorAgent] = {}
        self._build_agents()

    def _safe(self, symbol: str) -> str:
        return symbol.replace("/", "_").replace("-", "_").replace(".", "_").replace("=", "_")

    def _build_agents(self) -> None:
        self.agents = {}

        stable_each = (self.total_balance * self.stable_allocation) / max(len(self.stable_symbols), 1)
        alt_each = (self.total_balance * self.alt_allocation) / max(len(self.alt_symbols), 1)
        stock_each = self.stock_balance / max(len(self.stock_symbols), 1) if self.stock_symbols else 0
        futures_each = self.futures_balance / max(len(self.futures_symbols), 1) if self.futures_symbols else 0

        for sym in self.stable_symbols:
            s = self._safe(sym)
            self.agents[sym] = SupervisorAgent(
                symbol=sym, market_type="stable", asset_class="crypto",
                timeframe=self.timeframe, history_limit=self.history_limit,
                risk_pct=self.risk_pct_stable, daily_drawdown_limit=self.daily_drawdown_limit,
                starting_balance=stable_each, test_mode=self.test_mode,
                state_path=f"states/{s}_stable.json", log_path=f"logs/{s}_stable.csv",
                cooldown_seconds=self.cooldown_seconds, data_feed=self.feed,
                cooldown_store=self.shared_cooldowns,
            )

        for sym in self.alt_symbols:
            s = self._safe(sym)
            self.agents[sym] = SupervisorAgent(
                symbol=sym, market_type="alt", asset_class="crypto",
                timeframe=self.timeframe, history_limit=self.history_limit,
                risk_pct=self.risk_pct_alt, daily_drawdown_limit=self.daily_drawdown_limit,
                starting_balance=alt_each, test_mode=self.test_mode,
                state_path=f"states/{s}_alt.json", log_path=f"logs/{s}_alt.csv",
                cooldown_seconds=self.cooldown_seconds, data_feed=self.feed,
                cooldown_store=self.shared_cooldowns,
            )

        for sym in self.stock_symbols:
            s = self._safe(sym)
            self.agents[sym] = SupervisorAgent(
                symbol=sym, market_type="stock", asset_class="stock",
                timeframe=self.timeframe, history_limit=self.history_limit,
                risk_pct=self.risk_pct_stock, daily_drawdown_limit=self.daily_drawdown_limit,
                starting_balance=stock_each, test_mode=self.test_mode,
                state_path=f"states/{s}_stock.json", log_path=f"logs/{s}_stock.csv",
                cooldown_seconds=self.cooldown_seconds, data_feed=self.feed,
                cooldown_store=self.shared_cooldowns,
            )

        for sym in self.futures_symbols:
            s = self._safe(sym)
            self.agents[sym] = SupervisorAgent(
                symbol=sym, market_type="futures", asset_class="futures",
                timeframe=self.timeframe, history_limit=self.history_limit,
                risk_pct=self.risk_pct_futures, daily_drawdown_limit=self.daily_drawdown_limit,
                starting_balance=futures_each, test_mode=self.test_mode,
                state_path=f"states/{s}_futures.json", log_path=f"logs/{s}_futures.csv",
                cooldown_seconds=self.cooldown_seconds, data_feed=self.feed,
                cooldown_store=self.shared_cooldowns,
            )

    # ── run ─────────────────────────────────────────────────────────
    def run_once_crypto(self) -> list:
        return [
            self.agents[s].run_once()
            for s in self.stable_symbols + self.alt_symbols
            if s in self.agents
        ]

    def run_once_stocks(self) -> list:
        return [
            self.agents[s].run_once()
            for s in self.stock_symbols
            if s in self.agents
        ]

    def run_once_futures(self) -> list:
        return [
            self.agents[s].run_once()
            for s in self.futures_symbols
            if s in self.agents
        ]

    def run_once(self) -> list:
        return self.run_once_crypto() + self.run_once_stocks() + self.run_once_futures()

    # ── expert panel for a single symbol ───────────────────────────
    def expert_panel(self, symbol: str) -> Optional[dict]:
        agent = self.agents.get(symbol)
        if not agent:
            return None
        try:
            df = agent.fetch_candles()
            if df.empty or len(df) < 10:
                return None
            return agent.run_experts(df)
        except Exception:
            return None

    # ── prices ─────────────────────────────────────────────────────
    def get_live_price(self, symbol: str) -> float:
        agent = self.agents.get(symbol)
        if not agent:
            return 0.0
        try:
            return agent.get_live_price()
        except Exception:
            snap = agent.execution.paper.snapshot()
            return float(snap.get("last_price", 0.0))

    # ── snapshots ──────────────────────────────────────────────────
    def symbol_snapshot(self, symbol: str) -> dict:
        agent = self.agents.get(symbol)
        if not agent:
            return {"cash": 0, "asset_qty": 0, "avg_entry": 0, "last_price": 0,
                    "realized_pnl": 0, "unrealized_pnl": 0, "equity": 0, "trades": [],
                    "trade_count": 0, "win_rate": 0, "total_fees": 0}
        return agent.execution.paper.snapshot()

    def sleeve_snapshot(self, symbols: List[str]) -> dict:
        snaps = {s: self.symbol_snapshot(s) for s in symbols}
        equity = sum(float(v["equity"]) for v in snaps.values())
        cash = sum(float(v["cash"]) for v in snaps.values())
        realized = sum(float(v["realized_pnl"]) for v in snaps.values())
        unrealized = sum(float(v["unrealized_pnl"]) for v in snaps.values())
        return {"symbols": snaps, "equity": equity, "cash": cash,
                "realized_pnl": realized, "unrealized_pnl": unrealized}

    def snapshot(self) -> dict:
        stable = self.sleeve_snapshot(self.stable_symbols)
        alt = self.sleeve_snapshot(self.alt_symbols)
        stocks = self.sleeve_snapshot(self.stock_symbols)
        futures = self.sleeve_snapshot(self.futures_symbols)
        total_eq = stable["equity"] + alt["equity"] + stocks["equity"] + futures["equity"]
        return {
            "stable": stable, "alt": alt, "stocks": stocks, "futures": futures,
            "total_equity": total_eq,
            "total_cash": stable["cash"] + alt["cash"] + stocks["cash"] + futures["cash"],
        }

    # ── manual trade ───────────────────────────────────────────────
    def manual_trade(self, symbol: str, side: str, qty: float, price: float, reason: str = "manual") -> dict:
        agent = self.agents[symbol]
        agent.execution.mark_price(price)
        snap = agent.execution.execute(symbol=symbol, side=side, quantity=qty, price=price, reason=reason)
        agent.risk.update_balance_position(snap)
        return snap

    # ── reset ──────────────────────────────────────────────────────
    def reset_all_states(self) -> None:
        for p in glob.glob("states/*.json"):
            try: os.remove(p)
            except OSError: pass
        for p in glob.glob("logs/*.csv"):
            try: os.remove(p)
            except OSError: pass
        CooldownStore().clear()
        self.shared_cooldowns = CooldownStore()
        self._build_agents()
