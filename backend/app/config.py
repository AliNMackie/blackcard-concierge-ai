import os
import logging
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "Elite Concierge AI"
    VERSION: str = "0.1.0"
    ENV: str = os.getenv("ENV", "development")

    # Vertex AI / Gemini
    PROJECT_ID: str = os.getenv("PROJECT_ID", "")
    GCP_REGION: str = "europe-west2"
    GEMINI_MODEL_ID: str = "gemini-2.5-flash"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DB_INSTANCE_CONNECTION_NAME: str = os.getenv("DB_INSTANCE_CONNECTION_NAME", "")
    DB_USER: str = os.getenv("DB_USER", "elite-concierge-user")
    DB_NAME: str = os.getenv("DB_NAME", "concierge_db")
    DB_PASS: str = os.getenv("DB_PASS", "") # Injected via Secret

    # Auth
    ELITE_API_KEY: str = os.getenv("ELITE_API_KEY", "dev-secret-123")
    TERRA_API_SECRET: str = os.getenv("TERRA_API_SECRET", "terra-secret-placeholder")
    
    # Firebase Auth
    FIREBASE_CREDENTIALS_JSON: str = os.getenv("FIREBASE_CREDENTIALS_JSON", "")
    
    # Twilio (WhatsApp)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DATABASE_URL and self.DB_PASS and self.DB_INSTANCE_CONNECTION_NAME:
            # Construct AsyncPG URL for Cloud SQL
            # postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/instance
            encoded_user = quote_plus(self.DB_USER)
            encoded_pass = quote_plus(self.DB_PASS)
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{encoded_user}:{encoded_pass}@/"
                f"{self.DB_NAME}?host=/cloudsql/{self.DB_INSTANCE_CONNECTION_NAME}"
            )

# Singleton
settings = Settings()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("elite-concierge")
