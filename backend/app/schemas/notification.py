"""Notification request/response DTOs."""
from datetime import datetime
from typing import Any

from pydantic import Field

from app.domain.enums import NotificationChannel, NotificationSeverity
from app.schemas.common import ORMSchema, SchemaBase


class NotificationCreate(SchemaBase):
    """Payload for raising a notification."""

    channel: NotificationChannel = NotificationChannel.DESKTOP
    severity: NotificationSeverity = NotificationSeverity.INFO
    event_type: str = Field(default="", max_length=80)
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(default="", max_length=2000)
    meta: dict[str, Any] = Field(default_factory=dict)


class NotificationRead(ORMSchema):
    """A notification as returned by the API."""

    id: int
    created_at: datetime
    channel: NotificationChannel
    severity: NotificationSeverity
    event_type: str
    title: str
    message: str
    is_read: bool
    is_sent: bool
    sent_at: datetime | None
    delivery_error: str
    meta: dict[str, Any]
