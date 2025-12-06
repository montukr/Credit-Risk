from datetime import datetime

def model_versions_col(db):
    return db["model_versions"]

def register_model_version(db, username: str, version: int, metrics: dict, is_active: bool):
    if is_active:
        model_versions_col(db).update_many(
            {"username": username}, {"$set": {"is_active": False}}
        )
    doc = {
        "username": username,
        "version": version,
        "is_active": is_active,
        "logreg_auc": metrics["logreg_auc"],
        "tree_auc": metrics["tree_auc"],
        "nn_auc": metrics["nn_auc"],
        "created_at": datetime.utcnow(),
    }
    model_versions_col(db).insert_one(doc)

def get_active_model_version(db, username: str):
    return model_versions_col(db).find_one(
        {"username": username, "is_active": True},
        sort=[("created_at", -1)]
    )
