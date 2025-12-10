# app/models/user.py
from datetime import datetime
from bson import ObjectId
from pymongo.collection import Collection
from ..core.db import get_db


def user_collection(db=None) -> Collection:
    if db is None:
        db = get_db()
    return db["users"]


def create_user(db, username: str, email: str, password_hash: str, role: str = "user", phone: str = None):
    """
    Create a new user with a unique username.

    Raises:
        ValueError: if the username already exists.
    """
    col = user_collection(db)

    # Application-level uniqueness check
    if col.find_one({"username": username}):
        raise ValueError("Username already exists")

    doc = {
        "username": username,
        "email": email,
        "hashed_password": password_hash,
        "role": role,
        "phone": phone,        # ⭐ NEW: store WhatsApp number
        "created_at": datetime.utcnow(),
        "last_login": None,
    }
    res = col.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc


def get_user_by_username(db, username: str):
    return user_collection(db).find_one({"username": username})


def get_user_by_id(db, user_id: str):
    """
    Fetch user by ObjectId string. Required for WhatsApp alerts.
    """
    try:
        return user_collection(db).find_one({"_id": ObjectId(user_id)})
    except:
        return None


def update_last_login(db, username: str):
    user_collection(db).update_one(
        {"username": username},
        {"$set": {"last_login": datetime.utcnow()}},
    )
