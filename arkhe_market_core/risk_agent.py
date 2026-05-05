"""
risk_agent.py – Risk-management expert.

Enforces position sizing, drawdown limits, market-hours filters,
and per-market risk rules.  Accepts a volatility size_factor from
the VolatilityAgent to scale positions dynamically.
"""

from datetime import datetime, timezone, date
from typing import Iterable, Tuple


# Market-hours presets (UTC)
MARKET_HOURS = {
    "crypto":  ((0, 23),),                # 24/7
    "stock":   ((13, 20),),               # ~NYSE 9:30-16:00 ET
    "futures": ((0, 23),),                # near 24 hrs Sun-Fri
}


class RiskAgent:
    def __init__(
        self,
        risk_pct: float = 0.01,
        daily_drawdown_limit: float = 0.04,
        market_type: str = "stable",
        trading_hours: Iterable[Tuple[int, int]] = None,
        starting_balance: float = 100.0,
        test_mode: bool = True,
        max_position_pct: float = 0.25,
    ) -> None:
        self.risk_pct = float(risk_pct)
        self.daily_drawdown_limit = float(daily_drawdown_limit)
        self.market_type = market_type
        self.max_position_pct = float(max_position_pct)

        if trading_hours:
            self.trading_hours = tuple(trading_hours)
        else:
            bucket = "crypto"
            if market_type in ("stock",):
                bucket = "stock"
            elif market_type in ("futures",):
                bucket = "futures"
            self.trading_hours = MARKET_HOURS[bucket]

        self.cash = float(starting_balance)
        self.position = 0.0
        self.equity = float(starting_balance)
        self._day_start: date = self._current_day()
        self._start_day_equity: float = float(starting_balance)
        self.test_mode = bool(test_mode)

    def _current_day(self) -> date:
        return datetime.now(timezone.utc).date()

    def reset_daily_balance(self) -> None:
        today = self._current_day()
        if today != self._day_start:
            self._day_start = today
            self._start_day_equity = self.equity

    def exceeded_drawdown(self) -> bool:
        loss = self._start_day_equity - self.equity
        return loss >= self._start_day_equity * self.daily_drawdown_limit

    def is_trading_time(self) -> bool:
        # Venue-aware session check. Audit-driven change: previously this
        # bucketed by UTC hour, treating futures as effectively 24/7 and
        # stocks as a rough UTC window — both wrong enough to allow
        # trades in closed sessions in live mode.
        #
        # Delegates to services.market_calendar.is_market_open, which
        # respects exchange timezones, weekends, the CME daily 17:00–18:00
        # halt, and holidays registered via market_calendar.register_holidays.
        if self.test_mode:
            return True

        from services.market_calendar import is_market_open

        # `market_type` values: 'stable' | 'alt' | 'stock' | 'futures'.
        # Map them onto canonical asset classes the calendar understands.
        if self.market_type in ("stable", "alt"):
            asset_class = "crypto"
        elif self.market_type == "stock":
            asset_class = "stocks"
        elif self.market_type == "futures":
            asset_class = "futures"
        else:
            asset_class = "crypto"

        return is_market_open(asset_class)

    def calculate_position_size(
        self, price: float, stop_distance: float, vol_size_factor: float = 1.0,
    ) -> float:
        if stop_distance <= 0 or price <= 0:
            return 0.0

        risk_amount = self.equity * self.risk_pct
        base_qty = risk_amount / stop_distance
        scaled_qty = base_qty * vol_size_factor

        # Cap at max_position_pct of equity
        max_val = self.equity * self.max_position_pct
        max_qty = max_val / price
        qty = min(scaled_qty, max_qty)

        return round(qty, 8)

    def update_balance_position(self, snapshot: dict) -> None:
        self.cash = float(snapshot["cash"])
        self.position = float(snapshot["asset_qty"])
        self.equity = float(snapshot["equity"])

    def risk_summary(self) -> dict:
        dd_used = (self._start_day_equity - self.equity) / (self._start_day_equity + 1e-10)
        return {
            "equity": round(self.equity, 2),
            "cash": round(self.cash, 2),
            "position": round(self.position, 8),
            "dd_used_pct": round(dd_used * 100, 2),
            "dd_limit_pct": round(self.daily_drawdown_limit * 100, 2),
            "risk_pct": round(self.risk_pct * 100, 3),
            "trading_ok": self.is_trading_time(),
            "dd_ok": not self.exceeded_drawdown(),
        }
