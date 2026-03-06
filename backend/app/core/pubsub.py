import json
import logging
from google.cloud import pubsub_v1
from app.config import settings

logger = logging.getLogger("elite-concierge")

class PubSubPublisher:
    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(settings.PROJECT_ID, "video-frames-input")

    def publish_video_job(self, video_uri: str, user_id: str, movement_type: str):
        """
        Publishes a message to the video-frames-input topic for video processing.
        """
        try:
            data = {
                "video_uri": video_uri,
                "user_id": user_id,
                "movement_type": movement_type,
                "job_type": "video"
            }
            message_bytes = json.dumps(data).encode("utf-8")
            
            future = self.publisher.publish(self.topic_path, message_bytes)
            message_id = future.result()
            
            logger.info(f"Published video message {message_id} to {self.topic_path}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish to Pub/Sub: {e}")
            raise

    def publish_vector_job(self, job_id: str, user_id: str, movement_type: str, vector: list):
        """
        Publishes a message for pre-extracted vector analysis.
        """
        try:
            data = {
                "job_id": job_id,
                "user_id": user_id,
                "movement_type": movement_type,
                "vector": vector,
                "job_type": "vector"
            }
            message_bytes = json.dumps(data).encode("utf-8")
            
            future = self.publisher.publish(self.topic_path, message_bytes)
            message_id = future.result()
            
            logger.info(f"Published vector message {message_id} to {self.topic_path}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish vector job to Pub/Sub: {e}")
            raise

publisher = PubSubPublisher()
