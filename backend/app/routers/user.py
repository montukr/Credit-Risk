# # app/routers/user.py

# from datetime import datetime

# from fastapi import APIRouter, Depends

# from app.core.deps import get_current_customer
# from app.core.db import get_db
# from app.schemas.transaction import TransactionCreate
# from app.schemas.risk import RiskSummary
# from app.schemas.customer import CreditLimitUpdate
# from app.services.customer_service import handle_add_transaction, get_user_transactions
# from app.services.ml_service import score_customer
# from app.core.serialization import to_str_id, to_str_id_list
# from app.models.customer import (
#     ensure_customer_for_user,
#     update_customer_credit_limit_for_user,
#     customers_col,
#     risk_scores_col,
# )

# router = APIRouter(prefix="/user", tags=["user"])


# @router.post("/transactions/add")
# def add_transaction(
#     tx: TransactionCreate,
#     current_user=Depends(get_current_customer),
#     db=Depends(get_db),
# ):
#     """
#     Create a transaction for the logged-in customer and return both
#     the transaction doc and updated customer aggregates.
#     """
#     tx_doc, customer = handle_add_transaction(db, current_user, tx)
#     return {
#         "transaction": to_str_id(tx_doc),
#         "customer": to_str_id(customer),
#     }


# @router.get("/transactions")
# def list_transactions(
#     current_user=Depends(get_current_customer),
#     db=Depends(get_db),
# ):
#     """
#     Return recent transactions and the current customer profile
#     for the logged-in user.
#     """
#     txs, customer = get_user_transactions(db, current_user)
#     return {
#         "transactions": to_str_id_list(txs),
#         "customer": to_str_id(customer),
#     }



# @router.get("/risk_summary", response_model=RiskSummary)
# def risk_summary(
#     current_user=Depends(get_current_customer),
#     db=Depends(get_db),
# ):
#     """
#     Score the logged-in user's customer profile using the admin's model,
#     persist the latest risk score, and return a RiskSummary.
#     """
#     # ensure customer doc exists
#     customer = ensure_customer_for_user(db, current_user)

#     # for now, single admin model owner
#     admin_username = "admin"

#     # score_customer only takes (admin_username, customer)
#     risk = score_customer(admin_username, customer)

#     # Use business CustomerID as the key (consistent with batch/single scoring)
#     cust_id = customer["CustomerID"]

#     # Persist this score into risk_scores collection
#     risk_doc = {
#         "customer_id": cust_id,
#         "username": admin_username,
#         "ml_probability": risk["ml_probability"],
#         "ensemble_probability": risk["ensemble_probability"],
#         "risk_band": risk["risk_band"],
#         "timestamp": datetime.utcnow(),
#     }
#     risk_scores_col(db).insert_one(risk_doc)

#     # Denormalise onto customers so admin views can read risk_band / last_score
#     customers_col(db).update_one(
#         {"CustomerID": cust_id},
#         {
#             "$set": {
#                 "risk_band": risk["risk_band"],
#                 "last_score": risk["ensemble_probability"],
#                 "updated_at": datetime.utcnow(),
#             }
#         },
#     )

#     return RiskSummary(
#         ml_probability=risk["ml_probability"],
#         ensemble_probability=risk["ensemble_probability"],
#         risk_band=risk["risk_band"],
#         top_features=[
#             {"feature": f["feature"], "value": f["value"]}
#             for f in risk["top_features"]
#         ],
#         rules=[],
#     )


# @router.patch("/credit_limit")
# def update_own_credit_limit(
#     payload: CreditLimitUpdate,
#     current_user=Depends(get_current_customer),
#     db=Depends(get_db),
# ):
#     """
#     Allow the logged-in user to adjust their own credit limit.
#     """
#     update_customer_credit_limit_for_user(db, current_user, payload.credit_limit)
#     return {"status": "ok"}



# app/routers/user.py

from datetime import datetime

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
    customers_col,
    risk_scores_col,
)

router = APIRouter(prefix="/user", tags=["user"])


# -----------------------------------------------------------
# ADD A TRANSACTION
# -----------------------------------------------------------
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


# -----------------------------------------------------------
# LIST USER TRANSACTIONS
# -----------------------------------------------------------
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


# -----------------------------------------------------------
# USER RISK SUMMARY (SCORES + PERSISTS)
# -----------------------------------------------------------
@router.get("/risk_summary", response_model=RiskSummary)
def risk_summary(
    current_user=Depends(get_current_customer),
    db=Depends(get_db),
):
    """
    Score the logged-in user's customer profile,
    persist the latest risk score using the same
    canonical logic used by admin/transactions.
    """
    # 1) Ensure customer document exists
    customer = ensure_customer_for_user(db, current_user)

    # 2) Score with admin model
    admin_username = "admin"
    risk = score_customer(admin_username, customer)

    # 3) Canonical risk key (MUST match admin + tx updates)
    cust_id = str(customer["_id"])

    # 4) Write to risk_scores history
    risk_scores_col(db).insert_one(
        {
            "customer_id": cust_id,
            "username": admin_username,
            "ml_probability": risk["ml_probability"],
            "ensemble_probability": risk["ensemble_probability"],
            "risk_band": risk["risk_band"],
            "timestamp": datetime.utcnow(),
        }
    )

    # 5) Denormalise onto customers for dashboard/admin
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

    # 6) Return response
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


# -----------------------------------------------------------
# USER SELF-SERVICE CREDIT LIMIT UPDATE
# -----------------------------------------------------------
@router.patch("/credit_limit")
def update_own_credit_limit(
    payload: CreditLimitUpdate,
    current_user=Depends(get_current_customer),
    db=Depends(get_db),
):
    update_customer_credit_limit_for_user(db, current_user, payload.credit_limit)
    return {"status": "ok"}
