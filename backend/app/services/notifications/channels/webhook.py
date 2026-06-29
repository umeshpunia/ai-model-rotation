import httpx
from typing import Any
from app.services.notifications.channels.base import BaseNotificationChannel
from app.core.config import get_settings
from app.core.logging import get_logger

_logger = get_logger("webhook_notification")

class WebhookNotificationChannel(BaseNotificationChannel):
    """Sends notification alerts to a configured generic HTTP webhook endpoint."""

    async def send(self, title: str, message: str, meta: dict[str, Any] | None = None) -> bool:
        settings = get_settings().notification
        if not settings.webhook_enabled or not settings.webhook_url:
            return False
            
        payload = {
            "title": title,
            "message": message,
            "meta": meta or {}
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(settings.webhook_url, json=payload)
                if res.status_code < 300:
                    _logger.info("notification.webhook.sent_successfully")
                    return True
                else:
                    _logger.error("notification.webhook.bad_status", status_code=res.status_code, body=res.text)
                    return False
        except Exception as e:
            _logger.error("notification.webhook.failed", error=str(e))
            return False
