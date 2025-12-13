import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Credit Risk Platform"

    # Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "credit_risk"

    # JWT
    JWT_SECRET_KEY: str = "change_this_to_a_long_random_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Artifacts
    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"

    # WhatsApp
    WHATSAPP_TOKEN: str | None = None
    WHATSAPP_PHONE_ID: str | None = None
    WHATSAPP_API_VERSION: str = "v21.0"
    WHATSAPP_TEMPLATE_WELCOME: str | None = None
    WHATSAPP_TEMPLATE_FLAGGED: str | None = None

    # CORS Configuration
    # We change the type hint to allow parsing into a list
    CORS_ORIGINS: Union[str, List[str]] = []

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        # This ignores extra fields in .env so it doesn't crash
        extra = "ignore" 

settings = Settings()
ARTIFACTS_DIR = settings.ARTIFACTS_DIR