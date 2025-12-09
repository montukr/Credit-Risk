# app/services/customer_service.py
from datetime import datetime, timedelta

from fastapi import HTTPException

from app.models.customer import (
    ensure_customer_for_user,
    get_recent_transactions_for_customer,
    customers_col,
    risk_scores_col,
)
from app.services.ml_service import score_customer


# -----------------------------------------------------------
# ADD A TRANSACTION + RECOMPUTE AGGREGATES + RE-SCORE
# -----------------------------------------------------------
def handle_add_transaction(db, current_user, tx):
    """
    Create (or load) the customer for this user, insert a transaction
    if within limit, recompute aggregates, re-score risk, persist updated
    risk state, and return (transaction_doc, updated_customer_doc).
    """

    customers = customers_col(db)
    transactions = db["transactions"]

    # 1) Ensure the customer exists
    customer = ensure_customer_for_user(db, current_user)
    cust_id = str(customer["_id"])
    credit_limit = float(customer.get("CreditLimit", 1.0))

    # 2) Compute current balance (sum of all tx amounts)
    existing_txs = list(transactions.find({"customer_id": cust_id}))
    current_balance = sum(float(t["amount"]) for t in existing_txs) or 0.0

    # 3) Normalise category (treat ATM-like categories as "cash")
    raw_category = (tx.category or "").strip().lower()
    if raw_category in ["atm", "atm_withdrawal", "atm withdrawal", "cash_withdrawal"]:
        category = "cash"
    else:
        category = raw_category or "other"

    # 4) Projected balance after this transaction
    tx_amount = float(tx.amount)
    projected_balance = current_balance + tx_amount

    # 5) HARD CAP: do not allow utilisation > 100% of CreditLimit
    if projected_balance > credit_limit:
        available = max(0.0, credit_limit - current_balance)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "LIMIT_EXCEEDED",
                "message": "Credit limit fully utilised. Cannot process this transaction.",
                "available_credit": available,
                "credit_limit": credit_limit,
            },
        )

    # 6) Insert the transaction (only if within limit)
    tx_doc = {
        "customer_id": cust_id,
        "amount": tx_amount,
        "category": category,
        "description": tx.description,
        "timestamp": datetime.utcnow(),
    }
    transactions.insert_one(tx_doc)

    # 7) Recompute aggregates + write into customers collection
    _update_customer_aggregates(db, customer)

    # Refresh customer doc after aggregates update
    customer = customers.find_one({"_id": customer["_id"]})

    # 8) Re-score using the default admin model
    admin_username = "admin"
    risk = score_customer(admin_username, customer)

    # 9) Write risk to history (risk_scores)
    risk_scores_col(db).insert_one(
        {
            "customer_id": cust_id,  # canonical key
            "username": admin_username,
            "ml_probability": risk["ml_probability"],
            "ensemble_probability": risk["ensemble_probability"],
            "risk_band": risk["risk_band"],
            "timestamp": datetime.utcnow(),
        }
    )

    # 10) Write canonical values into customers doc
    customers.update_one(
        {"_id": customer["_id"]},
        {
            "$set": {
                "risk_band": risk["risk_band"],
                "last_score": risk["ensemble_probability"],
                "updated_at": datetime.utcnow(),
            }
        },
    )

    # 11) Return latest customer snapshot
    customer = customers.find_one({"_id": customer["_id"]})
    return tx_doc, customer


# -----------------------------------------------------------
# INTERNAL: Recompute aggregates
# -----------------------------------------------------------
def _update_customer_aggregates(db, customer):
    """
    Recompute behavioural aggregates:
    - UtilisationPct
    - MerchantMixIndex
    - CashWithdrawalPct
    - RecentSpendChangePct
    """
    customers = customers_col(db)
    transactions = db["transactions"]

    cust_id = str(customer["_id"])
    credit_limit = float(customer.get("CreditLimit", 1.0))

    # All transactions for customer
    txs = list(transactions.find({"customer_id": cust_id}))
    total_spend = sum(float(t["amount"]) for t in txs) or 0.0

    # Utilisation %
    utilisation_pct = (total_spend / credit_limit * 100.0) if credit_limit > 0 else 0.0

    # Merchant mix index
    categories = {t.get("category") for t in txs}
    merchant_mix_index = (len(categories) / len(txs)) if txs else 0.0

    # Cash withdrawal %
    cash_spend = sum(float(t["amount"]) for t in txs if t.get("category") == "cash")
    cash_withdrawal_pct = (cash_spend / total_spend * 100.0) if total_spend > 0 else 0.0

    # Recent spend change %
    now = datetime.utcnow()
    last_30 = now - timedelta(days=30)
    prev_60 = now - timedelta(days=60)

    spend_last = sum(
        float(t["amount"]) for t in txs
        if last_30 <= t["timestamp"] <= now
    )
    spend_prev = sum(
        float(t["amount"]) for t in txs
        if prev_60 <= t["timestamp"] < last_30
    )

    if spend_prev > 0:
        recent_change_pct = ((spend_last - spend_prev) / spend_prev) * 100.0
    else:
        recent_change_pct = 0.0

    # Persist aggregates
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


# -----------------------------------------------------------
# BALANCE / AVAILABLE CREDIT HELPER
# -----------------------------------------------------------
def _get_balance_and_available(db, customer):
    """
    Compute current balance and available credit for a customer.
    """
    transactions = db["transactions"]
    cust_id = str(customer["_id"])
    txs = list(transactions.find({"customer_id": cust_id}))
    balance = sum(float(t["amount"]) for t in txs) or 0.0
    credit_limit = float(customer.get("CreditLimit", 1.0))
    available = max(0.0, credit_limit - balance)
    return balance, available, credit_limit


# -----------------------------------------------------------
# FETCH USER TRANSACTIONS
# -----------------------------------------------------------
def get_user_transactions(db, current_user):
    """
    Return (transactions, customer_doc) for the logged-in user.
    Used by /user/transactions to show dashboard history.
    Attaches current_balance and available_credit to the customer.
    """
    customer = ensure_customer_for_user(db, current_user)
    balance, available, credit_limit = _get_balance_and_available(db, customer)
    customer["current_balance"] = balance
    customer["available_credit"] = available
    customer["CreditLimit"] = credit_limit
    cust_id = str(customer["_id"])
    txs = get_recent_transactions_for_customer(db, cust_id, limit=20)
    return txs, customer
