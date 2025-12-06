from pathlib import Path
import pandas as pd
from fastapi import HTTPException
from ..ml.ml_pipeline import train_models, FEATURE_COLUMNS, predict_probas
from ..models.model_version import register_model_version, get_active_model_version

def get_artifact_dir_for(username: str, version: int) -> Path:
    from ..core.config import ARTIFACTS_DIR
    return ARTIFACTS_DIR / username / f"v{version}"

def retrain_from_file(db, username: str, file_path: Path, version: int):
    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    missing = [c for c in FEATURE_COLUMNS + ["DPDBucketNextMonthBinary"] if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    artifact_dir = get_artifact_dir_for(username, version)
    log_auc, tree_auc, nn_auc = train_models(df, artifact_dir=artifact_dir)
    register_model_version(
        db,
        username=username,
        version=version,
        metrics={"logreg_auc": log_auc, "tree_auc": tree_auc, "nn_auc": nn_auc},
        is_active=True,
    )
    return {"logreg_auc": log_auc, "tree_auc": tree_auc, "nn_auc": nn_auc}

def score_customer(db, admin_username: str, customer) -> dict:
    mv = get_active_model_version(db, admin_username)
    if not mv:
        raise HTTPException(status_code=400, detail="No active model for this admin")

    version = mv["version"]
    artifact_dir = get_artifact_dir_for(admin_username, version)

    row = {col: float(customer.get(col, 0.0)) for col in FEATURE_COLUMNS}
    X = pd.DataFrame([row])
    p_log, p_tree, ensemble = predict_probas(artifact_dir, X)
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
