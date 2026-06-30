import logging
import hashlib
import time
import httpx
from datetime import datetime, timezone
from typing import Optional

from core.config import settings

logger = logging.getLogger("quantcai.meta_capi")

def hash_data(data: str) -> str:
    """Hash user data using SHA256 as required by Meta."""
    if not data:
        return ""
    return hashlib.sha256(data.strip().lower().encode("utf-8")).hexdigest()

async def send_purchase_event_to_meta(
    email: str,
    amount: float,
    currency: str,
    sale_id: str,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    Sends a Purchase event to the Meta Conversions API.
    Designed to run as a background task.
    """
    if not settings.META_ACCESS_TOKEN or not settings.META_PIXEL_ID:
        logger.warning(f"Meta CAPI not configured. Skipping event for sale {sale_id}")
        return

    url = f"https://graph.facebook.com/v19.0/{settings.META_PIXEL_ID}/events"
    
    # Meta requires an array of event objects
    event_time = int(time.time())
    
    user_data = {
        "em": hash_data(email)
    }
    
    if client_ip:
        user_data["client_ip_address"] = client_ip
    if user_agent:
        user_data["client_user_agent"] = user_agent

    payload = {
        "data": [
            {
                "event_name": "Purchase",
                "event_time": event_time,
                "action_source": "website",
                "event_source_url": settings.FRONTEND_URL,
                "user_data": user_data,
                "custom_data": {
                    "currency": currency,
                    "value": amount
                },
                # Use sale_id as the event_id for deduplication
                "event_id": f"purchase_{sale_id}"
            }
        ],
        "access_token": settings.META_ACCESS_TOKEN
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Successfully sent CAPI Purchase event for sale {sale_id}")
            else:
                logger.error(
                    f"Failed to send CAPI event for sale {sale_id}. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
    except Exception as e:
        logger.error(f"Exception while sending CAPI event for sale {sale_id}: {e}", exc_info=True)
