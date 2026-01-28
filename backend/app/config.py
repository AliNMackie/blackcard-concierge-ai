import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "elite-concierge-backend"
    VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"
    
    # GCP Config
    PROJECT_ID: str = "mock-project-id"
    GCP_REGION: str = "europe-west2"
    
    # Vertex AI Config
    GEMINI_MODEL_ID: str = "gemini-3-flash-preview"

    # Database Config
    DB_INSTANCE_CONNECTION_NAME: Optional[str] = None # e.g. project:region:instance
    DB_SECRET_ID: Optional[str] = None # e.g. projects/123/secrets/db-pass/versions/1
    DB_USER: str = "elite-concierge-user"
    DB_NAME: str = "concierge_db"
    
    # Local Dev Override (if not using Cloud SQL Connector)
    DATABASE_URL: Optional[str] = None 

    def is_production(self) -> bool:
        return self.PROJECT_ID != "mock-project-id"

settings = Settings()

# Configure Logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(settings.APP_NAME)
