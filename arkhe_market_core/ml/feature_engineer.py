"""
feature_engineer.py – FreqAI-inspired automatic feature expansion.
"""
import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import List

class FeatureEngineer:
    def __init__(self):
        pass

    def populate_features(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        if periods is None:
            periods = [8, 14, 21, 34, 55]

        df = df.copy()

        for period in periods:
            df[f"%-rsi-{period}"] = ta.rsi(df["close"], length=period)
            df[f"%-sma-{period}"] = ta.sma(df["close"], length=period)
            df[f"%-ema-{period}"] = ta.ema(df["close"], length=period)
            df[f"%-roc-{period}"] = ta.roc(df["close"], length=period)

            if "volume" in df.columns:
                vol_ma = df["volume"].rolling(window=period).mean()
                df[f"%-vol_ratio-{period}"] = df["volume"] / (vol_ma + 1e-10)

        df["%-returns"] = df["close"].pct_change()
        return df

    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        return [col for col in df.columns if col.startswith("%-")]
