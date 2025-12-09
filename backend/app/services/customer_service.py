# # app/services/customer_service.py
# from datetime import datetime, timedelta

# from app.models.customer import (
#     ensure_customer_for_user,
#     get_recent_transactions_for_customer,
# )


# def handle_add_transaction(db, current_user, tx):
#     """
#     Create a customer if needed, add a transaction for that customer,
#     recompute aggregates, and return (transaction_doc, updated_customer_doc).
#     """
#     customers = db["customers"]
#     transactions = db["transactions"]

#     customer = ensure_customer_for_user(db, current_user)
#     cust_id = str(customer["_id"])

#     tx_doc = {
#         "customer_id": cust_id,
#         "amount": float(tx.amount),
#         "category": tx.category,
#         "description": tx.description,
#         "timestamp": datetime.utcnow(),
#     }
#     transactions.insert_one(tx_doc)

#     # recompute aggregates
#     _update_customer_aggregates(db, customer)

#     customer = customers.find_one({"_id": customer["_id"]})
#     return tx_doc, customer


# def _update_customer_aggregates(db, customer):
#     """
#     Recompute main behavioural aggregates from transactions:
#     - UtilisationPct
#     - MerchantMixIndex
#     - CashWithdrawalPct
#     - RecentSpendChangePct
#     """
#     customers = db["customers"]
#     transactions = db["transactions"]

#     cust_id = str(customer["_id"])
#     credit_limit = float(customer.get("CreditLimit", 1.0))

#     txs = list(transactions.find({"customer_id": cust_id}))
#     total_spend = sum(float(t["amount"]) for t in txs) or 0.0
#     utilisation_pct = (total_spend / credit_limit) * 100.0 if credit_limit > 0 else 0.0

#     # simple MerchantMixIndex: distinct categories / total tx
#     categories = {t.get("category") for t in txs}
#     merchant_mix_index = (len(categories) / len(txs)) if txs else 0.0

#     # CashWithdrawalPct: share of spend where category == "cash"
#     cash_spend = sum(float(t["amount"]) for t in txs if t.get("category") == "cash")
#     cash_withdrawal_pct = (cash_spend / total_spend * 100.0) if total_spend > 0 else 0.0

#     # RecentSpendChangePct: last 30d vs previous 30d
#     now = datetime.utcnow()
#     last_30 = now - timedelta(days=30)
#     prev_60 = now - timedelta(days=60)

#     spend_last = sum(
#         float(t["amount"]) for t in txs if last_30 <= t["timestamp"] <= now
#     )
#     spend_prev = sum(
#         float(t["amount"]) for t in txs if prev_60 <= t["timestamp"] < last_30
#     )
#     if spend_prev > 0:
#         recent_change_pct = ((spend_last - spend_prev) / spend_prev) * 100.0
#     else:
#         recent_change_pct = 0.0

#     customers.update_one(
#         {"_id": customer["_id"]},
#         {
#             "$set": {
#                 "UtilisationPct": utilisation_pct,
#                 "MerchantMixIndex": merchant_mix_index,
#                 "CashWithdrawalPct": cash_withdrawal_pct,
#                 "RecentSpendChangePct": recent_change_pct,
#                 "updated_at": datetime.utcnow(),
#             }
#         },
#     )


# def get_user_transactions(db, current_user):
#     """
#     Return (transactions, customer_doc) for the logged-in user.
#     Used by /user/transactions to feed the user dashboard.
#     """
#     customer = ensure_customer_for_user(db, current_user)
#     cust_id = str(customer["_id"])
#     txs = get_recent_transactions_for_customer(db, cust_id, limit=20)
#     return txs, customer



# app/services/customer_service.py
from datetime import datetime, timedelta

from app.models.customer import (
    ensure_customer_for_user,
    get_recent_transactions_for_customer,
    customers_col,
    risk_scores_col,
)
from app.services.ml_service import score_customer


def handle_add_transaction(db, current_user, tx):
    """
    Create a customer if needed, add a transaction for that customer,
    recompute aggregates, re-score risk, and return
    (transaction_doc, updated_customer_doc).
    """
    customers = db["customers"]
    transactions = db["transactions"]

    customer = ensure_customer_for_user(db, current_user)
    cust_id = str(customer["_id"])

    tx_doc = {
        "customer_id": cust_id,
        "amount": float(tx.amount),
        "category": tx.category,
        "description": tx.description,
        "timestamp": datetime.utcnow(),
    }
    transactions.insert_one(tx_doc)

    # recompute aggregates and update customer doc
    _update_customer_aggregates(db, customer)

    # reload updated customer (aggregates now applied)
    customer = customers.find_one({"_id": customer["_id"]})

    # re-score with admin model (single admin "admin" or configurable)
    admin_username = "admin"
    risk = score_customer(admin_username, customer)

    # persist risk history and denormalised fields
    risk_doc = {
        "customer_id": cust_id,
        "username": admin_username,
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

    # return transaction and the latest customer snapshot
    customer = customers.find_one({"_id": customer["_id"]})
    return tx_doc, customer


def _update_customer_aggregates(db, customer):
    """
    Recompute main behavioural aggregates from transactions:
    - UtilisationPct
    - MerchantMixIndex
    - CashWithdrawalPct
    - RecentSpendChangePct
    """
    customers = db["customers"]
    transactions = db["transactions"]

    cust_id = str(customer["_id"])
    credit_limit = float(customer.get("CreditLimit", 1.0))

    txs = list(transactions.find({"customer_id": cust_id}))
    total_spend = sum(float(t["amount"]) for t in txs) or 0.0
    utilisation_pct = (total_spend / credit_limit) * 100.0 if credit_limit > 0 else 0.0

    # simple MerchantMixIndex: distinct categories / total tx
    categories = {t.get("category") for t in txs}
    merchant_mix_index = (len(categories) / len(txs)) if txs else 0.0

    # CashWithdrawalPct: share of spend where category == "cash"
    cash_spend = sum(float(t["amount"]) for t in txs if t.get("category") == "cash")
    cash_withdrawal_pct = (cash_spend / total_spend * 100.0) if total_spend > 0 else 0.0

    # RecentSpendChangePct: last 30d vs previous 30d
    now = datetime.utcnow()
    last_30 = now - timedelta(days=30)
    prev_60 = now - timedelta(days=60)

    spend_last = sum(
        float(t["amount"]) for t in txs if last_30 <= t["timestamp"] <= now
    )
    spend_prev = sum(
        float(t["amount"]) for t in txs if prev_60 <= t["timestamp"] < last_30
    )
    if spend_prev > 0:
        recent_change_pct = ((spend_last - spend_prev) / spend_prev) * 100.0
    else:
        recent_change_pct = 0.0

    customers.update_one(
        {"_id": customer["_id"]},
        {
            "$set": {
                "UtilisationPct": utilisation_pct,
                "MerchantMixIndex": merchant_mix_index,
                "CashWithdrawalPct": cash_withdrawal_pct,
                "RecentSpendChangePct": recent_change_pct,
                "updated_at": datetime.utcnow(),
            }
        },
    )


def get_user_transactions(db, current_user):
    """
    Return (transactions, customer_doc) for the logged-in user.
    Used by /user/transactions to feed the user dashboard.
    """
    customer = ensure_customer_for_user(db, current_user)
    cust_id = str(customer["_id"])
    txs = get_recent_transactions_for_customer(db, cust_id, limit=20)
    return txs, customer
