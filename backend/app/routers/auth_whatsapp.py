# app/routers/auth_whatsapp.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.db import get_db
from app.models.otp import create_otp, verify_otp
from app.models.user import create_user_with_phone, get_user_by_phone
from app.services.whatsapp_service import send_otp_message
from app.core.security import create_access_token

router = APIRouter(prefix="/auth/whatsapp", tags=["auth-whatsapp"])

class SendOtp(BaseModel):
    phone: str

class VerifyOtp(BaseModel):
    phone: str
    code: str
    username: str | None = None  # Only needed for new users


@router.post("/send_otp")
def send_otp(payload: SendOtp, db=Depends(get_db)):
    phone = payload.phone.strip()

    code = create_otp(db, phone)
    send_otp_message(phone, code)

    return {"status": "otp_sent"}


@router.post("/verify_otp")
def verify_otp_and_register(payload: VerifyOtp, db=Depends(get_db)):
    phone = payload.phone.strip()

    if not verify_otp(db, phone, payload.code):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Existing user → login
    user = get_user_by_phone(db, phone)
    if user:
        token = create_access_token(subject=str(user["_id"]), role=user["role"])
        return {"access_token": token, "username": user["username"], "role": user["role"]}

    # New user → require username
    if not payload.username:
        raise HTTPException(status_code=400, detail="Username required")

    user = create_user_with_phone(db, payload.username, phone)

    token = create_access_token(subject=str(user["_id"]), role=user["role"])
    return {"access_token": token, "username": user["username"], "role": user["role"]}
