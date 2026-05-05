import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
import joblib

DATA = Path("ml/data/training_dataset.csv")
MODEL_OUT = Path("ml/models/arkhe_market_model.pkl")

df = pd.read_csv(DATA).fillna(0)

feature_cols = [c for c in df.columns if c.startswith("feature_")]
if not feature_cols:
    print("No feature columns found")
    raise SystemExit(0)

X = df[feature_cols].copy()

for col in X.columns:
    X[col] = pd.to_numeric(X[col], errors="coerce")

X = X.fillna(0)

numeric_feature_cols = [c for c in X.columns if X[c].dtype.kind in "biufc"]
X = X[numeric_feature_cols]

if X.shape[1] == 0:
    print("No numeric feature columns found after cleanup")
    raise SystemExit(0)

y = (X.sum(axis=1) > X.mean(axis=1)).astype(float)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = MLPRegressor(
    hidden_layer_sizes=(32, 16),
    activation="relu",
    max_iter=500,
    random_state=42,
)

model.fit(X_scaled, y)

MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
joblib.dump((model, scaler, numeric_feature_cols), MODEL_OUT)

print("Model trained and saved to", MODEL_OUT)
print("Used feature columns:", numeric_feature_cols)
