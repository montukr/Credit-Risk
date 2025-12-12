# app/services/auth_service.py

from fastapi import HTTPException, status
from datetime import datetime
from ..core.security import hash_password, verify_password, create_access_token
from ..models.user import create_user, get_user_by_username, update_last_login

# WhatsApp senders
from app.services.whatsapp_service import (
    send_welcome_message
)


# ---------------------------------------------------------
# REGISTER (NO WHATSAPP MESSAGE — AND MARK FIRST LOGIN DONE)
# ---------------------------------------------------------
def register_user(db, username: str, email: str, password: str, phone: str | None = None):
    pwd_hash = hash_password(password)

    try:
        user = create_user(
            db,
            username,
            email,
            pwd_hash,
            role="user",
            phone=phone
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    print("✅ User registered:", user)

    # ⭐ IMPORTANT FIX:
    # Mark last_login so auto-login after registration does NOT trigger welcome.
    update_last_login(db, username)

    return user   # do NOT send WhatsApp message here


# ---------------------------------------------------------
# LOGIN (SEND WELCOME ONLY ON FIRST REAL LOGIN)
# ---------------------------------------------------------
def login_user(db, username: str, password: str):
    user = get_user_by_username(db, username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    stored_hash = user.get("hashed_password") or user.get("password_hash")
    if not stored_hash or not verify_password(password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Detect true FIRST LOGIN
    is_first_login = user.get("last_login") is None
    phone = user.get("phone")
    role = user.get("role")

    print("🔍 First login?", is_first_login)
    print("📞 User phone:", phone)
    print("👤 User role:", role)

    # Update last_login NOW
    update_last_login(db, username)

    # -----------------------------------------------------
    # WHATSAPP LOGIC
    # -----------------------------------------------------
    # Do not send any WhatsApp messages for admins
    if role != "admin" and phone:
        if is_first_login:
            # First REAL login — send welcome + hello_world
            print("🔥 Sending WhatsApp WELCOME template (first login)…")
            send_welcome_message(phone, username)

        else:
            # All other logins → send only hello_world
            print("ℹ Not first login — sending HELLO_WORLD only.")
            send_welcome_message(phone, username)
    else:
        print("ℹ Skipping WhatsApp sends for admin or missing phone.")
    # -----------------------------------------------------

    token = create_access_token(subject=username, role=user["role"])
    return token, user
