# app/routers/auth_whatsapp.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.db import get_db
from app.models.otp import create_otp, verify_otp
from app.models.user import get_user_by_phone
from app.services.whatsapp_service import send_otp_message
from app.core.security import create_access_token


router = APIRouter(prefix="/auth/whatsapp", tags=["auth-whatsapp"])


class SendOtp(BaseModel):
    phone: str


class VerifyOtp(BaseModel):
    phone: str
    code: str
    # username is NOT needed here anymore; account is created later
    username: str | None = None  # kept for backward-compat but unused



@router.post("/send_otp")
def send_otp(payload: SendOtp, db=Depends(get_db)):
    phone = payload.phone.strip()

    code = create_otp(db, phone)
    send_otp_message(phone, code)

    return {"status": "otp_sent"}



@router.post("/verify_otp")
def verify_otp_and_register(payload: VerifyOtp, db=Depends(get_db)):
    phone = payload.phone.strip()

    # 1) Validate OTP only
    if not verify_otp(db, phone, payload.code):
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # 2) If user already exists → treat as login and issue token
    user = get_user_by_phone(db, phone)
    if user:
        token = create_access_token(subject=str(user["_id"]), role=user["role"])
        return {
            "access_token": token,
            "username": user["username"],
            "role": user["role"],
            "is_new_user": False,
        }

    # 3) No user yet → just mark OTP as verified; frontend will now show
    #    the "Create Account" form and call the normal /auth/register endpoint.
    return {
        "status": "otp_verified",
        "is_new_user": True,
        "message": "OTP verified. Please complete registration to create your account.",
    }
