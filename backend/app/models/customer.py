from datetime import datetime, timedelta
from bson import ObjectId


def customers_col(db):
    return db["customers"]


def transactions_col(db):
    return db["transactions"]


def risk_scores_col(db):
    return db["risk_scores"]


def ensure_customer_for_user(db, user):
    col = customers_col(db)
    existing = col.find_one({"user_id": str(user["_id"])})
    if existing:
        return existing

    doc = {
        "user_id": str(user["_id"]),
        "username": user["username"],          # for admin search
        "CustomerID": user["username"],        # show username as card name
        "CreditLimit": 100000.0,
        "UtilisationPct": 0.0,
        "AvgPaymentRatio": 100.0,             # demo defaults
        "MinDuePaidFrequency": 100.0,
        "MerchantMixIndex": 0.5,
        "CashWithdrawalPct": 0.0,
        "RecentSpendChangePct": 0.0,
        "spend_cap": None,
        "category_blocks": [],
        "alerts_enabled": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    res = col.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


def add_transaction(db, customer_id: str, amount: float, category: str, description: str | None):
    tx = {
        "customer_id": customer_id,
        "amount": float(amount),
        "category": category,
        "description": description,
        "timestamp": datetime.utcnow(),
    }
    transactions_col(db).insert_one(tx)
    return tx


def get_recent_transactions_for_customer(db, customer_id: str, limit: int = 20):
    return list(
        transactions_col(db)
        .find({"customer_id": customer_id})
        .sort("timestamp", -1)
        .limit(limit)
    )


def update_customer_aggregates_simple(db, customer):
    """
    Recompute main behavioural aggregates from transactions:
    - UtilisationPct
    - MerchantMixIndex
    - CashWithdrawalPct
    - RecentSpendChangePct

    Keep AvgPaymentRatio and MinDuePaidFrequency as static demo values for now.
    """
    cust_id = str(customer["_id"])
    credit_limit = float(customer.get("CreditLimit", 1.0))

    txs = list(transactions_col(db).find({"customer_id": cust_id}))
    total_spend = sum(float(t["amount"]) for t in txs) or 0.0
    utilisation_pct = (total_spend / credit_limit) * 100.0 if credit_limit > 0 else 0.0

    # Simple merchant mix: distinct categories / total tx
    merchant_mix_index = 0.0
    if txs:
        categories = {t.get("category") for t in txs}
        merchant_mix_index = len(categories) / len(txs)

    # Cash withdrawal %: share of spend where category == "cash"
    cash_spend = sum(float(t["amount"]) for t in txs if t.get("category") == "cash")
    cash_withdrawal_pct = (cash_spend / total_spend * 100.0) if total_spend > 0 else 0.0

    # Recent spend change: last 30 days vs previous 30 days
    now = datetime.utcnow()
    last_30 = now - timedelta(days=30)
    prev_60 = now - timedelta(days=60)

    spend_last = sum(
        float(t["amount"])
        for t in txs
        if last_30 <= t["timestamp"] <= now
    )
    spend_prev = sum(
        float(t["amount"])
        for t in txs
        if prev_60 <= t["timestamp"] < last_30
    )
    if spend_prev > 0:
        recent_change_pct = ((spend_last - spend_prev) / spend_prev) * 100.0
    else:
        recent_change_pct = 0.0

    update = {
        "UtilisationPct": utilisation_pct,
        "MerchantMixIndex": merchant_mix_index,
        "CashWithdrawalPct": cash_withdrawal_pct,
        "RecentSpendChangePct": recent_change_pct,
        "updated_at": datetime.utcnow(),
    }
    customers_col(db).update_one({"_id": customer["_id"]}, {"$set": update})
    customer.update(update)
    return customer


def admin_list_customers(db):
    # expose username/CustomerID for search and display
    return list(
        customers_col(db).find(
            {},
            {
                "CustomerID": 1,
                "username": 1,
                "CreditLimit": 1,
                "UtilisationPct": 1,
                "risk_band": 1,
                "last_score": 1,
            },
        )
    )


def admin_update_credit_limit(db, customer_id: str, new_limit: float):
    customers_col(db).update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": {"CreditLimit": float(new_limit)}},
    )


def admin_update_controls(db, customer_id: str, controls: dict):
    customers_col(db).update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": controls},
    )


def get_customer_by_id(db, customer_id: str):
    return customers_col(db).find_one({"_id": ObjectId(customer_id)})

def update_customer_credit_limit_for_user(db, user, new_limit: float):
    """
    Update CreditLimit for the logged-in user's customer record.
    """
    col = customers_col(db)
    customer = ensure_customer_for_user(db, user)
    col.update_one(
        {"_id": customer["_id"]},
        {"$set": {"CreditLimit": float(new_limit), "updated_at": datetime.utcnow()}},
    )
