from datetime import datetime
from app.core.db import get_db

def _col():
    return get_db()["model_versions"]

def register_model_version(username: str, version: int, metrics: dict, is_active: bool = True):
    col = _col()
    if is_active:
        col.update_many({"username": username}, {"$set": {"is_active": False}})
    col.insert_one(
        {
            "username": username,
            "version": version,
            "is_active": is_active,
            "logreg_auc": metrics["logreg_auc"],
            "tree_auc": metrics["tree_auc"],
            "nn_auc": metrics["nn_auc"],
            "created_at": datetime.utcnow(),
        }
    )

def get_active_model_version(username: str):
    col = _col()
    return col.find_one(
        {"username": username, "is_active": True},
        sort=[("created_at", -1)],
    )
