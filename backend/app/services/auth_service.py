from fastapi import HTTPException, status
from ..core.security import hash_password, verify_password, create_access_token
from ..models.user import create_user, get_user_by_username, update_last_login

def register_user(db, username: str, email: str, password: str):
    pwd_hash = hash_password(password)
    try:
        # default new users to "user" role
        user = create_user(db, username, email, pwd_hash, role="user")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return user

def login_user(db, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    stored_hash = user.get("hashed_password") or user.get("password_hash")
    if not stored_hash or not verify_password(password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    update_last_login(db, username)
    token = create_access_token(subject=username, role=user["role"])
    return token, user
