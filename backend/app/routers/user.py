from fastapi import APIRouter, Depends

from app.core.deps import get_current_customer
from app.core.db import get_db
from app.schemas.transaction import TransactionCreate
from app.schemas.risk import RiskSummary
from app.schemas.customer import CreditLimitUpdate
from app.services.customer_service import handle_add_transaction, get_user_transactions
from app.services.ml_service import score_customer
from app.core.serialization import to_str_id, to_str_id_list
from app.models.customer import (
    ensure_customer_for_user,
    update_customer_credit_limit_for_user,
)

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
    # ensure customer doc exists
    customer = ensure_customer_for_user(db, current_user)

    # for now, single admin model owner
    admin_username = "admin"

    # score_customer only takes (admin_username, customer)
    risk = score_customer(admin_username, customer)

    return RiskSummary(
        ml_probability=risk["ml_probability"],
        ensemble_probability=risk["ensemble_probability"],
        risk_band=risk["risk_band"],
        top_features=[
            {"feature": f["feature"], "value": f["value"]}
            for f in risk["top_features"]
        ],
        rules=[],
    )


@router.patch("/credit_limit")
def update_own_credit_limit(
    payload: CreditLimitUpdate,
    current_user=Depends(get_current_customer),
    db=Depends(get_db),
):
    update_customer_credit_limit_for_user(db, current_user, payload.credit_limit)
    return {"status": "ok"}
