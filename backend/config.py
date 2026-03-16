"""
config.py — Application Configuration
========================================

Loads settings from environment variables using Pydantic Settings.
All configuration is centralized here for easy management.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ---- Server ----
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DEBUG: bool = False

    # ---- Database ----
    POSTGRES_USER: str = "sharks"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "sharksfromspace"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ---- Redis ----
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---- NASA Earthdata ----
    NASA_EARTHDATA_USERNAME: str = ""
    NASA_EARTHDATA_PASSWORD: str = ""
    NASA_EARTHDATA_BEARER_TOKEN: str = ""

    # ---- ML Model ----
    MODEL_PATH: str = "./models/shark_predictor.pkl"
    PREDICTION_THRESHOLD: float = 0.6

    # ---- Data Pipeline ----
    DATA_RAW_DIR: str = "./data/raw"
    DATA_PROCESSED_DIR: str = "./data/processed"
    FETCH_INTERVAL_HOURS: int = 6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton settings instance
settings = Settings()
