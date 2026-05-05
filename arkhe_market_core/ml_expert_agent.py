"""
ml_expert_agent.py – ML Expert Agent using LightGBM.
"""
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from pathlib import Path
from typing import Dict
from arkhe_market_core.ml.feature_engineer import FeatureEngineer
from arkhe_market_core.ml.data_preprocessor import clean_data

class MLExpertAgent:
    def __init__(self):
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.model_path = Path("models/ml_expert_model.txt")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

    def train(self, df: pd.DataFrame):
        df = df.copy()
        df = self.feature_engineer.populate_features(df)
        df = clean_data(df)
        if len(df) < 30:
            return False

        feature_cols = self.feature_engineer.get_feature_columns(df)
        if not feature_cols:
            return False

        # Simple target: future return
        df["&-target"] = df["close"].shift(-6) / df["close"] - 1
        df = clean_data(df)

        X = df[feature_cols]
        y = df["&-target"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

        train_data = lgb.Dataset(X_train, label=y_train)
        params = {"objective": "regression", "metric": "rmse", "verbose": -1}
        self.model = lgb.train(params, train_data, num_boost_round=100)
        self.model.save_model(str(self.model_path))
        return True

    def predict(self, df: pd.DataFrame) -> Dict:
        if self.model is None and self.model_path.exists():
            self.model = lgb.Booster(model_file=str(self.model_path))

        if self.model is None:
            self.train(df)
            if self.model is None:
                return {"ml_signal": 0, "ml_confidence": 0.5, "ml_pred": 0.0}

        df = df.copy()
        df = self.feature_engineer.populate_features(df)
        feature_cols = self.feature_engineer.get_feature_columns(df)
        X = df[feature_cols].iloc[[-1]]

        pred = float(self.model.predict(X)[0])
        confidence = min(max(abs(pred) * 10, 0.3), 1.0)

        return {
            "ml_signal": 1 if pred > 0.001 else (-1 if pred < -0.001 else 0),
            "ml_confidence": round(confidence, 3),
            "ml_pred": round(pred, 5)
        }
