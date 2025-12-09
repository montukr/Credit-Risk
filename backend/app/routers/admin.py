# from fastapi import APIRouter, Depends, Query
# from ..core.deps import get_current_admin
# from ..core.db import get_db
# from ..schemas.customer import CustomerSummary, CreditLimitUpdate, ControlsUpdate
# from ..models.customer import (
#     admin_list_customers,
#     admin_update_credit_limit,
#     admin_update_controls,
#     get_customer_by_id,
#     get_customer_with_latest_score,
#     get_transactions_for_customer_id,
# )
# from ..core.serialization import to_str_id, to_str_id_list
# from ..models.customer import customers_col
# from app.services.ml_service import score_customer


# router = APIRouter(prefix="/admin", tags=["admin"])

# # @router.get("/customers", response_model=list[CustomerSummary])
# # def list_customers(current_admin=Depends(get_current_admin), db=Depends(get_db)):
# #     customers = admin_list_customers(db)
# #     customers = to_str_id_list(customers)
# #     summaries: list[CustomerSummary] = []
# #     for c in customers:
# #         summaries.append(
# #             CustomerSummary(
# #                 id=c["id"],
# #                 CustomerID=c.get("CustomerID", ""),
# #                 CreditLimit=float(c.get("CreditLimit", 0)),
# #                 UtilisationPct=float(c.get("UtilisationPct", 0)),
# #                 risk_band=c.get("risk_band"),
# #                 last_score=c.get("last_score"),
# #             )
# #         )
# #     return summaries

# @router.get("/customers", response_model=list[CustomerSummary])
# def list_customers(current_admin=Depends(get_current_admin), db=Depends(get_db)):
#     customers = admin_list_customers(db)
#     customers = to_str_id_list(customers)

#     summaries: list[CustomerSummary] = []

#     for c in customers:
#         summaries.append(
#             CustomerSummary(
#                 id=c["id"],
#                 CustomerID=c.get("CustomerID", ""),
#                 CreditLimit=float(c.get("CreditLimit", 0)),
#                 UtilisationPct=float(c.get("UtilisationPct", 0)),
#                 username=c.get("username"),          # <- new line
#                 risk_band=c.get("risk_band"),
#                 last_score=c.get("last_score"),
#             )
#         )

#     return summaries


# @router.patch("/customers/{customer_id}/credit_limit")
# def change_credit_limit(
#     customer_id: str,
#     payload: CreditLimitUpdate,
#     current_admin=Depends(get_current_admin),
#     db=Depends(get_db),
# ):
#     admin_update_credit_limit(db, customer_id, payload.credit_limit)
#     return {"status": "ok"}

# @router.patch("/customers/{customer_id}/controls")
# def change_controls(
#     customer_id: str,
#     payload: ControlsUpdate,
#     current_admin=Depends(get_current_admin),
#     db=Depends(get_db),
# ):
#     admin_update_controls(db, customer_id, payload.dict(exclude_unset=True))
#     return {"status": "ok"}

# @router.get("/customer/{customer_id}")
# def customer_detail(customer_id: str, current_admin=Depends(get_current_admin), db=Depends(get_db)):
#     customer = get_customer_with_latest_score(db, customer_id)
#     return to_str_id(customer) if customer else {}

# # in app/routers/admin.py
# @router.patch("/customers/{customer_id}/features")
# def admin_update_features(
#     customer_id: str,
#     payload: dict,
#     db=Depends(get_db),
#     current_admin=Depends(get_current_admin),
# ):
#     # payload keys: CreditLimit, UtilisationPct, AvgPaymentRatio, ...
#     admin_update_controls(db, customer_id, payload)
#     return {"status": "ok"}

# @router.get("/customer/{customer_id}/transactions")
# def customer_transactions(
#     customer_id: str,
#     current_admin=Depends(get_current_admin),
#     db=Depends(get_db),
# ):
#     txs = get_transactions_for_customer_id(db, customer_id)
#     return {"transactions": to_str_id_list(txs)}



# @router.get("/top/customers")
# def top_customers(
#     kind: str = Query("latest", enum=["latest", "flagged", "utilisation", "cash"]),
#     limit: int = Query(10, ge=1, le=50),
#     current_admin=Depends(get_current_admin),
#     db=Depends(get_db),
# ):
#     col = customers_col(db)

#     if kind == "latest":
#         cursor = (
#             col.find({"source": "app_user"})
#             .sort("created_at", -1)
#             .limit(limit)
#         )
#     elif kind == "flagged":
#         cursor = (
#             col.find({"source": "app_user", "risk_band": {"$in": ["High", "Critical"]}})
#             .sort("updated_at", -1)
#             .limit(limit)
#         )
#     elif kind == "utilisation":
#         cursor = (
#             col.find({"source": "app_user"})
#             .sort("UtilisationPct", -1)
#             .limit(limit)
#         )
#     elif kind == "cash":
#         cursor = (
#             col.find({"source": "app_user"})
#             .sort("CashWithdrawalPct", -1)
#             .limit(limit)
#         )
#     else:
#         cursor = []

#     rows = to_str_id_list(list(cursor))
#     return {"customers": rows}



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
                username=c.get("username"),
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
    customer = get_customer_with_latest_score(db, customer_id)
    return to_str_id(customer) if customer else {}


@router.patch("/customers/{customer_id}/features")
def admin_update_features(
    customer_id: str,
    payload: dict,
    db=Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Admin updates ML features (CreditLimit, UtilisationPct, etc.) for a customer,
    then re-scores and persists the latest risk band / score.
    """
    # 1) Apply feature updates
    admin_update_controls(db, customer_id, payload)

    # 2) Reload updated customer document
    customer = customers_col(db).find_one({"_id": ObjectId(customer_id)})
    if not customer:
        return {"status": "not_found"}

    # 3) Re-score with admin's active model
    risk = score_customer(current_admin["username"], customer)

    # 4) Persist into risk_scores history and denormalise onto customers
    cust_id = str(customer["_id"])
    risk_doc = {
        "customer_id": cust_id,
        "username": current_admin["username"],
        "ml_probability": risk["ml_probability"],
        "ensemble_probability": risk["ensemble_probability"],
        "risk_band": risk["risk_band"],
        "timestamp": datetime.utcnow(),
    }
    risk_scores_col(db).insert_one(risk_doc)

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


@router.get("/customer/{customer_id}/transactions")
def customer_transactions(
    customer_id: str,
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    txs = get_transactions_for_customer_id(db, customer_id)
    return {"transactions": to_str_id_list(txs)}


@router.get("/top/customers")
def top_customers(
    kind: str = Query("latest", enum=["latest", "flagged", "utilisation", "cash"]),
    limit: int = Query(10, ge=1, le=50),
    current_admin=Depends(get_current_admin),
    db=Depends(get_db),
):
    """
    Return top-N customers for dashboard cards:
    - latest: newest app_user customers
    - flagged: latest High/Critical band
    - utilisation: highest UtilisationPct
    - cash: highest CashWithdrawalPct
    """
    col = customers_col(db)

    if kind == "latest":
        cursor = (
            col.find({"source": "app_user"})
            .sort("created_at", -1)
            .limit(limit)
        )
    elif kind == "flagged":
        cursor = (
            col.find({"source": "app_user", "risk_band": {"$in": ["High", "Critical"]}})
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
