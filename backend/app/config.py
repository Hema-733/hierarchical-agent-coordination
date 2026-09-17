"""
config.py — Application settings loaded from environment variables.

Uses pydantic-settings to automatically read from the .env file.
Access settings anywhere by importing the `settings` singleton at the bottom.

Example:
    from app.config import settings
    print(settings.MONGODB_URI)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- MongoDB ---
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "onboarding_db"

    # --- Google Gemini ---
    GEMINI_API_KEY: str = ""

    # --- FastAPI App ---
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8001
    DEBUG: bool = True

    # --- CORS ---
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Tell pydantic-settings to read from backend/.env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# A single shared instance used across the entire app
settings = Settings()
