from pathlib import Path
import shutil
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.core.deps import get_current_admin
from app.ml.model_registry import list_model_versions, get_active_model_version
from app.ml.model_loader import predict_probas_for, compute_ensemble
from app.ml.rule_engine import evaluate_rules
from app.schemas.risk import CustomerFeatures, RiskSummary
from app.services.ml_service import retrain_from_file

router = APIRouter(prefix="/risk", tags=["risk"])


def _next_version_for(username: str) -> int:
    """
    Look at model_versions and return the next version number for this admin.
    """
    versions = list_model_versions(username)
    if not versions:
        return 1
    return int(versions[0]["version"]) + 1


@router.post("/retrain")
async def retrain_model(
    file: UploadFile = File(...),
    current_admin=Depends(get_current_admin),
):
    """
    Admin-only: upload labelled CSV/XLSX/JSON and retrain models.
    """
    tmp_path = Path(f"/tmp/{file.filename}")
    with tmp_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    version = _next_version_for(current_admin["username"])
    metrics = retrain_from_file(
        username=current_admin["username"],
        file_path=tmp_path,
        version=version,
    )
    return {"message": "Model retrained", **metrics}


@router.get("/models")
def get_models(current_admin=Depends(get_current_admin)):
    """
    List all model versions for this admin with AUC metrics and active flag.
    """
    versions = list_model_versions(current_admin["username"])
    for v in versions:
        v["_id"] = str(v["_id"])
    return versions


@router.post("/score_row", response_model=RiskSummary)
def score_row(
    features: CustomerFeatures,
    current_admin=Depends(get_current_admin),
):
    """
    Score a single synthetic customer behaviour row using the admin's active model.
    Used by the React 'Risk Lab' page.
    """
    mv = get_active_model_version(current_admin["username"])
    if not mv:
        raise HTTPException(status_code=400, detail="No active model")

    version = mv["version"]

    row_np = np.array(
        [[
            features.credit_limit,
            features.utilisation_pct,
            features.avg_payment_ratio,
            features.min_due_paid_freq,
            features.merchant_mix_index,
            features.cash_withdrawal_pct,
            features.recent_spend_change_pct,
        ]],
        dtype=float,
    )

    p_log, p_tree, p_nn = predict_probas_for(current_admin["username"], version, row_np)
    ensemble = compute_ensemble(p_log, p_tree, p_nn)
    ens = float(ensemble[0])
    prob = float(p_log[0])

    if ens < 0.2:
        band = "Very Low"
    elif ens < 0.4:
        band = "Low"
    elif ens < 0.6:
        band = "Medium"
    elif ens < 0.8:
        band = "High"
    else:
        band = "Critical"

    rules = evaluate_rules(features)

    top_features = [
        {"feature": "UtilisationPct", "value": features.utilisation_pct},
        {"feature": "CashWithdrawalPct", "value": features.cash_withdrawal_pct},
        {"feature": "AvgPaymentRatio", "value": features.avg_payment_ratio},
    ]

    return RiskSummary(
        ml_probability=prob,
        ensemble_probability=ens,
        risk_band=band,
        top_features=top_features,
        rules=rules,
    )
