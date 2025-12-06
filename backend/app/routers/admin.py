from fastapi import APIRouter, Depends
from ..core.deps import get_current_admin
from ..core.db import get_db
from ..schemas.customer import CustomerSummary, CreditLimitUpdate, ControlsUpdate
from ..models.customer import (
    admin_list_customers,
    admin_update_credit_limit,
    admin_update_controls,
    get_customer_by_id,
)
from ..core.serialization import to_str_id, to_str_id_list  # NEW

router = APIRouter(prefix="/admin", tags=["admin"])

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
                risk_band=c.get("risk_band"),
                last_score=c.get("last_score"),
            )
        )
    return summaries

@router.patch("/customers/{customer_id}/credit_limit")
def change_credit_limit(
    customer_id: str,
    payload: CreditLimitUpdate,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    admin_update_credit_limit(db, customer_id, payload.credit_limit)
    return {"status": "ok"}

@router.patch("/customers/{customer_id}/controls")
def change_controls(
    customer_id: str,
    payload: ControlsUpdate,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    admin_update_controls(db, customer_id, payload.dict(exclude_unset=True))
    return {"status": "ok"}

@router.get("/customer/{customer_id}")
def customer_detail(
    customer_id: str,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    customer = get_customer_by_id(db, customer_id)
    return to_str_id(customer)
