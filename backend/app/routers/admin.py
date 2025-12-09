from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, Query

from ..core.deps import get_current_admin
from ..core.db import get_db
from ..schemas.customer import CustomerSummary, CreditLimitUpdate, ControlsUpdate
from ..models.customer import (
    admin_list_customers,
    admin_update_credit_limit,
    admin_update_controls,
    get_customer_with_latest_score,
    get_transactions_for_customer_id,
    customers_col,
    risk_scores_col,
)
from ..core.serialization import to_str_id, to_str_id_list
from app.services.ml_service import score_customer

router = APIRouter(prefix="/admin", tags=["admin"])


# -----------------------------------------------------------
# LIST ALL CUSTOMERS (PORTFOLIO TABLE)
# -----------------------------------------------------------
@router.get("/customers", response_model=list[CustomerSummary])
def list_customers(current_admin=Depends(get_current_admin), db=Depends(get_db)):
    customers = admin_list_customers(db)
    customers = to_str_id_list(customers)

    summaries: list[CustomerSummary] = []

    for c in customers:
        summaries.append(
            CustomerSummary(
                id=c["id"],
                CustomerID=c.get("CustomerID", ""),
                CreditLimit=float(c.get("CreditLimit", 0)),
                UtilisationPct=float(c.get("UtilisationPct", 0)),
                CashWithdrawalPct=float(c.get("CashWithdrawalPct", 0)),
                username=c.get("username"),
                risk_band=c.get("risk_band"),
                last_score=c.get("last_score"),
            )
        )

    return summaries


# -----------------------------------------------------------
# CREDIT LIMIT UPDATE
# -----------------------------------------------------------
@router.patch("/customers/{customer_id}/credit_limit")
def change_credit_limit(
    customer_id: str,
    payload: CreditLimitUpdate,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    admin_update_credit_limit(db, customer_id, payload.credit_limit)
    return {"status": "ok"}


# -----------------------------------------------------------
# CONTROL UPDATE (spend caps, blocks, etc.)
# -----------------------------------------------------------
@router.patch("/customers/{customer_id}/controls")
def change_controls(
    customer_id: str,
    payload: ControlsUpdate,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    admin_update_controls(db, customer_id, payload.dict(exclude_unset=True))
    return {"status": "ok"}


# -----------------------------------------------------------
# CUSTOMER DETAIL PAGE INFO
# -----------------------------------------------------------
@router.get("/customer/{customer_id}")
def customer_detail(
    customer_id: str,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    """
    Uses get_customer_with_latest_score:
    - Does not overwrite up-to-date customer.risk_band / last_score
    - Only backfills from risk_scores when missing
    """
    customer = get_customer_with_latest_score(db, customer_id)
    return to_str_id(customer) if customer else {}


# -----------------------------------------------------------
# ADMIN FEATURE UPDATE + RE-SCORING
# -----------------------------------------------------------
@router.patch("/customers/{customer_id}/features")
def admin_update_features(
    customer_id: str,
    payload: dict,
    db=Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Admin updates ML features (e.g., UtilisationPct, AvgPaymentRatio),
    then immediately re-scores using the ML model and persists:
    - customer.risk_band
    - customer.last_score
    - a new risk_scores history row
    """

    # 1) Apply updates to customer document
    admin_update_controls(db, customer_id, payload)

    # 2) Reload updated customer doc
    customer = customers_col(db).find_one({"_id": ObjectId(customer_id)})
    if not customer:
        return {"status": "not_found"}

    # 3) Re-score using ML
    risk = score_customer(current_admin["username"], customer)

    # 4) Save to risk history
    risk_scores_col(db).insert_one(
        {
            "customer_id": str(customer["_id"]),
            "username": current_admin["username"],
            "ml_probability": risk["ml_probability"],
            "ensemble_probability": risk["ensemble_probability"],
            "risk_band": risk["risk_band"],
            "timestamp": datetime.utcnow(),
        }
    )

    # 5) Denormalise onto customers collection
    customers_col(db).update_one(
        {"_id": customer["_id"]},
        {
            "$set": {
                "risk_band": risk["risk_band"],
                "last_score": risk["ensemble_probability"],
                "updated_at": datetime.utcnow(),
            }
        },
    )

    return {
        "status": "ok",
        "risk_band": risk["risk_band"],
        "last_score": risk["ensemble_probability"],
    }


# -----------------------------------------------------------
# CUSTOMER TRANSACTIONS
# -----------------------------------------------------------
@router.get("/customer/{customer_id}/transactions")
def customer_transactions(
    customer_id: str,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    txs = get_transactions_for_customer_id(db, customer_id)
    return {"transactions": to_str_id_list(txs)}


# -----------------------------------------------------------
# TOP CUSTOMERS (FLAGGED, UTILISATION, CASH)
# -----------------------------------------------------------
@router.get("/top/customers")
def top_customers(
    kind: str = Query("latest", enum=["latest", "flagged", "utilisation", "cash"]),
    limit: int = Query(10, ge=1, le=50),
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    """
    - latest → newest app_user customers
    - flagged → High (current ML band)
    - utilisation → highest UtilisationPct
    - cash → highest CashWithdrawalPct
    """
    col = customers_col(db)

    if kind == "latest":
        cursor = (
            col.find({"source": "app_user"})
            .sort("created_at", -1)
            .limit(limit)
        )
    elif kind == "flagged":
        # ML model outputs only Low / Medium / High
        cursor = (
            col.find({"source": "app_user", "risk_band": "High"})
            .sort("updated_at", -1)
            .limit(limit)
        )
    elif kind == "utilisation":
        cursor = (
            col.find({"source": "app_user"})
            .sort("UtilisationPct", -1)
            .limit(limit)
        )
    elif kind == "cash":
        cursor = (
            col.find({"source": "app_user"})
            .sort("CashWithdrawalPct", -1)
            .limit(limit)
        )
    else:
        cursor = []

    rows = to_str_id_list(list(cursor))
    return {"customers": rows}
