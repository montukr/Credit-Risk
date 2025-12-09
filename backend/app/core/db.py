from typing import Optional

from pymongo import MongoClient
from pymongo.errors import OperationFailure
from .config import settings

_client: Optional[MongoClient] = None
_db = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI)
    return _client


def ensure_indexes(db):
    """
    Ensures all global indexes exist.
    This is safe to run on every startup — MongoDB will ignore if index already exists.
    """
    try:
        db["customers"].create_index(
            [("user_id", 1), ("source", 1)],
            unique=True,
            name="uniq_user_source"
        )
    except OperationFailure as e:
        # If index already exists or namespace conflict, ignore safely
        print("Index creation skipped:", e)


def get_db():
    """
    Return the main MongoDB database object using the URI and DB name
    from settings. Also ensures required indexes exist.
    """
    global _db
    if _db is None:
        client = get_client()
        _db = client[settings.MONGODB_DB]

        # ⭐ Automatically enforce unique index on startup
        ensure_indexes(_db)

    return _db
