"""
data_preprocessor.py – Data cleaning utilities inspired by FreqAI.
"""
import pandas as pd
import numpy as np
from scipy import stats

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace([np.inf, -np.inf], np.nan)
    return df.dropna()

def remove_outliers(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
    numeric = df.select_dtypes(include=[np.number])
    z_scores = np.abs(stats.zscore(numeric))
    mask = (z_scores < threshold).all(axis=1)
    return df[mask].reset_index(drop=True)
