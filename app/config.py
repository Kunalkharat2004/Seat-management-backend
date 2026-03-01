from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str

    # ── JWT ───────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # ── App ───────────────────────────────────────────────────────
    APP_ENV: str = "development"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"

    # ── Email (Resend) ────────────────────────────────────────────
    EMAIL_PROVIDER: str = "resend"
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "onboarding@resend.dev"
    EMAIL_OVERRIDE_TO: Optional[str] = None

    # ── Expiry Job ────────────────────────────────────────────────
    EXPIRY_HOUR: int = 10
    EXPIRY_MINUTE: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
