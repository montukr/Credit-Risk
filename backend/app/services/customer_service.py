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

# WhatsApp alert support
from app.services.whatsapp_service import send_flagged_risk_message
from app.models.user import get_user_by_id


# -----------------------------------------------------------
# ADD A TRANSACTION + RECOMPUTE AGGREGATES + RE-SCORE
# -----------------------------------------------------------
def handle_add_transaction(db, current_user, tx):
    """
    Insert a transaction, recompute aggregates, re-score risk,
    update customer + risk history, and trigger WhatsApp alerts
    when risk transitions into HIGH.
    """

    customers = customers_col(db)
    transactions = db["transactions"]

    # 1) Ensure the customer exists
    customer = ensure_customer_for_user(db, current_user)
    cust_id = str(customer["_id"])
    credit_limit = float(customer.get("CreditLimit", 1.0))

    # ⭐ Save previous risk band (for detecting transitions)
    previous_band = customer.get("risk_band")

    # 2) Compute current balance
    existing_txs = list(transactions.find({"customer_id": cust_id}))
    current_balance = sum(float(t["amount"]) for t in existing_txs) or 0.0

    # 3) Normalize category
    raw_category = (tx.category or "").strip().lower()
    if raw_category in ["atm", "atm_withdrawal", "atm withdrawal", "cash_withdrawal"]:
        category = "cash"
    else:
        category = raw_category or "other"

    # 4) Projected balance
    tx_amount = float(tx.amount)
    projected_balance = current_balance + tx_amount

    # 5) Prevent exceeding credit limit
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

    # 6) Insert transaction
    tx_doc = {
        "customer_id": cust_id,
        "amount": tx_amount,
        "category": category,
        "description": tx.description,
        "timestamp": datetime.utcnow(),
    }
    transactions.insert_one(tx_doc)

    # 7) Recompute aggregates
    _update_customer_aggregates(db, customer)

    # Refresh updated customer
    customer = customers.find_one({"_id": customer["_id"]})

    # 8) Re-score using default admin model
    admin_username = "admin"
    risk = score_customer(admin_username, customer)

    # 9) Insert risk history record
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

    # 10) Update customer record
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

    # ⭐ REFRESH snapshot after update
    updated_customer = customers.find_one({"_id": customer["_id"]})
    new_band = updated_customer.get("risk_band")

    # ------------------------------------------------------------
    # ⭐ 11) WhatsApp ALERT: Only if risk transitions → HIGH
    # ------------------------------------------------------------
    if new_band == "High":
        user_id = updated_customer.get("user_id")
        if user_id:
            user = get_user_by_id(db, user_id)
            phone = user.get("phone") if user else None

            if phone:
                reason = "Your recent spending behaviour indicates elevated delinquency risk."
                send_flagged_risk_message(
                    phone=phone,
                    username=user["username"],
                    band="High",
                    reason=reason,
                )

    # ------------------------------------------------------------
    return tx_doc, updated_customer


# -----------------------------------------------------------
# INTERNAL: Recompute aggregates
# -----------------------------------------------------------
def _update_customer_aggregates(db, customer):
    """
    Compute:
      - UtilisationPct
      - MerchantMixIndex
      - CashWithdrawalPct
      - RecentSpendChangePct
    """
    customers = customers_col(db)
    transactions = db["transactions"]

    cust_id = str(customer["_id"])
    credit_limit = float(customer.get("CreditLimit", 1.0))

    txs = list(transactions.find({"customer_id": cust_id}))
    total_spend = sum(float(t["amount"]) for t in txs) or 0.0

    utilisation_pct = (total_spend / credit_limit * 100.0) if credit_limit > 0 else 0.0
    categories = {t.get("category") for t in txs}
    merchant_mix_index = (len(categories) / len(txs)) if txs else 0.0

    cash_spend = sum(float(t["amount"]) for t in txs if t.get("category") == "cash")
    cash_withdrawal_pct = (cash_spend / total_spend * 100.0) if total_spend > 0 else 0.0

    now = datetime.utcnow()
    last_30 = now - timedelta(days=30)
    prev_60 = now - timedelta(days=60)

    spend_last = sum(float(t["amount"]) for t in txs if last_30 <= t["timestamp"] <= now)
    spend_prev = sum(float(t["amount"]) for t in txs if prev_60 <= t["timestamp"] < last_30)

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


# -----------------------------------------------------------
# BALANCE / AVAILABLE CREDIT HELPER
# -----------------------------------------------------------
def _get_balance_and_available(db, customer):
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
    customer = ensure_customer_for_user(db, current_user)
    balance, available, credit_limit = _get_balance_and_available(db, customer)

    customer["current_balance"] = balance
    customer["available_credit"] = available
    customer["CreditLimit"] = credit_limit

    cust_id = str(customer["_id"])
    txs = get_recent_transactions_for_customer(db, cust_id, limit=20)
    return txs, customer
