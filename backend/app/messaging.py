"""
Messaging Module - Outbound WhatsApp via Twilio.
"""
from app.config import settings, logger


def send_whatsapp(to: str, body: str) -> str:
    """
    Send a WhatsApp message via Twilio.
    
    Args:
        to: Recipient phone number (with or without 'whatsapp:' prefix)
        body: Message content
        
    Returns:
        Message SID from Twilio, or "MOCK_SID" if not configured
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio not configured, skipping outbound WhatsApp")
        return "MOCK_SID_NOT_CONFIGURED"
    
    try:
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Ensure proper WhatsApp format
        from_number = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
        to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        
        logger.info(f"Sent WhatsApp to {to_number}, SID: {message.sid}")
        return message.sid
        
    except Exception as e:
        logger.error(f"Failed to send WhatsApp: {e}")
        raise


def send_sms(to: str, body: str) -> str:
    """
    Send an SMS via Twilio (fallback for non-WhatsApp users).
    """
    if not settings.TWILIO_ACCOUNT_SID:
        logger.warning("Twilio not configured, skipping SMS")
        return "MOCK_SID_NOT_CONFIGURED"
    
    try:
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_WHATSAPP_NUMBER,  # Use same number for SMS
            to=to
        )
        
        logger.info(f"Sent SMS to {to}, SID: {message.sid}")
        return message.sid
        
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        raise
