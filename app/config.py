from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/seat_management"

    # ── JWT ───────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # ── App ───────────────────────────────────────────────────────
    APP_ENV: str = "development"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # ── Expiry Job ────────────────────────────────────────────────
    EXPIRY_HOUR: int = 10
    EXPIRY_MINUTE: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
