import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "Elite Concierge AI"
    VERSION: str = "0.1.0"
    ENV: str = os.getenv("ENV", "development")

    # Vertex AI / Gemini
    PROJECT_ID: str = os.getenv("PROJECT_ID", "blackcard-concierge-ai")
    GCP_REGION: str = "europe-west2"
    GEMINI_MODEL_ID: str = "gemini-2.5-flash"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_INSTANCE_CONNECTION_NAME: str = os.getenv("DB_INSTANCE_CONNECTION_NAME", "")
    DB_USER: str = os.getenv("DB_USER", "elite-concierge-user")
    DB_NAME: str = os.getenv("DB_NAME", "concierge_db")
    DB_SECRET_ID: str = os.getenv("DB_SECRET_ID", "elite-concierge-db-pass")

    # Auth
    ELITE_API_KEY: str = os.getenv("ELITE_API_KEY", "dev-secret-123")
    TERRA_API_SECRET: str = os.getenv("TERRA_API_SECRET", "terra-secret-placeholder")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

# Singleton
settings = Settings()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("elite-concierge")
