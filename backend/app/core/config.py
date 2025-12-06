from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Credit Risk Platform"
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "credit_risk_db"

    JWT_SECRET_KEY: str = "super-secret-key-change"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"

    class Config:
        env_file = ".env"

settings = Settings()
ARTIFACTS_DIR = settings.ARTIFACTS_DIR
