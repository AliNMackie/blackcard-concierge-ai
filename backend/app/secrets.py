import os
from google.cloud import secretmanager
import logging
# from app.config import logger (Circular Import Fix)

logger = logging.getLogger("elite-concierge")

def get_secret(secret_id: str, version_id: str = "latest", project_id: str = None) -> str:
    """
    Fetches a secret from Google Secret Manager.
    """
    if not project_id:
        project_id = os.getenv("PROJECT_ID")
        
    if not project_id:
        logger.warning("PROJECT_ID not set. Cannot fetch secret.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to fetch secret {secret_id}: {e}")
        return None
