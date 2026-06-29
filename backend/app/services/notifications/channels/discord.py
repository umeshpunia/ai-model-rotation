import httpx
from typing import Any
from app.services.notifications.channels.base import BaseNotificationChannel
from app.core.config import get_settings
from app.core.logging import get_logger

_logger = get_logger("discord_notification")

class DiscordNotificationChannel(BaseNotificationChannel):
    """Sends notification alerts to a Discord Webhook."""

    async def send(self, title: str, message: str, meta: dict[str, Any] | None = None) -> bool:
        settings = get_settings().notification
        if not settings.discord_enabled or not settings.discord_webhook:
            return False
            
        # Color based on alert severity (red for warning/error-like title keywords, blue otherwise)
        is_critical = any(kwd in title.lower() for kwd in ["fail", "error", "unavailable", "offline", "invalid"])
        color = 15548997 if is_critical else 3447003 # red or blue
        
        payload = {
            "embeds": [{
                "title": f"AI Gateway Pro: {title}",
                "description": message,
                "color": color,
                "footer": {"text": "AI Gateway Pro Monitor"}
            }]
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(settings.discord_webhook, json=payload)
                if res.status_code < 300:
                    _logger.info("notification.discord.sent_successfully")
                    return True
                else:
                    _logger.error("notification.discord.bad_status", status_code=res.status_code, body=res.text)
                    return False
        except Exception as e:
            _logger.error("notification.discord.failed", error=str(e))
            return False
