from ..models.customer import (
    ensure_customer_for_user,
    add_transaction,
    update_customer_aggregates_simple,
    get_recent_transactions_for_customer,
)

def handle_add_transaction(db, current_user, tx_req):
    customer = ensure_customer_for_user(db, current_user)
    tx = add_transaction(db, str(customer["_id"]), tx_req.amount, tx_req.category, tx_req.description)
    customer = update_customer_aggregates_simple(db, customer)
    return tx, customer

def get_user_transactions(db, current_user):
    customer = ensure_customer_for_user(db, current_user)
    txs = get_recent_transactions_for_customer(db, str(customer["_id"]))
    return txs, customer
