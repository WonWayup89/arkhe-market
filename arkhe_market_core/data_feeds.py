"""
data_feeds.py – Unified market-data gateway for Arkhe Market.

Provides live / near-live OHLCV for:
  • Crypto  – Coinbase Exchange public REST
  • Stocks  – Yahoo Finance (yfinance)
  • Futures – Yahoo Finance continuous-contract tickers

Every fetch returns a standard pd.DataFrame with columns:
    open, high, low, close, volume   (float64)
    index = pd.DatetimeIndex (UTC)
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

import pandas as pd

# ── Coinbase (crypto) ──────────────────────────────────────────────
import requests

# ── Yahoo Finance (stocks + futures) ───────────────────────────────
try:
    import yfinance as yf

    _HAS_YF = True
except ImportError:
    _HAS_YF = False


# ── Futures symbol mapping ─────────────────────────────────────────
FUTURES_YF_MAP: Dict[str, str] = {
    "ES": "ES=F",
    "NQ": "NQ=F",
    "RTY": "RTY=F",
    "YM": "YM=F",
    "CL": "CL=F",
    "NG": "NG=F",
    "GC": "GC=F",
    "SI": "SI=F",
    "ZN": "ZN=F",
    "ZB": "ZB=F",
    "6E": "6E=F",
    "6J": "6J=F",
    "HG": "HG=F",
    "PL": "PL=F",
    "ZC": "ZC=F",
    "ZW": "ZW=F",
    "ZS": "ZS=F",
    "LE": "LE=F",
}

# Timeframe to yfinance interval string
_TF_MAP = {
    60: "1m",
    300: "5m",
    900: "15m",
    3600: "1h",
    21600: "1h",
    86400: "1d",
}

_TF_PERIOD = {
    60: "1d",
    300: "5d",
    900: "5d",
    3600: "1mo",
    21600: "3mo",
    86400: "1y",
}


class DataFeed:
    """Unified data-feed router."""

    def __init__(self, cache_ttl: int = 15) -> None:
        self._cache: Dict[str, dict] = {}
        self._cache_ttl = cache_ttl  # seconds

    # ── public API ─────────────────────────────────────────────────
    def fetch_crypto(
        self,
        symbol: str,
        timeframe: int = 3600,
        limit: int = 200,
    ) -> pd.DataFrame:
        key = f"crypto:{symbol}:{timeframe}"
        cached = self._from_cache(key)
        if cached is not None:
            return cached.tail(limit)

        df = self._coinbase_candles(symbol, timeframe, limit)
        self._to_cache(key, df)
        return df

    def fetch_stock(
        self,
        symbol: str,
        timeframe: int = 3600,
        limit: int = 200,
    ) -> pd.DataFrame:
        key = f"stock:{symbol}:{timeframe}"
        cached = self._from_cache(key)
        if cached is not None:
            return cached.tail(limit)

        df = self._yfinance_candles(symbol, timeframe, limit)
        self._to_cache(key, df)
        return df

    def fetch_futures(
        self,
        symbol: str,
        timeframe: int = 3600,
        limit: int = 200,
    ) -> pd.DataFrame:
        yf_sym = FUTURES_YF_MAP.get(symbol, f"{symbol}=F")
        key = f"futures:{yf_sym}:{timeframe}"
        cached = self._from_cache(key)
        if cached is not None:
            return cached.tail(limit)

        df = self._yfinance_candles(yf_sym, timeframe, limit)
        self._to_cache(key, df)
        return df

    def live_price_crypto(self, symbol: str) -> float:
        """Return the latest trade price from Coinbase ticker."""
        try:
            url = f"https://api.exchange.coinbase.com/products/{symbol}/ticker"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return float(resp.json()["price"])
        except Exception:
            df = self.fetch_crypto(symbol, timeframe=60, limit=5)
            if df.empty:
                return 0.0
            return float(df.iloc[-1]["close"])

    def live_price_stock(self, symbol: str) -> float:
        if not _HAS_YF:
            return 0.0
        try:
            t = yf.Ticker(symbol)
            info = t.fast_info
            price = getattr(info, "last_price", None) or getattr(info, "previous_close", 0.0)
            return float(price)
        except Exception:
            return 0.0

    def live_price_futures(self, symbol: str) -> float:
        yf_sym = FUTURES_YF_MAP.get(symbol, f"{symbol}=F")
        return self.live_price_stock(yf_sym)

    # ── Coinbase ───────────────────────────────────────────────────
    def _coinbase_candles(
        self,
        symbol: str,
        timeframe: int,
        limit: int,
    ) -> pd.DataFrame:
        url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
        params = {"granularity": timeframe}
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(data, columns=["timestamp", "low", "high", "open", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
        df.sort_values("timestamp", inplace=True)
        df = df.tail(limit)
        df.set_index("timestamp", inplace=True)
        df = df[["open", "high", "low", "close", "volume"]].astype(float)
        return df

    # ── Yahoo Finance ──────────────────────────────────────────────
    def _yfinance_candles(
        self,
        symbol: str,
        timeframe: int,
        limit: int,
    ) -> pd.DataFrame:
        if not _HAS_YF:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        interval = _TF_MAP.get(timeframe, "1h")
        period = _TF_PERIOD.get(timeframe, "1mo")

        try:
            t = yf.Ticker(symbol)
            df = t.history(period=period, interval=interval)
        except Exception:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        if df.empty:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df.columns = [c.lower() for c in df.columns]
        keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        df = df[keep].astype(float)

        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")

        df = df.tail(limit)
        return df

    # ── cache helpers ──────────────────────────────────────────────
    def _from_cache(self, key: str) -> Optional[pd.DataFrame]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.time() - entry["ts"] > self._cache_ttl:
            return None
        return entry["df"].copy()

    def _to_cache(self, key: str, df: pd.DataFrame) -> None:
        self._cache[key] = {"df": df.copy(), "ts": time.time()}
