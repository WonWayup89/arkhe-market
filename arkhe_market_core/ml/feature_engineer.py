"""
feature_engineer.py — FreqAI-inspired feature expansion in pure pandas.

Avoids the pandas_ta dependency on purpose: the existing repo runs on
plain pandas/numpy, and adding a heavy TA library for five indicators
isn't a good trade. The features below are deliberately a small,
well-understood set; expand when a real model needs more.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd


# Feature columns are prefixed with "%-" so MLExpertAgent and any future
# trainer can find them with a simple startswith() filter.
FEATURE_PREFIX = "%-"

DEFAULT_PERIODS: List[int] = [8, 14, 21, 34, 55]


class FeatureEngineer:
    """
    Build a multi-period indicator panel from an OHLCV dataframe.

    Required input columns: at minimum `close`. `volume` is used if
    present. The dataframe is copied — input is not mutated.
    """

    def __init__(self, periods: Optional[List[int]] = None) -> None:
        self.periods = list(periods) if periods else list(DEFAULT_PERIODS)

    # ── indicators (pure pandas/numpy) ─────────────────────────────
    @staticmethod
    def _rsi(close: pd.Series, period: int) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)
        avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)

    @staticmethod
    def _sma(close: pd.Series, period: int) -> pd.Series:
        return close.rolling(window=period, min_periods=period).mean()

    @staticmethod
    def _ema(close: pd.Series, period: int) -> pd.Series:
        return close.ewm(span=period, adjust=False).mean()

    @staticmethod
    def _roc(close: pd.Series, period: int) -> pd.Series:
        prev = close.shift(period)
        return (close - prev) / prev.replace(0.0, np.nan) * 100.0

    # ── public api ─────────────────────────────────────────────────
    def populate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a copy of `df` with multi-period RSI/SMA/EMA/ROC and
        (when available) a volume ratio. Columns are prefixed `%-`.
        """
        if "close" not in df.columns:
            raise ValueError("FeatureEngineer requires a 'close' column.")

        out = df.copy()
        close = out["close"].astype(float)

        for period in self.periods:
            out[f"{FEATURE_PREFIX}rsi-{period}"] = self._rsi(close, period)
            out[f"{FEATURE_PREFIX}sma-{period}"] = self._sma(close, period)
            out[f"{FEATURE_PREFIX}ema-{period}"] = self._ema(close, period)
            out[f"{FEATURE_PREFIX}roc-{period}"] = self._roc(close, period)

            if "volume" in out.columns:
                vol = out["volume"].astype(float)
                vol_ma = vol.rolling(window=period, min_periods=period).mean()
                out[f"{FEATURE_PREFIX}vol_ratio-{period}"] = vol / vol_ma.replace(0.0, np.nan)

        out[f"{FEATURE_PREFIX}returns"] = close.pct_change()
        return out

    @staticmethod
    def feature_columns(df: pd.DataFrame) -> List[str]:
        """Return the list of `%-`-prefixed feature columns in `df`."""
        return [c for c in df.columns if c.startswith(FEATURE_PREFIX)]
