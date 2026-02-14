from firebase_admin import messaging
from app.config import logger

def send_fcm_notification(token: str, title: str, body: str, data: dict = None):
    """
    Sends a push notification to a specific device token.
    """
    if not token:
        logger.warning("FCM: No token provided, skipping notification.")
        return

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
        )
        response = messaging.send(message)
        logger.info(f"FCM: Successfully sent message: {response}")
        return response
    except Exception as e:
        logger.error(f"FCM: Error sending message: {e}")
        return None

def send_topic_notification(topic: str, title: str, body: str):
    """
    Sends a message to a topic (e.g., 'all_trainers').
    """
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic=topic,
        )
        response = messaging.send(message)
        logger.info(f"FCM: Sent to topic {topic}: {response}")
        return response
    except Exception as e:
        logger.error(f"FCM: Error sending to topic {topic}: {e}")
        return None

def subscribe_to_topic(token: str, topic: str):
    """
    Subscribes a device token to a topic.
    """
    try:
        response = messaging.subscribe_to_topic([token], topic)
        logger.info(f"FCM: Subscribed token to {topic}: {response.success_count} success")
        return response
    except Exception as e:
        logger.error(f"FCM: Error subscribing to topic {topic}: {e}")
        return None
