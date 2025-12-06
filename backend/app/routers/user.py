from fastapi import APIRouter, Depends
from ..core.deps import get_current_customer
from ..core.db import get_db
from ..schemas.transaction import TransactionCreate
from ..schemas.risk import RiskSummary, FeatureContribution
from ..services.customer_service import handle_add_transaction, get_user_transactions
from ..services.ml_service import score_customer
from ..core.serialization import to_str_id, to_str_id_list  # NEW

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/transactions/add")
def add_transaction(
    tx: TransactionCreate,
    current_user=Depends(get_current_customer),
    db=Depends(get_db),
):
    tx_doc, customer = handle_add_transaction(db, current_user, tx)
    return {
        "transaction": to_str_id(tx_doc),
        "customer": to_str_id(customer),
    }

@router.get("/transactions")
def list_transactions(
    current_user=Depends(get_current_customer),
    db=Depends(get_db),
):
    txs, customer = get_user_transactions(db, current_user)
    return {
        "transactions": to_str_id_list(txs),
        "customer": to_str_id(customer),
    }

@router.get("/risk_summary", response_model=RiskSummary)
def risk_summary(
    current_user=Depends(get_current_customer),
    db=Depends(get_db),
):
    from ..models.customer import ensure_customer_for_user
    customer = ensure_customer_for_user(db, current_user)
    admin_username = "admin"
    risk = score_customer(db, admin_username, customer)
    return RiskSummary(
        ml_probability=risk["ml_probability"],
        ensemble_probability=risk["ensemble_probability"],
        risk_band=risk["risk_band"],
        top_features=[
            FeatureContribution(feature=f["feature"], value=f["value"])
            for f in risk["top_features"][:3]
        ],
    )
