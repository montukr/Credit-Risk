# app/models/otp.py
import random
from datetime import datetime, timedelta
from app.core.db import get_db

def otp_col(db):
    return db["otp_codes"]


def generate_otp():
    return str(random.randint(100000, 999999))


def create_otp(db, phone: str, purpose="register"):
    code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    otp_col(db).insert_one({
        "phone": phone,
        "code": code,
        "purpose": purpose,
        "verified": False,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
    })

    return code


def verify_otp(db, phone: str, code: str, purpose="register"):
    rec = otp_col(db).find_one(
        {"phone": phone, "purpose": purpose},
        sort=[("created_at", -1)]
    )

    if not rec:
        return False

    if rec["expires_at"] < datetime.utcnow():
        return False

    if rec["code"] != code:
        return False

    otp_col(db).update_one(
        {"_id": rec["_id"]},
        {"$set": {"verified": True}}
    )

    return True
