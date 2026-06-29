import smtplib
from email.mime.text import MIMEText
from typing import Any
import os

from app.services.notifications.channels.base import BaseNotificationChannel
from app.core.config import get_settings
from app.core.logging import get_logger

_logger = get_logger("email_notification")

class EmailNotificationChannel(BaseNotificationChannel):
    """Sends notification alerts via SMTP email."""

    async def send(self, title: str, message: str, meta: dict[str, Any] | None = None) -> bool:
        settings = get_settings().notification
        if not settings.email_enabled or not settings.email_smtp:
            _logger.info("notification.email.disabled_or_no_smtp")
            return False
            
        smtp_target = settings.email_smtp
        mail_from = settings.email_from
        mail_to = settings.email_to
        
        # Optional credentials from env
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pass = os.getenv("SMTP_PASSWORD", "")
        
        try:
            # Parse host and port
            if ":" in smtp_target:
                host, port_str = smtp_target.split(":", 1)
                port = int(port_str)
            else:
                host = smtp_target
                port = 587
                
            # Create message
            msg = MIMEText(message)
            msg["Subject"] = title
            msg["From"] = mail_from
            msg["To"] = mail_to
            
            # Send in thread to avoid blocking event loop
            def _send_sync():
                with smtplib.SMTP(host, port, timeout=10) as server:
                    if port == 587:
                        server.starttls()
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.sendmail(mail_from, [mail_to], msg.as_string())
                    
            # Run in worker thread
            import anyio
            await anyio.to_thread.run_sync(_send_sync)
            _logger.info("notification.email.sent_successfully", recipient=mail_to)
            return True
            
        except Exception as e:
            _logger.error("notification.email.failed", recipient=mail_to, error=str(e))
            return False
