import os
from pathlib import Path
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

    # ⭐ WhatsApp API credentials (must be declared here)
    WHATSAPP_TOKEN: str | None = None
    WHATSAPP_PHONE_ID: str | None = None
    WHATSAPP_API_VERSION: str = "v21.0"
    WHATSAPP_TEMPLATE_WELCOME: str | None = None
    WHATSAPP_TEMPLATE_FLAGGED: str | None = None

    # ⭐ CORS origins (comma-separated URLs, e.g. "http://localhost:5173,http://frontend-ip")
    CORS_ORIGINS: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
ARTIFACTS_DIR = settings.ARTIFACTS_DIR
