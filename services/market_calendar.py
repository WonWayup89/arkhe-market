"""
services/market_calendar.py — Exchange-aware trading-session checks.

Replaces the prior coarse UTC-hour buckets in RiskAgent.is_trading_time()
with venue-specific session windows expressed in the venue's local
timezone.

Implemented venues:

    NYSE / equities  — Mon–Fri 09:30–16:00 America/New_York. Honors
                       only the holidays registered via
                       `register_holidays`.
    CME futures      — Sun 18:00 → Fri 17:00 America/Chicago, with a
                       daily 17:00–18:00 maintenance halt (Mon–Thu).
                       Approximation of the CME Globex session; good
                       enough to keep the engine off the weekend.
    Crypto           — 24×7. Always returns True.

The audit explicitly called this out as too coarse for live use. The
holiday set is intentionally empty — wire one in via
`register_holidays(venue, [date(2026, 7, 4), ...])` from the UI or a
config file. Falling back to "open" when no calendar is registered is
safer than silently treating every day as a holiday.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, Iterable, Optional, Set

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover — Python < 3.9
    ZoneInfo = None  # type: ignore[assignment]


@dataclass(frozen=True)
class SessionWindow:
    """A single open period in local time, e.g. 09:30 → 16:00."""

    start: time
    end: time


# ── per-venue calendars ───────────────────────────────────────────────
NYSE_TZ = "America/New_York"
NYSE_REGULAR_SESSION = SessionWindow(start=time(9, 30), end=time(16, 0))

CME_TZ = "America/Chicago"
# CME Globex: Sun 17:00 to Fri 16:00 with a 17:00–18:00 daily halt
# (Mon–Thu). We model it as a per-weekday allowlist below.
CME_HALT = SessionWindow(start=time(17, 0), end=time(18, 0))

# Holidays registered at runtime: { "stocks": {date(...), ...} }
_HOLIDAYS: Dict[str, Set[date]] = {
    "stocks":  set(),
    "futures": set(),
}


def register_holidays(venue: str, days: Iterable[date]) -> None:
    """Add holidays for a venue. `venue` accepts 'stocks' or 'futures'."""
    bucket = _HOLIDAYS.setdefault(venue, set())
    for d in days:
        bucket.add(d)


def clear_holidays(venue: Optional[str] = None) -> None:
    """Test helper. Pass None to clear all venues."""
    if venue is None:
        for v in _HOLIDAYS:
            _HOLIDAYS[v] = set()
        return
    _HOLIDAYS[venue] = set()


def _now_in(tz: str) -> datetime:
    if ZoneInfo is None:
        # Fallback — treat naive UTC as local. Better than crashing.
        return datetime.now(timezone.utc)
    return datetime.now(ZoneInfo(tz))


def _is_holiday(venue: str, d: date) -> bool:
    return d in _HOLIDAYS.get(venue, set())


# ── public api ───────────────────────────────────────────────────────
def is_market_open(asset_class: str, *, now_utc: Optional[datetime] = None) -> bool:
    """
    Returns True if `asset_class` is open right now (or at `now_utc` if
    provided — useful for tests). Accepts the canonical asset class
    strings: 'crypto', 'stocks', 'futures'. Falls back to True for
    anything unknown so we don't silently halt unrelated markets.
    """
    ac = (asset_class or "").strip().lower()
    if ac in {"stock", "equity", "equities"}:
        ac = "stocks"
    if ac in {"future"}:
        ac = "futures"
    if ac in {"cryptos"}:
        ac = "crypto"

    if ac == "crypto":
        return True
    if ac == "stocks":
        return _is_stocks_open(now_utc=now_utc)
    if ac == "futures":
        return _is_futures_open(now_utc=now_utc)
    return True


# ── stocks (NYSE) ────────────────────────────────────────────────────
def _is_stocks_open(*, now_utc: Optional[datetime] = None) -> bool:
    if ZoneInfo is None:
        return _utc_hour_fallback_stocks(now_utc)
    local = _project(now_utc, NYSE_TZ)
    if local.weekday() >= 5:  # Sat/Sun
        return False
    if _is_holiday("stocks", local.date()):
        return False
    t = local.time()
    return NYSE_REGULAR_SESSION.start <= t < NYSE_REGULAR_SESSION.end


def _utc_hour_fallback_stocks(now_utc: Optional[datetime]) -> bool:
    """Used only when zoneinfo isn't available (Py<3.9)."""
    now = now_utc or datetime.now(timezone.utc)
    if now.weekday() >= 5:
        return False
    return 13 <= now.hour < 20  # ≈ 09:00 – 16:00 ET in standard time


# ── futures (CME) ────────────────────────────────────────────────────
def _is_futures_open(*, now_utc: Optional[datetime] = None) -> bool:
    """
    CME Globex approximation:
      Sunday  18:00 → 17:00 next day's halt
      Mon-Thu 18:00 → 17:00 next day's halt
      Friday  open until 17:00, then closed
      Saturday closed
    """
    if ZoneInfo is None:
        # Without zoneinfo, only block the obvious weekend.
        now = now_utc or datetime.now(timezone.utc)
        if now.weekday() == 5:  # Saturday UTC
            return False
        return True

    local = _project(now_utc, CME_TZ)
    weekday = local.weekday()  # Mon=0..Sun=6
    t = local.time()

    if _is_holiday("futures", local.date()):
        return False

    # Saturday: closed all day.
    if weekday == 5:
        return False

    # Sunday: open from 18:00 onward.
    if weekday == 6:
        return t >= time(18, 0)

    # Friday: open until 17:00. After 17:00 closed for weekend.
    if weekday == 4:
        return t < time(17, 0)

    # Mon-Thu: closed during 17:00-18:00 daily halt; otherwise open.
    return not (CME_HALT.start <= t < CME_HALT.end)


# ── helpers ──────────────────────────────────────────────────────────
def _project(now_utc: Optional[datetime], tz_name: str) -> datetime:
    if now_utc is None:
        return _now_in(tz_name)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    if ZoneInfo is None:  # pragma: no cover
        return now_utc
    return now_utc.astimezone(ZoneInfo(tz_name))
