"""
data_preprocessor.py — Cleaning utilities for ML feature frames.

`DataPreprocessor` is a class (the buggy unmerged version was
function-only, which is why `from .data_preprocessor import DataPreprocessor`
crashed). Outlier removal is implemented with pandas/numpy so we don't
depend on scipy.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


class DataPreprocessor:
    """
    Clean a feature frame in place-safe steps:
      1. replace ±inf with NaN
      2. drop rows where ALL feature columns are NaN
      3. forward-fill remaining NaNs (then drop any leading rows still NaN)
      4. remove rows whose numeric features are >= z_threshold std devs from mean

    Defaults are conservative — outlier removal is opt-in.
    """

    def __init__(
        self,
        z_threshold: Optional[float] = 4.0,
        fill_method: str = "ffill",
    ) -> None:
        self.z_threshold = z_threshold
        self.fill_method = fill_method

    # ── public api ─────────────────────────────────────────────────
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply the cleaning pipeline; never mutates the caller's frame."""
        out = df.replace([np.inf, -np.inf], np.nan)

        if self.fill_method == "ffill":
            out = out.ffill()
        elif self.fill_method == "bfill":
            out = out.bfill()
        # else: leave NaNs; caller may choose to dropna explicitly

        # Any row that is *entirely* NaN is useless for ML.
        out = out.dropna(how="all")

        if self.z_threshold is not None and self.z_threshold > 0:
            out = self.remove_outliers(out, threshold=self.z_threshold)

        return out

    @staticmethod
    def remove_outliers(df: pd.DataFrame, threshold: float = 4.0) -> pd.DataFrame:
        """
        Drop rows where any numeric column is >= `threshold` z-scores from
        its column mean. Uses ddof=0 (population std) to avoid SciPy.
        """
        numeric = df.select_dtypes(include=[np.number])
        if numeric.empty:
            return df.copy()

        means = numeric.mean(axis=0)
        stds = numeric.std(axis=0, ddof=0).replace(0.0, np.nan)
        z = ((numeric - means) / stds).abs()
        # If a column had std=0, its z is NaN — treat as 0 (constant col is fine).
        z = z.fillna(0.0)
        keep_mask = (z < threshold).all(axis=1)
        return df.loc[keep_mask].copy()
