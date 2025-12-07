from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.ml.ml_pipeline import (
    train_models,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    normalize_bank_dataframe,
)
from app.ml.model_loader import predict_probas_for, compute_ensemble
from app.ml.model_registry import register_model_version, get_active_model_version
from app.core.config import ARTIFACTS_DIR


def get_artifact_dir_for(username: str, version: int) -> Path:
    return ARTIFACTS_DIR / username / f"v{version}"


def _load_training_dataframe(file_path: Path) -> pd.DataFrame:
    """
    Load a training dataframe from CSV, XLSX, or JSON (records),
    then normalize column names and derive the binary target if needed.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(file_path)
    elif suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    elif suffix == ".json":
        df = pd.read_json(file_path, orient="records")
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type; use CSV, XLSX, or JSON",
        )

    # normalize headers like "Credit Limit" -> "CreditLimit"
    df = normalize_bank_dataframe(df)

    # if we only have DPD bucket, derive binary target
    if "DPDBucketNextMonthBinary" not in df.columns and "DPDBucketNextMonth" in df.columns:
        df["DPDBucketNextMonthBinary"] = (df["DPDBucketNextMonth"] > 0).astype(int)

    return df


def retrain_from_file(username: str, file_path: Path, version: int) -> dict:
    df = _load_training_dataframe(file_path)

    # validate feature + target columns
    missing = [c for c in FEATURE_COLUMNS + [TARGET_COLUMN] if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    artifact_dir = get_artifact_dir_for(username, version)
    log_auc, tree_auc, nn_auc = train_models(df, artifact_dir=artifact_dir)

    register_model_version(
        username=username,
        version=version,
        metrics={"logreg_auc": log_auc, "tree_auc": tree_auc, "nn_auc": nn_auc},
        is_active=True,
    )

    return {
        "logreg_auc": log_auc,
        "tree_auc": tree_auc,
        "nn_auc": nn_auc,
        "version": version,
    }


def score_customer(admin_username: str, customer: dict) -> dict:
    """
    Build a feature row from the customer document, score it with the
    active model for this admin, and return probabilities + band + features.
    """
    mv = get_active_model_version(admin_username)
    if not mv:
        raise HTTPException(status_code=400, detail="No active model for this admin")

    version = mv["version"]

    row = {col: float(customer.get(col, 0.0)) for col in FEATURE_COLUMNS}
    X = np.array([[row[col] for col in FEATURE_COLUMNS]], dtype=float)

    p_log, p_tree, p_nn = predict_probas_for(admin_username, version, X)
    ensemble = compute_ensemble(p_log, p_tree, p_nn)
    prob = float(p_log[0])
    ens = float(ensemble[0])

    if ens > 0.7:
        band = "High"
    elif ens > 0.4:
        band = "Medium"
    else:
        band = "Low"

    return {
        "ml_probability": prob,
        "ensemble_probability": ens,
        "risk_band": band,
        "top_features": [{"feature": k, "value": v} for k, v in row.items()],
    }
