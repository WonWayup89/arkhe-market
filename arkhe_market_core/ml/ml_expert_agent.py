import pandas as pd
import lightgbm as lgb
from pathlib import Path
from typing import Dict
from .feature_engineer import FeatureEngineer
from .data_preprocessor import DataPreprocessor

class MLExpertAgent:
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.preprocessor = DataPreprocessor()
        self.model = None

    def analyze(self, df: pd.DataFrame) -> Dict:
        if len(df) < 30:
            return {"signal": None, "confidence": 0.0, "prediction": 0.0, "reason": "insufficient_data"}

        df = self.feature_engineer.populate_features(df)
        df = self.preprocessor.clean_data(df)

        # Placeholder ML logic (expand later with real training)
        prediction = df['%-roc-14'].iloc[-1] * 100 if '%-roc-14' in df.columns else 0.0
        confidence = min(abs(prediction) / 10.0, 1.0)
        signal = 'buy' if prediction > 0.6 else 'sell' if prediction < -0.6 else None

        return {
            "signal": signal,
            "confidence": float(confidence),
            "prediction": float(prediction),
            "reason": "ml_expert"
        }