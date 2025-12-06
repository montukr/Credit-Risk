import json
from pathlib import Path
from typing import Tuple, Optional

import joblib
import numpy as np
import pandas as pd
import shap
import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ..core.config import ARTIFACTS_DIR
from ..core.db import get_db

RANDOM_STATE = 42

FEATURE_COLUMNS = [
    "CreditLimit",
    "UtilisationPct",
    "AvgPaymentRatio",
    "MinDuePaidFrequency",
    "MerchantMixIndex",
    "CashWithdrawalPct",
    "RecentSpendChangePct",
]

TARGET_COLUMN = "DPDBucketNextMonthBinary"

class MLP(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, x):
        return self.net(x)

def _get_artifact_paths(artifact_dir: Optional[Path] = None):
    base = artifact_dir or ARTIFACTS_DIR
    base.mkdir(parents=True, exist_ok=True)
    return (
        base / "logreg_model.pkl",
        base / "tree_model.pkl",
        base / "nn_model.pt",
        base / "scaler.pkl",
        base / "explainer_shap.pkl",
        base / "baseline_stats.json",
    )

def train_models(df: pd.DataFrame, artifact_dir: Optional[Path] = None) -> Tuple[float, float, float]:
    X = df[FEATURE_COLUMNS].values
    y = df[TARGET_COLUMN].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_STATE, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logreg = LogisticRegression(
        random_state=RANDOM_STATE, max_iter=1000, class_weight="balanced"
    )
    logreg.fit(X_train_scaled, y_train)
    logreg_auc = roc_auc_score(y_test, logreg.predict_proba(X_test_scaled)[:, 1])

    tree = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=5,
        random_state=RANDOM_STATE,
        class_weight="balanced",
    )
    tree.fit(X_train_scaled, y_train)
    tree_auc = roc_auc_score(y_test, tree.predict_proba(X_test_scaled)[:, 1])

    input_dim = X_train_scaled.shape[1]
    nn_model = MLP(input_dim)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(nn_model.parameters(), lr=1e-3)

    X_train_t = torch.tensor(X_train_scaled, dtype=torch.float32)
    y_train_t = torch.tensor(y_train.reshape(-1, 1), dtype=torch.float32)
    X_test_t = torch.tensor(X_test_scaled, dtype=torch.float32)
    y_test_t = torch.tensor(y_test.reshape(-1, 1), dtype=torch.float32)

    nn_model.train()
    for _ in range(80):
        optimizer.zero_grad()
        outputs = nn_model(X_train_t)
        loss = criterion(outputs, y_train_t)
        loss.backward()
        optimizer.step()

    nn_model.eval()
    with torch.no_grad():
        logits = nn_model(X_test_t).numpy().ravel()
        probs = 1 / (1 + np.exp(-logits))
        nn_auc = roc_auc_score(y_test, probs)

    logreg_path, tree_path, nn_path, scaler_path, shap_path, baseline_path = _get_artifact_paths(
        artifact_dir
    )

    joblib.dump(logreg, logreg_path)
    joblib.dump(tree, tree_path)
    joblib.dump(scaler, scaler_path)
    torch.save(nn_model.state_dict(), nn_path)

    explainer = shap.TreeExplainer(tree)
    joblib.dump(explainer, shap_path)

    baseline_stats = {
        "feature_means": {col: float(df[col].mean()) for col in FEATURE_COLUMNS},
        "feature_stds": {col: float(df[col].std()) for col in FEATURE_COLUMNS},
        "target_rate": float(df[TARGET_COLUMN].mean()),
    }
    with open(baseline_path, "w") as f:
        json.dump(baseline_stats, f, indent=2)

    db = get_db()
    db["model_metadata"].delete_many({})
    db["model_metadata"].insert_one(
        {
            "logreg_auc": logreg_auc,
            "tree_auc": tree_auc,
            "nn_auc": nn_auc,
            "baseline_stats": baseline_stats,
        }
    )

    return logreg_auc, tree_auc, nn_auc

def predict_probas(artifact_dir: Path, X: pd.DataFrame):
    logreg_path, tree_path, nn_path, scaler_path, shap_path, baseline_path = _get_artifact_paths(
        artifact_dir
    )
    scaler = joblib.load(scaler_path)
    logreg = joblib.load(logreg_path)
    tree = joblib.load(tree_path)

    X_arr = X[FEATURE_COLUMNS].values
    X_scaled = scaler.transform(X_arr)

    p_logreg = logreg.predict_proba(X_scaled)[:, 1]
    p_tree = tree.predict_proba(X_scaled)[:, 1]
    ensemble = (p_logreg + p_tree) / 2.0
    return p_logreg, p_tree, ensemble
