import pandas as pd
import numpy as np
import talib as ta
from typing import List, Dict

class FeatureEngineer:
    def populate_features(self, df: pd.DataFrame, periods: List[int] = [8, 14, 20, 50]) -> pd.DataFrame:
        df = df.copy()
        for p in periods:
            df[f'%-rsi-{p}'] = ta.RSI(df['close'], timeperiod=p)
            df[f'%-sma-{p}'] = ta.SMA(df['close'], timeperiod=p)
            df[f'%-ema-{p}'] = ta.EMA(df['close'], timeperiod=p)
            df[f'%-roc-{p}'] = ta.ROC(df['close'], timeperiod=p)
            if 'high' in df and 'low' in df and 'volume' in df:
                df[f'%-mfi-{p}'] = ta.MFI(df['high'], df['low'], df['close'], df['volume'], timeperiod=p)
        df['%-volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        return df