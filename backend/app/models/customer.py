from datetime import datetime
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
        "CustomerID": f"C{str(user['_id'])[-6:]}",
        "CreditLimit": 100000,
        "UtilisationPct": 0.0,
        "AvgPaymentRatio": 100.0,
        "MinDuePaidFrequency": 100.0,
        "MerchantMixIndex": 0.5,
        "CashWithdrawalPct": 0.0,
        "RecentSpendChangePct": 0.0,
        "spend_cap": None,
        "category_blocks": [],
        "alerts_enabled": True,
        "created_at": datetime.utcnow(),
    }
    res = col.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc

def add_transaction(db, customer_id: str, amount: float, category: str, description: str | None):
    tx = {
        "customer_id": customer_id,
        "amount": amount,
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
    # very simple: UtilisationPct = total spend / credit limit * 100
    cust_id = str(customer["_id"])
    credit_limit = customer.get("CreditLimit", 1)
    pipeline = [
        {"$match": {"customer_id": cust_id}},
        {"$group": {"_id": "$customer_id", "total": {"$sum": "$amount"}}},
    ]
    res = list(transactions_col(db).aggregate(pipeline))
    total_spend = res[0]["total"] if res else 0.0
    utilisation_pct = (total_spend / credit_limit) * 100
    # keep other features simple constants for now
    update = {
        "UtilisationPct": utilisation_pct,
        "MerchantMixIndex": 0.5,
        "RecentSpendChangePct": 0.0,
        "CashWithdrawalPct": 0.0,
    }
    customers_col(db).update_one({"_id": customer["_id"]}, {"$set": update})
    customer.update(update)
    return customer

def admin_list_customers(db):
    return list(customers_col(db).find({}))

def admin_update_credit_limit(db, customer_id: str, new_limit: float):
    from bson import ObjectId
    customers_col(db).update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": {"CreditLimit": new_limit}}
    )

def admin_update_controls(db, customer_id: str, controls: dict):
    from bson import ObjectId
    customers_col(db).update_one(
        {"_id": ObjectId(customer_id)},
        {"$set": controls}
    )

def get_customer_by_id(db, customer_id: str):
    from bson import ObjectId
    return customers_col(db).find_one({"_id": ObjectId(customer_id)})
