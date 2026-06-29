"""Repository for :class:`Notification` entities."""
from __future__ import annotations
from datetime import datetime

from app.domain.entities.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Data access for notifications / alerts."""

    model = Notification

    def list_unread(self, *, limit: int = 50) -> list[Notification]:
        """Return unread notifications, newest first."""
        return self.list(
            filters={"is_read": False},
            order_by=Notification.created_at.desc(),
            limit=limit,
        )

    def list_pending_delivery(self, *, limit: int = 100) -> list[Notification]:
        """Return notifications that still need to be sent to a channel."""
        return self.list(
            filters={"is_sent": False},
            order_by=Notification.created_at.asc(),
            limit=limit,
        )

    def count_unread(self) -> int:
        """Count unread notifications."""
        return self.count(filters={"is_read": False})

    def mark_read(self, notification: Notification) -> Notification:
        """Mark a notification as read."""
        return self.update(notification, {"is_read": True})

    def delete_older_than(self, cutoff: datetime, *, only_read: bool = True) -> int:
        """Delete old notifications (read-only by default); return rows removed."""
        expressions = [Notification.created_at < cutoff]
        if only_read:
            expressions.append(Notification.is_read.is_(True))
        stale = self.list(expressions=expressions)
        for row in stale:
            self.session.delete(row)
        self.session.flush()
        return len(stale)
