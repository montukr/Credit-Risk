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

from app.core.config import ARTIFACTS_DIR
from app.core.db import get_db

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

COLUMN_ALIAS_MAP = {
    "customer_id": "CustomerID",
    "customer id": "CustomerID",
    "credit_limit": "CreditLimit",
    "credit limit": "CreditLimit",
    "utilisation_%": "UtilisationPct",
    "utilisation %": "UtilisationPct",
    "avg_payment_ratio": "AvgPaymentRatio",
    "avg payment ratio": "AvgPaymentRatio",
    "min_due_paid_frequency": "MinDuePaidFrequency",
    "min due paid frequency": "MinDuePaidFrequency",
    "merchant_mix_index": "MerchantMixIndex",
    "merchant mix index": "MerchantMixIndex",
    "cash_withdrawal_%": "CashWithdrawalPct",
    "cash withdrawal %": "CashWithdrawalPct",
    "recent_spend_change_%": "RecentSpendChangePct",
    "recent spend change %": "RecentSpendChangePct",
    "dpd bucket next month": "DPDBucketNextMonth",
    "delinquency_flag_next_month (dpd_bucket)": "DPDBucketNextMonth",
}

def normalize_bank_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    norm_cols = [c.strip().lower() for c in df.columns]
    rename_map = {}
    for orig, norm in zip(df.columns, norm_cols):
        if norm in COLUMN_ALIAS_MAP:
            rename_map[orig] = COLUMN_ALIAS_MAP[norm]
    df.rename(columns=rename_map, inplace=True)

    required_any = [
        "CustomerID",
        "CreditLimit",
        "UtilisationPct",
        "AvgPaymentRatio",
        "MinDuePaidFrequency",
        "MerchantMixIndex",
        "CashWithdrawalPct",
        "RecentSpendChangePct",
        "DPDBucketNextMonth",
    ]
    intersection = [c for c in required_any if c in df.columns]
    if intersection:
        df = df.dropna(subset=intersection, how="all")
    return df

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
    base = ARTIFACTS_DIR if artifact_dir is None else artifact_dir
    base.mkdir(parents=True, exist_ok=True)
    logreg_path = base / "logreg_model.pkl"
    tree_path = base / "tree_model.pkl"
    nn_path = base / "nn_model.pt"
    scaler_path = base / "scaler.pkl"
    shap_path = base / "explainer_shap.pkl"
    baseline_path = base / "baseline_stats.json"
    return logreg_path, tree_path, nn_path, scaler_path, shap_path, baseline_path

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
