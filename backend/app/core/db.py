from typing import Optional

from pymongo import MongoClient
from .config import settings


_client: Optional[MongoClient] = None
_db = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URI)
    return _client


def get_db():
    """
    Return the main MongoDB database object using the URI and DB name
    from settings.
    """
    global _db
    if _db is None:
        client = get_client()
        _db = client[settings.MONGODB_DB]
    return _db
