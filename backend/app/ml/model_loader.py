import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

import joblib
import numpy as np
import torch

from app.core.config import ARTIFACTS_DIR
from app.ml.ml_pipeline import MLP, FEATURE_COLUMNS
from app.core.db import get_db

logger = logging.getLogger("early_risk_app")

logreg_model = None
tree_model = None
nn_model = None
scaler = None
shap_explainer = None
baseline_stats: Dict = {}

def _paths_from_dir(artifact_dir: Optional[Path]):
    base = ARTIFACTS_DIR if artifact_dir is None else artifact_dir
    if artifact_dir is not None:
        base.mkdir(parents=True, exist_ok=True)
    logreg_path = base / "logreg_model.pkl"
    tree_path = base / "tree_model.pkl"
    nn_path = base / "nn_model.pt"
    scaler_path = base / "scaler.pkl"
    shap_path = base / "explainer_shap.pkl"
    baseline_path = base / "baseline_stats.json"
    return logreg_path, tree_path, nn_path, scaler_path, shap_path, baseline_path

def load_models(artifact_dir: Optional[Path] = None):
    global logreg_model, tree_model, nn_model, scaler, shap_explainer, baseline_stats

    logreg_path, tree_path, nn_path, scaler_path, shap_path, baseline_path = _paths_from_dir(
        artifact_dir
    )

    logger.info(f"Loading model artifacts from {logreg_path.parent} ...")

    if logreg_path.exists():
        logreg_model = joblib.load(logreg_path)
    else:
        logreg_model = None

    if tree_path.exists():
        tree_model = joblib.load(tree_path)
    else:
        tree_model = None

    if scaler_path.exists():
        scaler = joblib.load(scaler_path)
    else:
        scaler = None

    if shap_path.exists():
        shap_explainer = joblib.load(shap_path)
    else:
        shap_explainer = None

    if nn_path.exists():
        input_dim = len(FEATURE_COLUMNS)
        model = MLP(input_dim)
        state_dict = torch.load(nn_path, map_location=torch.device("cpu"))
        model.load_state_dict(state_dict)
        model.eval()
        nn_model = model.float()
    else:
        nn_model = None

    baseline_stats.clear()
    if baseline_path.exists():
        with open(baseline_path, "r") as f:
            baseline_stats.update(json.load(f))
    else:
        db = get_db()
        meta = db["model_metadata"].find_one()
        if meta and "baseline_stats" in meta:
            baseline_stats.update(meta["baseline_stats"])

    if logreg_model is None or tree_model is None or nn_model is None or scaler is None:
        raise RuntimeError("One or more models/scaler not loaded")

def predict_probas(features_array: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    global logreg_model, tree_model, nn_model, scaler
    if scaler is None or logreg_model is None or tree_model is None or nn_model is None:
        raise RuntimeError("Models not loaded; call load_models_for(...) first")

    X_scaled = scaler.transform(features_array)
    p_logreg = logreg_model.predict_proba(X_scaled)[:, 1]
    p_tree = tree_model.predict_proba(X_scaled)[:, 1]

    X_t = torch.tensor(X_scaled, dtype=torch.float32)
    with torch.no_grad():
        logits = nn_model(X_t).numpy().ravel()
        p_nn = 1 / (1 + np.exp(-logits))

    return p_logreg, p_tree, p_nn

def load_models_for(username: str, version: int):
    artifact_dir = ARTIFACTS_DIR / username / f"v{version}"
    load_models(artifact_dir=artifact_dir)

def predict_probas_for(username: str, version: int, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    load_models_for(username, version)
    return predict_probas(X)

def compute_ensemble(p_logreg: np.ndarray, p_tree: np.ndarray, p_nn: np.ndarray) -> np.ndarray:
    return (p_logreg + p_tree + p_nn) / 3.0
