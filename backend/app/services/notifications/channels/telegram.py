import httpx
from typing import Any
from app.services.notifications.channels.base import BaseNotificationChannel
from app.core.config import get_settings
from app.core.logging import get_logger

_logger = get_logger("telegram_notification")

class TelegramNotificationChannel(BaseNotificationChannel):
    """Sends notification alerts via Telegram Bot API."""

    async def send(self, title: str, message: str, meta: dict[str, Any] | None = None) -> bool:
        settings = get_settings().notification
        if not settings.telegram_enabled or not settings.telegram_bot_token or not settings.telegram_chat_id:
            return False
            
        token = settings.telegram_bot_token
        chat_id = settings.telegram_chat_id
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Simple Markdown parsing
        text = f"*AI Gateway Pro Alert: {title}*\n\n{message}"
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(url, json=payload)
                if res.status_code < 300:
                    _logger.info("notification.telegram.sent_successfully")
                    return True
                else:
                    _logger.error("notification.telegram.bad_status", status_code=res.status_code, body=res.text)
                    return False
        except Exception as e:
            _logger.error("notification.telegram.failed", error=str(e))
            return False
