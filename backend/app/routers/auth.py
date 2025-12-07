from fastapi import APIRouter, Depends
from ..core.db import get_db
from ..schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from ..services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db=Depends(get_db)):
    user = register_user(db, payload.username, payload.email, payload.password)
    token, _ = login_user(db, payload.username, payload.password)
    return TokenResponse(
        access_token=token,
        username=user["username"],
        role=user["role"],
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db=Depends(get_db)):
    token, user = login_user(db, payload.username, payload.password)
    return TokenResponse(
        access_token=token,
        username=user["username"],
        role=user["role"],
    )
