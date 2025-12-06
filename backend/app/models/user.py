from datetime import datetime

def user_collection(db):
    return db["users"]

def create_user(db, username: str, email: str, password_hash: str, role: str = "user"):
    col = user_collection(db)
    if col.find_one({"username": username}):
        raise ValueError("Username already exists")
    doc = {
        "username": username,
        "email": email,
        "hashed_password": password_hash,  # match your existing admin doc
        "role": role,
        "created_at": datetime.utcnow(),
        "last_login": None,
    }
    res = col.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc

def get_user_by_username(db, username: str):
    return user_collection(db).find_one({"username": username})

def update_last_login(db, username: str):
    user_collection(db).update_one(
        {"username": username},
        {"$set": {"last_login": datetime.utcnow()}}
    )
