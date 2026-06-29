import httpx
from typing import Any
from app.services.notifications.channels.base import BaseNotificationChannel
from app.core.config import get_settings
from app.core.logging import get_logger

_logger = get_logger("slack_notification")

class SlackNotificationChannel(BaseNotificationChannel):
    """Sends notification alerts to a Slack Webhook."""

    async def send(self, title: str, message: str, meta: dict[str, Any] | None = None) -> bool:
        settings = get_settings().notification
        if not settings.slack_enabled or not settings.slack_webhook:
            return False
            
        payload = {
            "text": f"*AI Gateway Pro Alert: {title}*\n\n{message}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(settings.slack_webhook, json=payload)
                if res.status_code < 300:
                    _logger.info("notification.slack.sent_successfully")
                    return True
                else:
                    _logger.error("notification.slack.bad_status", status_code=res.status_code, body=res.text)
                    return False
        except Exception as e:
            _logger.error("notification.slack.failed", error=str(e))
            return False
