import asyncio
from datetime import datetime, timezone
from typing import Any, List
from sqlmodel import Session

from app.core.database import session_scope
from app.core.config import get_settings
from app.domain.entities.notification import Notification
from app.domain.enums import NotificationChannel, NotificationSeverity
from app.repositories.notification_repository import NotificationRepository

from app.services.notifications.channels.desktop import DesktopNotificationChannel
from app.services.notifications.channels.email import EmailNotificationChannel
from app.services.notifications.channels.slack import SlackNotificationChannel
from app.services.notifications.channels.discord import DiscordNotificationChannel
from app.services.notifications.channels.telegram import TelegramNotificationChannel
from app.services.notifications.channels.webhook import WebhookNotificationChannel

from app.core.logging import get_logger

_logger = get_logger("notification_dispatcher")

class NotificationDispatcher:
    """Orchestrates saving and background dispatching of alerts to all enabled channels."""

    def __init__(self) -> None:
        self.channels = {
            NotificationChannel.DESKTOP: DesktopNotificationChannel(),
            NotificationChannel.EMAIL: EmailNotificationChannel(),
            NotificationChannel.SLACK: SlackNotificationChannel(),
            NotificationChannel.DISCORD: DiscordNotificationChannel(),
            NotificationChannel.TELEGRAM: TelegramNotificationChannel(),
            NotificationChannel.WEBHOOK: WebhookNotificationChannel(),
        }

    def notify(
        self,
        session: Session,
        severity: NotificationSeverity,
        event_type: str,
        title: str,
        message: str,
        meta: dict[str, Any] | None = None
    ) -> Notification:
        """Create, persist, and trigger background dispatch of a notification alert."""
        _logger.info("notification.trigger", event_type=event_type, title=title)
        
        # Determine primary channel based on settings
        settings = get_settings().notification
        primary_channel = NotificationChannel.DESKTOP
        if settings.email_enabled:
            primary_channel = NotificationChannel.EMAIL
        elif settings.slack_enabled:
            primary_channel = NotificationChannel.SLACK
            
        notif = Notification(
            channel=primary_channel,
            severity=severity,
            event_type=event_type,
            title=title,
            message=message,
            is_read=False,
            is_sent=False,
            meta=meta or {}
        )
        
        repo = NotificationRepository(session)
        repo.add(notif)
        session.flush()  # Populates notif.id
        
        assert notif.id is not None
        # Spawn background task to send
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._dispatch_background(notif.id, title, message, meta))
        except RuntimeError:
            asyncio.run(self._dispatch_background(notif.id, title, message, meta))
        
        return notif

    async def _dispatch_background(self, notif_id: int, title: str, message: str, meta: dict[str, Any] | None) -> None:
        """Runs in the background: validates enabled channels, sends notifications, and updates DB status."""
        settings = get_settings().notification
        
        enabled_types = []
        if settings.desktop_enabled:
            enabled_types.append(NotificationChannel.DESKTOP)
        if settings.email_enabled:
            enabled_types.append(NotificationChannel.EMAIL)
        if settings.slack_enabled:
            enabled_types.append(NotificationChannel.SLACK)
        if settings.discord_enabled:
            enabled_types.append(NotificationChannel.DISCORD)
        if settings.telegram_enabled:
            enabled_types.append(NotificationChannel.TELEGRAM)
        if settings.webhook_enabled:
            enabled_types.append(NotificationChannel.WEBHOOK)
            
        if not enabled_types:
            _logger.info("notification.dispatch.none_enabled", notif_id=notif_id)
            return

        successes = []
        errors = []
        
        # Dispatch to all enabled channels
        for chan_type in enabled_types:
            channel = self.channels.get(chan_type)
            if channel:
                success = await channel.send(title, message, meta)
                if success:
                    successes.append(chan_type.value)
                else:
                    errors.append(f"{chan_type.value} failed")

        # Update notification model state
        with session_scope() as session:
            repo = NotificationRepository(session)
            notif = repo.get(notif_id)
            if notif:
                notif.is_sent = len(successes) > 0
                notif.sent_at = datetime.now(timezone.utc).replace(tzinfo=None)
                if errors:
                    notif.delivery_error = ", ".join(errors)
                else:
                    notif.delivery_error = ""
                session.add(notif)

# Global dispatcher instance
_global_dispatcher = NotificationDispatcher()

def get_notification_dispatcher() -> NotificationDispatcher:
    return _global_dispatcher
