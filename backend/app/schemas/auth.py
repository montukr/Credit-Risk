from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    email: EmailStr
    password: str = Field(min_length=4, max_length=72)
    phone: str | None = None   # ← Added for WhatsApp


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=4, max_length=72)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
