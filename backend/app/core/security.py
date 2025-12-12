# from datetime import datetime, timedelta
# from typing import Optional
# from jose import jwt, JWTError
# from passlib.context import CryptContext
# from .config import settings

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)

# def verify_password(plain: str, hashed: str) -> bool:
#     return pwd_context.verify(plain, hashed)

# def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
#     if expires_delta is None:
#         expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode = {
#         "sub": subject,
#         "role": role,
#         "exp": datetime.utcnow() + expires_delta,
#     }
#     return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

# def decode_token(token: str):
#     try:
#         payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
#         return payload
#     except JWTError:
#         return None


from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings

# --- CONFIGURATION ---
JWT_CLAIMS = ["sub", "role", "exp", "iat"]

# We use bcrypt with auto-deprecation for older schemes if needed.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- PASSWORD FUNCTIONS ---

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    Truncates to 72 bytes to satisfy bcrypt's length limit.
    """
    # Truncate to 72 bytes (bcrypt limit)
    truncated_password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(truncated_password_bytes)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifies a plain-text password against a stored bcrypt hash.
    """
    # Must truncate plain text to match the hashing logic
    truncated_plain_bytes = plain.encode('utf-8')[:72]
    return pwd_context.verify(truncated_plain_bytes, hashed)

# --- JWT TOKEN FUNCTIONS ---

def create_access_token(
    subject: str, 
    role: str, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a signed JWT access token."""
    
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Use timezone.utc for standard compliance
    now = datetime.now(timezone.utc)
    
    to_encode: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": now + expires_delta,
        "iat": now,
    }
    
    # Convert datetimes to timestamps for JWT standard compliance
    to_encode["exp"] = int(to_encode["exp"].timestamp())
    to_encode["iat"] = int(to_encode["iat"].timestamp())
    
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": True, "verify_aud": False}
        )
        return payload
    except JWTError:
        return None