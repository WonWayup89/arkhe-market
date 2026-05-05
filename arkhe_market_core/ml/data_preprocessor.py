import pandas as pd
import numpy as np
from scipy import stats

class DataPreprocessor:
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        df = df.replace([np.inf, -np.inf], np.nan)
        return df.dropna()

    @staticmethod
    def remove_outliers(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        numeric = df.select_dtypes(include=np.number)
        z = np.abs(stats.zscore(numeric, nan_policy='omit'))
        return df[(z < threshold).all(axis=1)]

    @staticmethod
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        return (df - df.mean()) / (df.std() + 1e-8)