"""
backend/config.py
-----------------
Central configuration for the FastAPI backend.
Edit SECRET_KEY before deploying anywhere beyond localhost.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    # ── Database ─────────────────────────────────────────────────────────────
    DB_PATH: str = str(
        Path(__file__).parent.parent / "db" / "personal_financial_manager.db"
    )

    # ── JWT ───────────────────────────────────────────────────────────────────
    # Generate a real secret with: python -c "import secrets; print(secrets.token_hex(32))"
    # Then put it in a .env file:  SECRET_KEY=your_secret_here
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_use_secrets_token_hex_32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week — convenient for personal use

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Add your phone's browser origin here if needed, e.g. "http://192.168.1.x:5173"
    # "*" is fine for local-only use
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "*"]

    # ── App ───────────────────────────────────────────────────────────────────
    APP_TITLE: str = "Personal Financial Manager"
    APP_VERSION: str = "2.0.0"
    DEFAULT_CURRENCY: str = "EGP"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
